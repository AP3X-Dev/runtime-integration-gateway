import express from "express";
import bodyParser from "body-parser";

const HOST = process.env.RIG_NODE_HOST || "127.0.0.1";
const PORT = parseInt(process.env.RIG_NODE_PORT || "8790", 10);

function safeJsonParse(s) {
  try { return JSON.parse(s); } catch { return null; }
}

function loadPacks() {
  const raw = process.env.RIG_NODE_PACKS || "";
  const names = raw.split(",").map(s => s.trim()).filter(Boolean);
  const packs = [];
  for (const name of names) {
    // eslint-disable-next-line no-undef
    const mod = require(name);
    const packMeta = mod.rigPack ? mod.rigPack() : { name, version: "0.0.0" };
    const tools = mod.rigTools ? mod.rigTools() : [];
    const invoke = mod.rigInvoke;
    if (!invoke) {
      throw new Error(`pack ${name} does not export rigInvoke`);
    }
    packs.push({ pkg: name, meta: packMeta, tools, invoke });
  }
  return packs;
}

// Node ESM + require interop
import { createRequire } from "module";
const require = createRequire(import.meta.url);

const packs = loadPacks();
const toolIndex = new Map();
for (const p of packs) {
  for (const t of p.tools) {
    if (toolIndex.has(t.name)) {
      throw new Error(`duplicate tool name: ${t.name}`);
    }
    toolIndex.set(t.name, { pack: p, tool: t });
  }
}

const app = express();
app.use(bodyParser.json({ limit: "2mb" }));

app.get("/v1/health", (req, res) => {
  res.json({ status: "ok" });
});

app.get("/v1/tools", (req, res) => {
  const out = [];
  for (const [name, item] of toolIndex.entries()) {
    out.push({
      name: item.tool.name,
      description: item.tool.description,
      input_schema: item.tool.input_schema,
      output_schema: item.tool.output_schema,
      error_schema: item.tool.error_schema || { type: "object" },
      auth_slots: item.tool.auth_slots || [],
      risk_class: item.tool.risk_class || "read",
      tags: item.tool.tags || [],
      pack: item.pack.meta.name || item.pack.pkg,
      pack_version: item.pack.meta.version || "0.0.0"
    });
  }
  res.json(out);
});

app.post("/v1/tools/:name:call", async (req, res) => {
  const name = req.params.name;
  const item = toolIndex.get(name);
  if (!item) {
    return res.status(404).json({ ok: false, error: { type: "not_found", message: "tool not found", retryable: false } });
  }
  const args = (req.body && req.body.args) || {};
  const context = (req.body && req.body.context) || {};
  try {
    const output = await item.pack.invoke(name, args, context);
    return res.json({ ok: true, output });
  } catch (e) {
    const msg = (e && e.message) ? e.message : String(e);
    return res.json({
      ok: false,
      error: { type: "upstream_error", message: msg, retryable: false }
    });
  }
});

app.listen(PORT, HOST, () => {
  console.log(`rig-node-runner listening on http://${HOST}:${PORT}`);
  console.log(`loaded packs: ${packs.map(p => p.pkg).join(", ") || "none"}`);
});
