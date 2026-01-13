const { Client } = require('@notionhq/client');

function rigPack() {
  return { name: "@rig/pack-notion", version: "0.1.0" };
}

function rigTools() {
  return [
    {
      name: "notion.pages.create",
      description: "Create a Notion page",
      input_schema: {
        type: "object",
        properties: {
          parent: { type: "object", description: "Parent page or database" },
          properties: { type: "object" },
          children: { type: "array", description: "Block children" }
        },
        required: ["parent"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          id: { type: "string" }
        },
        required: ["id"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["NOTION_TOKEN"],
      risk_class: "write",
      tags: ["notion", "productivity"]
    },
    {
      name: "notion.pages.update",
      description: "Update a Notion page",
      input_schema: {
        type: "object",
        properties: {
          page_id: { type: "string" },
          properties: { type: "object" }
        },
        required: ["page_id"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          id: { type: "string" }
        },
        required: ["id"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["NOTION_TOKEN"],
      risk_class: "write",
      tags: ["notion", "productivity"]
    },
    {
      name: "notion.databases.query",
      description: "Query a Notion database",
      input_schema: {
        type: "object",
        properties: {
          database_id: { type: "string" },
          filter: { type: "object" },
          sorts: { type: "array" }
        },
        required: ["database_id"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          results: { type: "array" }
        },
        required: ["results"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["NOTION_TOKEN"],
      risk_class: "read",
      tags: ["notion", "productivity"]
    },
    {
      name: "notion.search",
      description: "Search Notion",
      input_schema: {
        type: "object",
        properties: {
          query: { type: "string" },
          filter: { type: "object" }
        },
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          results: { type: "array" }
        },
        required: ["results"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: ["NOTION_TOKEN"],
      risk_class: "read",
      tags: ["notion", "productivity"]
    }
  ];
}

async function rigInvoke(toolName, args, context) {
  const token = context.auth?.NOTION_TOKEN;
  if (!token) {
    throw new Error("NOTION_TOKEN not provided in context");
  }

  const notion = new Client({ auth: token });

  switch (toolName) {
    case "notion.pages.create":
      const page = await notion.pages.create({
        parent: args.parent,
        properties: args.properties || {},
        children: args.children || []
      });
      return { id: page.id };

    case "notion.pages.update":
      const updated = await notion.pages.update({
        page_id: args.page_id,
        properties: args.properties || {}
      });
      return { id: updated.id };

    case "notion.databases.query":
      const queryResult = await notion.databases.query({
        database_id: args.database_id,
        filter: args.filter,
        sorts: args.sorts
      });
      return { results: queryResult.results };

    case "notion.search":
      const searchResult = await notion.search({
        query: args.query,
        filter: args.filter
      });
      return { results: searchResult.results };

    default:
      throw new Error(`tool not found: ${toolName}`);
  }
}

module.exports = { rigPack, rigTools, rigInvoke };

