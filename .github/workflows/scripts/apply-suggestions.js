const { Octokit } = require("@octokit/rest");
const fs = require("fs");
const path = require("path");

const octokit = new Octokit({ auth: process.env.GH_TOKEN });
const [owner, repo] = process.env.REPO.split("/");
const pull_number = parseInt(process.env.PR_NUMBER);

async function run() {
  // Fetch all review comments on the PR
  const { data: comments } = await octokit.pulls.listReviewComments({
    owner,
    repo,
    pull_number,
    per_page: 100,
  });

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

    // Replace the lines the comment targets (1-indexed)
    const newLines = [
      ...fileLines.slice(0, startLine - 1),
      ...suggestedContent.split("\n").slice(0, -1), // trim trailing newline
      ...fileLines.slice(endLine),
    ];

    fs.writeFileSync(filePath, newLines.join("\n"), "utf8");
    console.log(`Applied suggestion on ${filePath} lines ${startLine}-${endLine}`);
    applied++;

    // Resolve the comment thread after applying
    await octokit.pulls.deleteReviewComment({
      owner,
      repo,
      comment_id: comment.id,
    });
  }

  console.log(`Total suggestions applied: ${applied}`);
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});