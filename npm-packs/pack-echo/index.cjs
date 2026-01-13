function rigPack() {
  return { name: "@rig/pack-echo", version: "0.1.0" };
}

function rigTools() {
  return [
    {
      name: "echo_node",
      description: "Echo back a message from the node runner",
      input_schema: {
        type: "object",
        properties: { message: { type: "string" } },
        required: ["message"],
        additionalProperties: false
      },
      output_schema: {
        type: "object",
        properties: {
          message: { type: "string" },
          tenant_id: { type: ["string","null"] },
          runner: { type: "string" }
        },
        required: ["message","tenant_id","runner"],
        additionalProperties: false
      },
      error_schema: { type: "object" },
      auth_slots: [],
      risk_class: "read",
      tags: ["demo"]
    }
  ];
}

async function rigInvoke(toolName, args, context) {
  if (toolName === "echo_node") {
    return {
      message: String(args.message || ""),
      tenant_id: context.tenant_id || null,
      runner: "node"
    };
  }
  throw new Error("tool not found");
}

module.exports = { rigPack, rigTools, rigInvoke };
