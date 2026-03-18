import { Octokit } from "@octokit/rest";
import fs from "fs";

const octokit = new Octokit({ auth: process.env.GH_TOKEN });
const [owner, repo] = process.env.REPO.split("/");
const pull_number = parseInt(process.env.PR_NUMBER);

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

  let applied = 0;

  for (const comment of comments) {
    const suggestionMatch = comment.body.match(
      /```suggestion\r?\n([\s\S]*?)```/
    );

    if (!suggestionMatch) continue;

    const suggestedContent = suggestionMatch[1];
    const filePath = comment.path;
    const startLine = comment.start_line ?? comment.line;
    const endLine = comment.line;

    if (!fs.existsSync(filePath)) continue;

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
