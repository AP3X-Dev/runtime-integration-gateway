const { Octokit } = require('@octokit/rest');

function rigPack() {
  return { name: "@rig/pack-github", version: "0.1.0" };
}

function rigTools() {
  return [
    {
      name: "github.issues.create",
      description: "Create a GitHub issue",
      input_schema: {
        type: "object",
        properties: {
          repo: { type: "string", description: "Repository (owner/repo)" },
          title: { type: "string", description: "Issue title" },
          body: { type: "string", description: "Issue body" },
          labels: { type: "array", items: { type: "string" } }
        },
        required: ["repo", "title"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          number: { type: "integer" },
          url: { type: "string" }
        },
        required: ["number", "url"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["GITHUB_TOKEN"],
      risk_class: "write",
      tags: ["github", "development"]
    },
    {
      name: "github.issues.comment",
      description: "Comment on a GitHub issue",
      input_schema: {
        type: "object",
        properties: {
          repo: { type: "string" },
          issue_number: { type: "integer" },
          body: { type: "string" }
        },
        required: ["repo", "issue_number", "body"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          id: { type: "integer" },
          url: { type: "string" }
        },
        required: ["id", "url"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["GITHUB_TOKEN"],
      risk_class: "write",
      tags: ["github", "development"]
    },
    {
      name: "github.pulls.create",
      description: "Create a GitHub pull request",
      input_schema: {
        type: "object",
        properties: {
          repo: { type: "string" },
          title: { type: "string" },
          head: { type: "string", description: "Branch with changes" },
          base: { type: "string", description: "Target branch" },
          body: { type: "string" }
        },
        required: ["repo", "title", "head"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          number: { type: "integer" },
          url: { type: "string" }
        },
        required: ["number", "url"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["GITHUB_TOKEN"],
      risk_class: "write",
      tags: ["github", "development"]
    },
    {
      name: "github.pulls.list",
      description: "List GitHub pull requests",
      input_schema: {
        type: "object",
        properties: {
          repo: { type: "string" },
          state: { type: "string", enum: ["open", "closed", "all"] },
          limit: { type: "integer", default: 20 }
        },
        required: ["repo"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          pull_requests: { type: "array" }
        },
        required: ["pull_requests"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["GITHUB_TOKEN"],
      risk_class: "read",
      tags: ["github", "development"]
    }
  ];
}

async function rigInvoke(toolName, args, context) {
  const token = context.auth?.GITHUB_TOKEN;
  if (!token) {
    throw new Error("GITHUB_TOKEN not provided in context");
  }

  const octokit = new Octokit({ auth: token });
  const [owner, repo] = args.repo.split('/');

  switch (toolName) {
    case "github.issues.create":
      const issue = await octokit.issues.create({
        owner,
        repo,
        title: args.title,
        body: args.body,
        labels: args.labels
      });
      return { number: issue.data.number, url: issue.data.html_url };

    case "github.issues.comment":
      const comment = await octokit.issues.createComment({
        owner,
        repo,
        issue_number: args.issue_number,
        body: args.body
      });
      return { id: comment.data.id, url: comment.data.html_url };

    case "github.pulls.create":
      const pr = await octokit.pulls.create({
        owner,
        repo,
        title: args.title,
        head: args.head,
        base: args.base || "main",
        body: args.body
      });
      return { number: pr.data.number, url: pr.data.html_url };

    case "github.pulls.list":
      const prs = await octokit.pulls.list({
        owner,
        repo,
        state: args.state || "open",
        per_page: args.limit || 20
      });
      return { pull_requests: prs.data };

    default:
      throw new Error(`tool not found: ${toolName}`);
  }
}

module.exports = { rigPack, rigTools, rigInvoke };

