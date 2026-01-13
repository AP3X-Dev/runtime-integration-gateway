RIG continued development from current repo baseline
Canonical naming

RIG: Runtime Integration Gateway

RIG Standard: spec for packs, schemas, policies, runtime behaviors

RIG Runtime: execution engine (validation, secrets, policy, retries, logs)

RIG Registry: discovery and versioned catalog of tools

RIG Packs: installable integrations (pip and npm)

RIG Bridge for MCP: export any RIG Registry as an MCP server

RIG Hub: optional hosted control plane (multi tenant, audit, approvals)

Spec acronyms

RSP: RIG Standard Pack (pack format)

RTP: RIG Tool Protocol (tool schema and call contract)

RGP: RIG Gateway Protocol (native HTTP discovery and invocation)

CLI and package naming

CLI: rig

pip packs: rig-pack-stripe, rig-pack-digitalocean

npm packs: @rig/pack-stripe, @rig/pack-digitalocean

One line positioning

RIG turns SDKs into safe, versioned agent tools and can export them as MCP instantly.

1) Objective

Evolve the current RIG repo into a real MCP competitor by completing the missing pillars:

First class npm support (not just “a runner exists”, but real pack install, discovery, versioning, tests, and policy)

RIG Bridge for MCP that exports the live RIG Registry and routes calls through RIG Runtime

Auto update plus instant update, including tool shape diff gates, canary promotion, and rollback

A stable RIG Standard (RSP, RTP, RGP) that third parties can implement without reading source code

2) Current baseline (what exists today)
2.1 Implemented

RTP core models, error taxonomy, ToolDef, ToolResult

RIG Registry with interface hash

RIG Runtime pipeline: JSON Schema validation, policy allow/deny, approval tokens, retries, env secrets, SQLite audit log

RGP server: list tools, call tool, approve token

CLI: init, list, serve, call, approve, add, update (pip oriented)

pip pack discovery via Python entry points with a demo pack

Node runner: HTTP service that can list tools and invoke tools from npm packs

Python side can ingest node tools and proxy calls to node runner

2.2 Not implemented or incomplete

RIG Bridge for MCP is scaffold only

Auto update and instant update are not real yet (no snapshot swap, canary, rollback)

npm pack lifecycle is not complete:

no official RSP spec for node packs

no robust rig add flow for npm packs

no pack contract test harness for node packs

No codegen importers for SDK surfaces

3) Scope
3.1 In scope

Finish npm packs as first class RSP

Implement MCP bridge (stdio and HTTP) that exports the registry

Implement pack set snapshotting and hot swap

Implement update controller with tool shape diff, canary, rollback

Add at least 2 “real” packs (one pip, one npm) beyond echo

3.2 Out of scope for this PRP

Public marketplace (RIG Hub marketplace)

Full hosted multi tenant SaaS (RIG Hub) beyond scaffolding

Automatic “wrap any SDK with zero config” for every package method (we will build guided importers with selection)

4) RIG Standard deliverables
4.1 RTP finalization

Freeze ToolDef fields and required error taxonomy

Define a strict RTP Result object for both RGP and MCP bridge responses

Provide JSON schema files for:

ToolDef

ToolResult

ToolError

ApprovalRequired payload

4.2 RSP for Python and Node packs

Create a single conceptual RSP with two concrete implementations:

Python RSP

Distribution: pip package rig-pack-*

Discovery: Python entry points rig.packs

Pack entry exports:

rig_pack_metadata() -> dict

rig_tools() -> list[ToolDef]

rig_impls() -> dict[name, RegisteredTool]

Node RSP

Distribution: npm package @rig/pack-*

Discovery: node runner loads packs from config and resolves them through node module resolution

Pack exports:

metadata(): { name, version }

tools(): ToolDef[]

invoke(toolName, args, ctx): Promise<{ ok, output, error }>

ToolDef must match RTP schema exactly (same JSON schema fields and risk tags)

4.3 RGP finalization

Publish an OpenAPI spec for RGP:

list tools

call tool

approvals approve and deny

health

audit query

Define explicit headers and fields:

correlation id

tenant id

actor id

5) Architecture changes to implement
5.1 Registry snapshots

Add a formal “pack set snapshot” concept:

registry snapshot includes:

interface_hash

pack_set_version

list of packs and versions

runtime holds active snapshot pointer

swaps are atomic:

inflight calls keep old snapshot

new calls use new snapshot

5.2 Unified tool execution model

All tool calls, including node tools, must go through RIG Runtime policy and audit.

Rule:

Node runner is only an execution backend

Python runtime remains the policy enforcement point

Node runner receives:

sanitized args

approved context

secrets only if explicitly allowed by pack policy (default deny)

5.3 Node runner hardening

Add tool schema validation on node side as a safety belt

Add timeouts, max payload, and concurrency caps

Add a pack sandbox mode option (future, at least isolate working directory now)

Add strict redaction of secrets from logs

6) MCP bridge implementation
6.1 Requirements

rig serve mcp starts an MCP server that:

lists tools from the live registry snapshot

calls tools via runtime pipeline

returns RTP normalized errors

Transport support:

stdio mode

HTTP mode

Update behavior:

HTTP bridge reflects registry snapshot swaps instantly

stdio bridge restarts under a supervisor when snapshot changes

6.2 Mapping rules

MCP tools list maps to registry list

MCP tool call maps to runtime call

Any approvals required must surface as an error payload that includes an approval token and a clear remediation hint

7) Auto update and instant update
7.1 Update controller

Implement an update service (can run inside rig serve for v0, separate process later) that:

Detects new versions:

pip packs and dependencies

npm packs and dependencies

Builds a candidate pack set

Runs verification:

pack contract tests

tool shape diff

Promotes candidate to canary snapshot

Monitors canary signals

Promotes to stable or rolls back automatically

7.2 Tool shape diff gate

Compute a diff over:

tool added or removed

input schema changes

output schema changes

error schema changes

risk class changes

Block auto promotion if:

tool removed

required input field added

incompatible type change

risk class elevated (read to money, write to destructive, etc)

Allow auto promotion if:

optional fields added

new tools added but disabled by default until allowed

patch compatible changes

7.3 Canary and rollback

Canary cohorts:

percent of tenants (hosted later)

for now, percent of calls per tool

Rollback triggers:

error rate spike

latency spike

increase in retries

increase in approval_required for tools that were previously auto approved

8) Developer experience requirements
8.1 CLI upgrades

Add commands and make them real:

rig add pip rig-pack-x

rig add npm @rig/pack-x

rig remove pip rig-pack-x

rig remove npm @rig/pack-x

rig packs shows installed packs and versions

rig doctor checks:

node runner reachable

pack discovery working

schema validation dependencies installed

audit DB writable

rig update

runs update controller once

prints tool shape diff summary

supports --apply and --dry-run

8.2 Config

Unify config as rig.yaml with:

enabled packs by source (pip, npm)

node runner URL and enable flag

policy defaults and risk approvals

update policy and rollout settings

audit sink config

9) Packs to ship in this phase

Minimum packs beyond echo:

9.1 Python pack

rig-pack-http or rig-pack-github (choose one and implement cleanly)

Must demonstrate auth slot usage and safe read operations

Must include contract tests with mocked responses

9.2 Node pack

@rig/pack-fs (safe filesystem operations in a sandbox dir) or @rig/pack-fetch (HTTP fetch with allow list)

Must demonstrate schema validation and error mapping

Must include contract tests

Both packs should be safe by default and highlight RIG policy gating.

10) Testing
10.1 Test layers

Unit tests:

RTP schemas and validation

policy decisions

approval token lifecycle

interface hash stability

Integration tests:

RGP server tool call end to end

node runner ingestion and proxy call end to end

MCP bridge list and call end to end

Update tests:

tool shape diff blocks breaking changes

snapshot swap is atomic

rollback restores previous snapshot

10.2 Contract test harness

Create a standard test runner that packs can plug into:

Python packs: pytest based contract tests

Node packs: vitest or node test runner contract tests

A shared “golden RTP” test vectors folder:

expected tool defs

expected error shapes

11) Acceptance criteria
11.1 npm support is real

rig add npm @rig/pack-echo installs or registers the pack in config

node runner loads it and exposes tools

rig list shows node tools

rig call <node tool> works through the runtime pipeline

policy and approvals apply to node tools the same way as python tools

11.2 MCP bridge works

rig serve mcp lists tools and can call them

MCP tool calls enforce the same policy and approval pipeline

stdio restart behavior on snapshot change is implemented

11.3 Auto update and instant update work

system detects a pack version bump (simulated is fine)

runs tool shape diff and blocks breaking changes

promotes a passing candidate via canary

swaps snapshots without manual steps

rolls back on induced failure

12) Milestones
Milestone 1: RIG Standard hardening

Freeze RTP schemas and publish them in repo
Finalize RSP for python and node

Finalize RGP OpenAPI spec

Milestone 2: npm packs first class

rig add npm and pack discovery flow

node runner hardening

node pack contract test harness

Milestone 3: MCP bridge

implement bridge stdio and HTTP

adapter uses live registry snapshot

restart strategy for stdio on snapshot change

Milestone 4: Updates

snapshot manager

tool shape diff

update controller run once via rig update

canary and rollback

Milestone 5: Ship real packs

1 python pack with auth

1 node pack with sandbox or allow list

end to end examples in examples/

13) Implementation instructions for the dev agent

Keep a task list file at repo root and update it after each meaningful change

Always implement vertical slices with tests:

pack install or discovery

tool listing

tool call

policy and approvals

Never allow secrets into model facing outputs or logs

MCP bridge must be an adapter over registry and runtime, not a separate tool system

For npm packs, keep the node runner minimal and treat it as a semi trusted boundary

Build the update controller with a strict “no breaking changes by default” rule

14) PRP task list seed (initial order)

Add RTP JSON schema files and validation tests

Add RGP OpenAPI spec and conformance tests

Implement node pack RSP contract and enforce ToolDef schema matching RTP

Implement rig add npm to write config and trigger node runner reload

Implement node runner reload and pack list endpoint

Add proxy execution path in runtime with consistent error mapping

Implement registry snapshot manager and atomic swap

Implement MCP bridge with tool listing and tool call routed to runtime

Implement stdio bridge supervisor restart on snapshot change

Implement tool shape diff and unit tests

Implement update controller run once and integrate into rig update

Implement canary metrics counters and rollback thresholds

Add one real python pack plus contract tests

Add one real node pack plus contract tests

Write docs: quickstart, pack author guide, policy guide, MCP export guideose