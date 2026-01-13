# RIG Implementation Task List

This task list tracks the implementation of RIG (Runtime Integration Gateway) based on PRP.md requirements.

## Milestone 1: RIG Standard Hardening
**Goal**: Freeze RTP schemas, finalize RSP for Python and Node, finalize RGP OpenAPI spec

### 1.1 RTP Schema Finalization
- [x] Create JSON Schema files for RTP core types
  - [x] Create `schemas/rtp/ToolDef.schema.json`
  - [x] Create `schemas/rtp/ToolResult.schema.json`
  - [x] Create `schemas/rtp/ToolError.schema.json`
  - [x] Create `schemas/rtp/ApprovalRequired.schema.json`
  - [x] Create `schemas/rtp/CallContext.schema.json`
- [x] Add validation tests for RTP schemas
  - [x] Test ToolDef schema validation (valid and invalid cases)
  - [x] Test ToolResult schema validation
  - [x] Test ToolError schema validation with all error types
  - [x] Test ApprovalRequired payload validation
  - [x] Test schema stability (hash-based regression tests)

### 1.2 RSP Python Pack Contract
- [ ] Document Python RSP contract in `docs/rsp-python.md`
  - [ ] Entry point specification (rig.packs)
  - [ ] Required exports: rig_pack_metadata(), rig_tools(), rig_impls()
  - [ ] ToolDef schema matching requirements
  - [ ] Error handling contract
- [ ] Create Python pack contract test harness
  - [ ] Create `packages/rig-core/rig_core/pack_contract_tests.py`
  - [ ] Add test runner for pack validation
  - [ ] Add golden test vectors in `tests/golden/rtp/`
- [ ] Update rig-pack-echo to match finalized RSP
  - [ ] Verify metadata export
  - [ ] Verify ToolDef schema compliance
  - [ ] Add contract tests for echo pack

### 1.3 RSP Node Pack Contract
- [ ] Document Node RSP contract in `docs/rsp-node.md`
  - [ ] npm package naming (@rig/pack-*)
  - [ ] Required exports: metadata(), tools(), invoke()
  - [ ] ToolDef schema matching RTP exactly
  - [ ] Error mapping to RTP error taxonomy
- [ ] Create Node pack contract test harness
  - [ ] Create test runner in `packages/rig-node-runner/src/contract-tests.ts`
  - [ ] Add schema validation on node side
  - [ ] Share golden test vectors from `tests/golden/rtp/`
- [ ] Update @rig/pack-echo to match finalized RSP
  - [ ] Implement metadata() export
  - [ ] Implement tools() with RTP-compliant ToolDef
  - [ ] Implement invoke() with proper error mapping
  - [ ] Add contract tests

### 1.4 RGP OpenAPI Specification
- [x] Create RGP OpenAPI spec at `specs/rgp-openapi.yaml`
  - [x] Define `/v1/health` endpoint
  - [x] Define `/v1/tools` (list tools)
  - [x] Define `/v1/tools/{name}/call` (call tool)
  - [x] Define `/v1/approvals/{token}/approve` endpoint
  - [x] Define `/v1/approvals/{token}/deny` endpoint
  - [x] Define `/v1/audit/query` endpoint
  - [x] Add headers: correlation_id, tenant_id, actor_id
- [x] Add RGP conformance tests
  - [x] Test all endpoints match OpenAPI spec
  - [x] Test header propagation
  - [x] Test error response formats
  - [x] Test correlation_id in responses

## Milestone 2: npm Packs First Class
**Goal**: Complete npm pack lifecycle with discovery, installation, hardening, and contract tests

### 2.1 npm Pack Discovery and Installation
- [ ] Implement `rig add npm` command
  - [ ] Parse npm package name
  - [ ] Update rig.yaml with npm pack entry
  - [ ] Trigger node runner reload
  - [ ] Verify pack loaded successfully
- [ ] Implement `rig remove npm` command
  - [ ] Remove pack from rig.yaml
  - [ ] Trigger node runner reload
  - [ ] Verify pack unloaded
- [ ] Implement `rig packs` command
  - [ ] List all installed packs (pip and npm)
  - [ ] Show pack versions
  - [ ] Show pack source (pip/npm)
  - [ ] Show tool count per pack
- [ ] Add node runner reload endpoint
  - [ ] POST `/v1/reload` endpoint
  - [ ] Reload packs from config
  - [ ] Return new pack list

### 2.2 Node Runner Hardening
- [ ] Add schema validation on node side
  - [ ] Validate tool args against input_schema before execution
  - [ ] Validate tool output against output_schema after execution
  - [ ] Return validation errors in RTP format
- [ ] Add execution safeguards
  - [ ] Implement timeout per tool call (configurable)
  - [ ] Implement max payload size limit
  - [ ] Implement concurrency caps
  - [ ] Add working directory isolation
- [ ] Add secrets redaction
  - [ ] Redact secrets from console logs
  - [ ] Redact secrets from error messages
  - [ ] Never expose secrets in responses
- [ ] Add error normalization
  - [ ] Map JavaScript errors to RTP error types
  - [ ] Preserve stack traces in internal logs only
  - [ ] Return structured ToolError responses

### 2.3 Runtime Proxy for Node Tools
- [ ] Implement consistent node tool execution path in runtime
  - [ ] Route node tool calls through RIG Runtime policy
  - [ ] Apply same approval gates as Python tools
  - [ ] Apply same retry logic as Python tools
  - [ ] Ensure audit logging for node tool calls
- [ ] Add integration tests
  - [ ] Test node tool call end-to-end through runtime
  - [ ] Test policy enforcement on node tools
  - [ ] Test approval flow for risky node tools
  - [ ] Test error mapping from node to RTP

### 2.4 CLI Developer Experience
- [ ] Implement `rig doctor` command
  - [ ] Check node runner reachable
  - [ ] Check pack discovery working (pip and npm)
  - [ ] Check schema validation dependencies installed
  - [ ] Check audit DB writable
  - [ ] Report configuration issues
- [ ] Improve config management
  - [ ] Validate rig.yaml schema on load
  - [ ] Provide helpful error messages for config issues
  - [ ] Support config merge from multiple sources

## Milestone 3: MCP Bridge
**Goal**: Implement MCP bridge (stdio and HTTP) that exports live registry and routes through runtime

### 3.1 MCP Bridge Core
- [ ] Implement MCP protocol adapter
  - [ ] Map MCP tools/list to registry.list_tools()
  - [ ] Map MCP tools/call to runtime.call()
  - [ ] Map RTP errors to MCP error format
  - [ ] Handle approval_required as MCP error with remediation
- [ ] Implement stdio transport
  - [ ] Read JSON-RPC from stdin
  - [ ] Write JSON-RPC to stdout
  - [ ] Handle initialization handshake
  - [ ] Handle shutdown gracefully
- [ ] Implement HTTP transport
  - [ ] POST /mcp endpoint for JSON-RPC
  - [ ] Support SSE for streaming (future)
  - [ ] Add CORS headers for browser clients
- [ ] Add `rig serve mcp` command
  - [ ] Support --transport=stdio (default)
  - [ ] Support --transport=http
  - [ ] Pass registry snapshot to bridge
  - [ ] Route all calls through runtime

### 3.2 MCP Bridge Update Behavior
- [ ] Implement snapshot change detection
  - [ ] Monitor registry snapshot hash
  - [ ] Detect when snapshot changes
- [ ] Implement stdio restart on snapshot change
  - [ ] Create supervisor process for stdio bridge
  - [ ] Restart stdio bridge when snapshot changes
  - [ ] Preserve client connection state if possible
- [ ] HTTP bridge instant reflection
  - [ ] HTTP bridge uses live registry snapshot
  - [ ] No restart needed for HTTP mode
  - [ ] Document difference in behavior

### 3.3 MCP Bridge Tests
- [ ] Add integration tests
  - [ ] Test MCP tools/list returns all registry tools
  - [ ] Test MCP tools/call executes through runtime
  - [ ] Test policy enforcement via MCP
  - [ ] Test approval_required error format
  - [ ] Test stdio transport end-to-end
  - [ ] Test HTTP transport end-to-end

## Milestone 4: Updates
**Goal**: Implement snapshot manager, tool shape diff, update controller, canary, and rollback

### 4.1 Registry Snapshot Manager
- [ ] Implement formal snapshot concept
  - [ ] Add SnapshotManager class
  - [ ] Snapshot includes: interface_hash, pack_set_version, pack list with versions
  - [ ] Support multiple snapshots (active, canary, previous)
- [ ] Implement atomic snapshot swap
  - [ ] Runtime holds active snapshot pointer
  - [ ] Inflight calls keep old snapshot
  - [ ] New calls use new snapshot
  - [ ] Add swap operation with rollback capability
- [ ] Add snapshot persistence
  - [ ] Save snapshots to `.rig/snapshots/`
  - [ ] Load snapshot on startup
  - [ ] Support snapshot history

### 4.2 Tool Shape Diff
- [ ] Implement tool shape diff engine
  - [ ] Detect tool added
  - [ ] Detect tool removed
  - [ ] Detect input schema changes (breaking vs compatible)
  - [ ] Detect output schema changes
  - [ ] Detect error schema changes
  - [ ] Detect risk class changes
- [ ] Implement breaking change detection
  - [ ] Block: tool removed
  - [ ] Block: required input field added
  - [ ] Block: incompatible type change
  - [ ] Block: risk class elevated (read→money, write→destructive)
  - [ ] Allow: optional fields added
  - [ ] Allow: new tools added (disabled by default)
  - [ ] Allow: patch-compatible changes
- [ ] Add diff tests
  - [ ] Test all breaking change scenarios
  - [ ] Test all compatible change scenarios
  - [ ] Test diff output format

### 4.3 Update Controller
- [ ] Implement update detection
  - [ ] Detect new pip pack versions
  - [ ] Detect new npm pack versions
  - [ ] Build candidate pack set
- [ ] Implement verification pipeline
  - [ ] Run pack contract tests on candidate
  - [ ] Compute tool shape diff
  - [ ] Block if breaking changes detected
  - [ ] Generate update report
- [ ] Implement `rig update` command
  - [ ] Support --dry-run (show diff, no apply)
  - [ ] Support --apply (promote to canary)
  - [ ] Print tool shape diff summary
  - [ ] Show breaking changes prominently
  - [ ] Require confirmation for risky updates

### 4.4 Canary and Rollback
- [ ] Implement canary promotion
  - [ ] Create canary snapshot
  - [ ] Route percentage of calls to canary
  - [ ] Collect canary metrics (error rate, latency, retries)
- [ ] Implement canary monitoring
  - [ ] Track error rate per snapshot
  - [ ] Track latency per snapshot
  - [ ] Track retry rate per snapshot
  - [ ] Track approval_required rate per snapshot
- [ ] Implement rollback triggers
  - [ ] Rollback on error rate spike (>2x baseline)
  - [ ] Rollback on latency spike (>2x baseline)
  - [ ] Rollback on retry increase (>2x baseline)
  - [ ] Rollback on approval_required increase for previously auto-approved tools
- [ ] Implement automatic rollback
  - [ ] Swap back to previous snapshot
  - [ ] Log rollback event to audit
  - [ ] Notify via configured channels
- [ ] Add update tests
  - [ ] Test canary promotion
  - [ ] Test automatic rollback on error spike
  - [ ] Test snapshot swap is atomic

## Milestone 5: Ship Real Packs
**Goal**: Create 1 Python pack and 1 Node pack with auth, tests, and examples

### 5.1 Python Pack (rig-pack-github or rig-pack-http)
- [ ] Choose pack to implement (recommend rig-pack-github)
- [ ] Implement pack structure
  - [ ] Create package in `packages/rig-pack-github/`
  - [ ] Implement rig_pack_metadata()
  - [ ] Implement rig_tools() with auth slots
  - [ ] Implement rig_impls() with safe read operations
- [ ] Implement tools
  - [ ] Tool: get_repository (read repo metadata)
  - [ ] Tool: list_issues (read issues with pagination)
  - [ ] Tool: search_code (search with query)
  - [ ] All tools use GITHUB_TOKEN auth slot
  - [ ] All tools are risk_class="read"
- [ ] Add contract tests
  - [ ] Mock GitHub API responses
  - [ ] Test all tools with valid inputs
  - [ ] Test error handling (auth errors, not found, rate limits)
  - [ ] Test schema compliance
- [ ] Add documentation
  - [ ] README with setup instructions
  - [ ] Example usage in `examples/github-pack/`

### 5.2 Node Pack (@rig/pack-fs or @rig/pack-fetch)
- [ ] Choose pack to implement (recommend @rig/pack-fs)
- [ ] Implement pack structure
  - [ ] Create package in `npm-packs/pack-fs/`
  - [ ] Implement metadata() export
  - [ ] Implement tools() export with RTP-compliant schemas
  - [ ] Implement invoke() with sandbox enforcement
- [ ] Implement tools
  - [ ] Tool: read_file (read from sandbox dir only)
  - [ ] Tool: write_file (write to sandbox dir only)
  - [ ] Tool: list_directory (list sandbox dir only)
  - [ ] All tools enforce sandbox path restrictions
  - [ ] All tools are risk_class="write" (except read_file: "read")
- [ ] Add contract tests
  - [ ] Test sandbox enforcement (reject paths outside sandbox)
  - [ ] Test all tools with valid inputs
  - [ ] Test error handling (permission denied, not found)
  - [ ] Test schema compliance
- [ ] Add documentation
  - [ ] README with setup instructions
  - [ ] Example usage in `examples/fs-pack/`

### 5.3 End-to-End Examples
- [ ] Create quickstart example
  - [ ] Install both packs
  - [ ] List tools
  - [ ] Call tools with approval flow
  - [ ] Show policy configuration
- [ ] Create MCP export example
  - [ ] Start MCP bridge
  - [ ] Connect MCP client
  - [ ] Call tools via MCP
- [ ] Create update example
  - [ ] Simulate pack version bump
  - [ ] Run rig update --dry-run
  - [ ] Show tool shape diff
  - [ ] Apply update with canary

## Testing Requirements (Cross-Milestone)

### Unit Tests
- [ ] RTP schema validation tests
- [ ] Policy decision tests
- [ ] Approval token lifecycle tests
- [ ] Interface hash stability tests
- [ ] Tool shape diff tests
- [ ] Secrets redaction tests

### Integration Tests
- [ ] RGP server tool call end-to-end
- [ ] Node runner ingestion and proxy call end-to-end
- [ ] MCP bridge list and call end-to-end
- [ ] Snapshot swap atomicity test
- [ ] Canary rollback test

### Contract Tests
- [ ] Python pack contract test harness
- [ ] Node pack contract test harness
- [ ] Golden RTP test vectors

## Documentation (Final Phase)

- [ ] Write `docs/quickstart.md`
- [ ] Write `docs/pack-author-guide-python.md`
- [ ] Write `docs/pack-author-guide-node.md`
- [ ] Write `docs/policy-guide.md`
- [ ] Write `docs/mcp-export-guide.md`
- [ ] Write `docs/update-and-rollback.md`
- [ ] Update main README.md with complete feature set

---

## Progress Tracking

**Current Milestone**: Milestone 1 (RIG Standard Hardening)
**Current Focus**: RSP Python and Node pack contracts

**Completed Tasks**: 3
**Total Tasks**: ~150+

**Last Updated**: 2026-01-13

## Recent Completions

### 2026-01-13
- ✅ Created RTP JSON Schema files (ToolDef, ToolResult, ToolError, ApprovalRequired, CallContext)
- ✅ Added comprehensive RTP schema validation tests (27 tests, all passing)
- ✅ Created pytest configuration and test infrastructure
- ✅ Created RGP OpenAPI specification (v1.0.0) with all endpoints
- ✅ Added RGP conformance tests (17 tests, all passing)

