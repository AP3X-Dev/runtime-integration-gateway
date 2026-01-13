const { WebClient } = require('@slack/web-api');

function rigPack() {
  return { name: "@rig/pack-slack", version: "0.1.0" };
}

function rigTools() {
  return [
    {
      name: "slack.messages.post",
      description: "Post a message to a Slack channel",
      input_schema: {
        type: "object",
        properties: {
          channel: { type: "string", description: "Channel ID or name" },
          text: { type: "string", description: "Message text" },
          blocks: { type: "array", description: "Block Kit blocks" },
          thread_ts: { type: "string", description: "Thread timestamp" }
        },
        required: ["channel", "text"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          ok: { type: "boolean" },
          ts: { type: "string" }
        },
        required: ["ok"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["SLACK_BOT_TOKEN"],
      risk_class: "write",
      tags: ["messaging", "slack"]
    },
    {
      name: "slack.messages.update",
      description: "Update a Slack message",
      input_schema: {
        type: "object",
        properties: {
          channel: { type: "string" },
          ts: { type: "string", description: "Message timestamp" },
          text: { type: "string" }
        },
        required: ["channel", "ts", "text"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          ok: { type: "boolean" },
          ts: { type: "string" }
        },
        required: ["ok"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["SLACK_BOT_TOKEN"],
      risk_class: "write",
      tags: ["messaging", "slack"]
    },
    {
      name: "slack.channels.list",
      description: "List Slack channels",
      input_schema: {
        type: "object",
        properties: {
          types: { type: "string", default: "public_channel" },
          limit: { type: "integer", default: 100 }
        },
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          ok: { type: "boolean" },
          channels: { type: "array" }
        },
        required: ["ok", "channels"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["SLACK_BOT_TOKEN"],
      risk_class: "read",
      tags: ["messaging", "slack"]
    },
    {
      name: "slack.users.lookupByEmail",
      description: "Look up a Slack user by email",
      input_schema: {
        type: "object",
        properties: {
          email: { type: "string", description: "User email" }
        },
        required: ["email"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          ok: { type: "boolean" },
          user: { type: "object" }
        },
        required: ["ok"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["SLACK_BOT_TOKEN"],
      risk_class: "read",
      tags: ["messaging", "slack"]
    }
  ];
}

async function rigInvoke(toolName, args, context) {
  const token = context.auth?.SLACK_BOT_TOKEN;
  if (!token) {
    throw new Error("SLACK_BOT_TOKEN not provided in context");
  }

  const client = new WebClient(token);

  switch (toolName) {
    case "slack.messages.post":
      const postResult = await client.chat.postMessage({
        channel: args.channel,
        text: args.text,
        blocks: args.blocks,
        thread_ts: args.thread_ts
      });
      return { ok: postResult.ok, ts: postResult.ts };

    case "slack.messages.update":
      const updateResult = await client.chat.update({
        channel: args.channel,
        ts: args.ts,
        text: args.text
      });
      return { ok: updateResult.ok, ts: updateResult.ts };

    case "slack.channels.list":
      const listResult = await client.conversations.list({
        types: args.types || "public_channel",
        limit: args.limit || 100
      });
      return { ok: listResult.ok, channels: listResult.channels || [] };

    case "slack.users.lookupByEmail":
      const userResult = await client.users.lookupByEmail({
        email: args.email
      });
      return { ok: userResult.ok, user: userResult.user };

    default:
      throw new Error(`tool not found: ${toolName}`);
  }
}

module.exports = { rigPack, rigTools, rigInvoke };

