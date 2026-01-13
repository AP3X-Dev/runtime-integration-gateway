# PRP: RIG (Runtime Integration Gateway)

## Role
You are a senior engineer implementing RIG, a system that turns SDKs into safe, versioned agent tools and can export them as MCP instantly.

## Goal
Deliver a plug and play integration layer that lets builders:
- Install an integration pack from pip or npm
- Get a stable, versioned tool interface in a registry
- Execute tool calls through a hardened runtime
- Serve tools over a native HTTP protocol
- Optionally export the same registry as an MCP server

RIG must support instant updates when packs update, with strong safety controls.

## Definitions
- RIG Standard: spec for pack format, schema, policies, runtime behaviors
- RIG Runtime: execution engine (validation, secrets, policy, retries, logs)
- RIG Registry: discovery and versioned catalog of tools
- RIG Packs: installable integrations (pip and npm)
- RIG Bridge for MCP: export any RIG registry as an MCP server
- RIG Hub: optional hosted control plane (multi tenant, audit, approvals)

Acronyms:
- RSP: RIG Standard Pack format
- RTP: RIG Tool Protocol
- RGP: RIG Gateway Protocol

## Non goals
- Reimplement every upstream SDK.
- Ship a full hosted product in v0.
- Guarantee compatibility for breaking changes in upstream SDKs.

## User stories
1) As a builder, I can install a pack and immediately list tools.
2) As a builder, I can call tools via HTTP without writing wrappers.
3) As a builder, I can require approval for risky tools.
4) As a platform operator, I can audit tool usage.
5) As an agent platform, I can export the same tools as MCP.
6) As a builder, I can update packs and the registry updates instantly.

## Architecture
### Components
1) rig-core
- RTP types: ToolDef, ToolResult, ToolError
- Registry: tool catalog, interface hash
- Runtime: schema validation, secrets resolution, policy enforcement, approvals, retries
- Audit: append only events

2) rig-protocol-rgp
- FastAPI app exposing:
  - GET /v1/tools
  - GET /v1/tools/{name}
  - POST /v1/tools/{name}:call
  - POST /v1/approvals/{token}:approve

3) rig-cli
- rig init
- rig list
- rig serve
- rig call
- rig approve
- rig add
- rig update

4) rig-pack-*
- Packs define tools and implementations and register via Python entry points

5) Node Runner (planned)
- Loads @rig/pack-* npm packages
- Exposes the same RTP and invocation contract to Python runtime

6) MCP Bridge (planned)
- Implements MCP tool listing and invocation mapped to RIG Registry and Runtime

7) Updater (planned)
- Watches pack sources, canaries, promotes snapshots, rollbacks

### Pack contract (Python)
A pack exposes:
- rig_pack_metadata() -> {name, version}
- rig_tools() -> list[ToolDef]
- rig_impls() -> dict[tool_name, RegisteredTool]

### Registry snapshot
- interface_hash: sha256 over sorted (tool name, input schema, output schema, error schema)
- pack_set_version: operator defined tag (dev, prod, etc)

### Runtime pipeline
For each call:
1) Resolve tool
2) Policy allow check
3) Validate input via JSON Schema
4) Approval gate by risk class
5) Resolve secrets via auth_slots
6) Invoke tool impl
7) Validate output via JSON Schema
8) Retry on exceptions up to policy.retries
9) Audit event

## Safety and policy
- Default: approvals for infra, money, destructive
- Allow list support per environment
- Future:
  - arg constraints per tool
  - rate limits
  - budgets
  - secret scoping per tenant

## Auto update and instant update
### v0
- rig update upgrades configured packs via pip and immediately affects subsequent runs

### v1
- Watcher loop mode for rig serve that polls pack sources and hot reloads registry
- Canary rollout: load new pack set in shadow, compare interface hash, run smoke calls, then promote
- Rollback to previous pack set on error spikes

### v2
- RIG Hub control plane manages updates, approvals, audit, and multi tenant isolation

## Acceptance criteria
- Install rig-pack-echo and see tool echo in rig list
- Run rig serve and call echo through RGP
- Approval tokens returned for tools marked infra, money, destructive
- Audit DB records tool call events
- rig update upgrades packs and reports version deltas

## Task list for implementation
- Implement rig-core: RTP, registry, runtime, secrets, audit
- Implement rig-protocol-rgp: FastAPI
- Implement rig-cli
- Implement demo pack
- Add unit tests for contract

## Next implementation tasks
- Node Runner MVP: npm pack loader and invocation bridge
- MCP Bridge MVP: minimal MCP server wired to registry and runtime
- Updater MVP: watcher loop, snapshot promotion, rollback
