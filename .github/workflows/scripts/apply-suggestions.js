import { Octokit } from "@octokit/rest";
import fs from "fs";

const GH_TOKEN = process.env.GH_TOKEN;
const REPO = process.env.REPO;
const PR_NUMBER = process.env.PR_NUMBER;

if (!GH_TOKEN || !REPO || !PR_NUMBER) {
  console.error(
    "Missing required environment variables: GH_TOKEN, REPO, PR_NUMBER"
  );
  process.exit(1);
}

const repo_parts = REPO.split("/");
if (repo_parts.length !== 2 || !repo_parts[0] || !repo_parts[1]) {
  console.error(`REPO must be in "owner/repo" format, got: ${REPO}`);
  process.exit(1);
}

const pull_number = parseInt(PR_NUMBER, 10);
if (isNaN(pull_number)) {
  console.error(`PR_NUMBER must be a valid integer, got: ${PR_NUMBER}`);
  process.exit(1);
}

const octokit = new Octokit({ auth: GH_TOKEN });
const [owner, repo] = repo_parts;

async function run() {
  // Fetch all review comments on the PR using pagination
  const comments = await octokit.paginate(
    octokit.pulls.listReviewComments,
    {
      owner,
      repo,
      pull_number,
      per_page: 100,
    }
  );

  // Build a set of comment IDs that already have an "applied" reply so we
  // don't re-apply the same suggestion on subsequent runs (idempotency).
  const alreadyApplied = new Set(
    comments
      .filter(
        (c) =>
          c.in_reply_to_id &&
          c.body.includes("✅ Suggestion applied automatically.")
      )
      .map((c) => c.in_reply_to_id)
  );

  let applied = 0;

  for (const comment of comments) {
    const suggestionMatch = comment.body.match(
      /```suggestion\r?\n([\s\S]*?)```/
    );

    if (!suggestionMatch) continue;

    // Skip if this suggestion was already applied in a previous run.
    if (alreadyApplied.has(comment.id)) {
      console.log(
        `Skipping already-applied suggestion on ${comment.path} (comment ${comment.id})`
      );
      continue;
    }

    const suggestedContent = suggestionMatch[1];
    const filePath = comment.path;
    const startLine = comment.start_line ?? comment.line;
    const endLine = comment.line;

    if (!fs.existsSync(filePath)) {
      console.warn(`Warning: file not found, skipping suggestion for path: ${filePath}`);
      continue;
    }

    const fileLines = fs.readFileSync(filePath, "utf8").split("\n");

    // Remove a single trailing newline if present (GitHub suggestions always
    // end with one), but preserve any intentional blank lines within the block.
    const trimmedContent = suggestedContent.endsWith("\n")
      ? suggestedContent.slice(0, -1)
      : suggestedContent;

    // Replace the lines the comment targets (1-indexed)
    const newLines = [
      ...fileLines.slice(0, startLine - 1),
      ...trimmedContent.split("\n"),
      ...fileLines.slice(endLine),
    ];

    fs.writeFileSync(filePath, newLines.join("\n"), "utf8");
    console.log(`Applied suggestion on ${filePath} lines ${startLine}-${endLine}`);
    applied++;

    // Post a reply to the review comment instead of deleting it,
    // to preserve review history and auditability.
    await octokit.pulls.createReplyForReviewComment({
      owner,
      repo,
      pull_number,
      comment_id: comment.id,
      body: "✅ Suggestion applied automatically.",
    });
  }

  console.log(`Total suggestions applied: ${applied}`);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
