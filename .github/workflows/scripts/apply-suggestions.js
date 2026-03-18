import { Octokit } from "@octokit/rest";
import fs from "fs";

const SUGGESTION_RE = /```suggestion\r?\n([\s\S]*?)```/;

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

  // Group actionable suggestions by file path so we can apply them in
  // descending line order per file. This prevents earlier edits from
  // invalidating the line numbers of later edits in the same file.
  const commentsByFile = new Map();

  for (const comment of comments) {
    const suggestionMatch = comment.body.match(SUGGESTION_RE);

    if (!suggestionMatch) continue;

    // Skip if this suggestion was already applied in a previous run.
    if (alreadyApplied.has(comment.id)) {
      console.log(
        `Skipping already-applied suggestion on ${comment.path} (comment ${comment.id})`
      );
      continue;
    }

    if (!commentsByFile.has(comment.path)) {
      commentsByFile.set(comment.path, []);
    }
    // Store the matched content alongside the comment to avoid re-matching later.
    commentsByFile.get(comment.path).push({
      comment,
      suggestedContent: suggestionMatch[1],
    });
  }

  for (const [filePath, fileEntries] of commentsByFile) {
    if (!fs.existsSync(filePath)) {
      console.warn(
        `Warning: file not found, skipping suggestions for path: ${filePath}`
      );
      continue;
    }

    // Sort descending by start line so bottom edits are applied first;
    // this keeps earlier line numbers valid as we work upward.
    fileEntries.sort((a, b) => {
      const aLine = a.comment.start_line ?? a.comment.line;
      const bLine = b.comment.start_line ?? b.comment.line;
      return bLine - aLine;
    });

    let fileLines = fs.readFileSync(filePath, "utf8").split("\n");

    for (const { comment, suggestedContent } of fileEntries) {
      const startLine = comment.start_line ?? comment.line;
      const endLine = comment.line;

      // Remove a single trailing newline if present (GitHub suggestions always
      // end with one), but preserve any intentional blank lines within the block.
      const trimmedContent = suggestedContent.endsWith("\n")
        ? suggestedContent.slice(0, -1)
        : suggestedContent;

      // Replace the lines the comment targets (1-indexed)
      fileLines = [
        ...fileLines.slice(0, startLine - 1),
        ...trimmedContent.split("\n"),
        ...fileLines.slice(endLine),
      ];

      console.log(
        `Applied suggestion on ${filePath} lines ${startLine}-${endLine}`
      );
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

    fs.writeFileSync(filePath, fileLines.join("\n"), "utf8");
  }

  console.log(`Total suggestions applied: ${applied}`);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
