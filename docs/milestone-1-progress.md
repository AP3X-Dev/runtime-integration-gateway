# Milestone 1 Progress Report: RIG Standard Hardening

**Date**: 2026-01-13  
**Status**: In Progress (Major Components Complete)

## Overview

Milestone 1 focuses on hardening the RIG Standard by freezing RTP schemas, finalizing RSP for Python and Node packs, and creating the RGP OpenAPI specification.

## Completed Work

### 1. RTP JSON Schema Files ✅

Created canonical JSON Schema definitions for all RTP core types:

- **`schemas/rtp/ToolDef.schema.json`** - Tool definition schema
  - Validates tool name, description, input/output/error schemas
  - Enforces risk class enum (read, write, infra, money, destructive)
  - Validates auth slot naming (uppercase with underscores)
  - Includes policy defaults and examples

- **`schemas/rtp/ToolError.schema.json`** - Error structure schema
  - Standardized error taxonomy (12 error types)
  - Retryable flag for transient failures
  - Remediation hints for error resolution
  - Upstream error code preservation

- **`schemas/rtp/ToolResult.schema.json`** - Tool execution result schema
  - Success/error discriminated union (ok: true/false)
  - Includes pack metadata (pack, version, interface hash)
  - Correlation ID for tracing
  - Pack set version for snapshot tracking

- **`schemas/rtp/CallContext.schema.json`** - Execution context schema
  - Tenant ID for multi-tenancy
  - Request ID for correlation
  - Actor identity

- **`schemas/rtp/ApprovalRequired.schema.json`** - Approval payload schema
  - Approval token (UUID format)
  - Tool name and risk class
  - Sanitized arguments (secrets redacted)
  - Timestamp and expiration

**Documentation**: `schemas/rtp/README.md` with usage examples and versioning policy

### 2. RTP Schema Validation Tests ✅

Created comprehensive test suite in `tests/test_rtp_schemas.py`:

- **27 tests, all passing**
- Tests for each schema (ToolDef, ToolError, ToolResult, CallContext, ApprovalRequired)
- Valid and invalid input cases
- Python dataclass conformance tests
- Schema stability regression tests
- All error types validated

**Test Coverage**:
- Minimal valid inputs
- Fully populated inputs
- Python model serialization
- Invalid field values
- Missing required fields
- Pattern validation (names, tokens, hashes)

### 3. RGP OpenAPI Specification ✅

Created formal OpenAPI 3.0 specification at `specs/rgp-openapi.yaml`:

**Endpoints**:
- `GET /v1/health` - Health check
- `GET /v1/tools` - List all tools
- `GET /v1/tools/{name}` - Get tool definition
- `POST /v1/tools/{name}:call` - Call a tool
- `POST /v1/approvals/{token}:approve` - Approve pending call
- `POST /v1/approvals/{token}:deny` - Deny pending call
- `POST /v1/audit/query` - Query audit logs (planned)

**Headers**:
- `X-RIG-Correlation-ID` - Request tracing
- `X-RIG-Tenant-ID` - Multi-tenancy support
- `X-RIG-Actor-ID` - Actor identification

**Schemas**:
- Complete component schemas for all request/response types
- Error taxonomy matching RTP
- Audit query structures (for future implementation)

**Documentation**: `specs/README.md` with usage examples and validation instructions

### 4. RGP Conformance Tests ✅

Created conformance test suite in `tests/test_rgp_conformance.py`:

- **17 tests, all passing**
- Tests for all RGP endpoints
- Header propagation validation
- Error response format validation
- Approval workflow testing
- Correlation ID tracking

**Test Classes**:
- `TestHealthEndpoint` - Health check conformance
- `TestToolsEndpoint` - Tool discovery conformance
- `TestToolCallEndpoint` - Tool invocation conformance
- `TestApprovalsEndpoint` - Approval workflow conformance
- `TestHeaderPropagation` - Header handling
- `TestErrorResponseFormat` - Error structure validation
- `TestResultMetadata` - Result metadata validation

### 5. Test Infrastructure ✅

- Created `pytest.ini` with test configuration
- Created `tests/conftest.py` for shared fixtures
- All 44 tests passing (27 RTP schema + 17 RGP conformance)
- Fast test execution (~1 second total)

## Remaining Work for Milestone 1

### RSP Python Pack Contract
- [ ] Document Python RSP contract in `docs/rsp-python.md`
- [ ] Create Python pack contract test harness
- [ ] Update rig-pack-echo to match finalized RSP
- [ ] Add golden test vectors

### RSP Node Pack Contract
- [ ] Document Node RSP contract in `docs/rsp-node.md`
- [ ] Create Node pack contract test harness
- [ ] Update @rig/pack-echo to match finalized RSP
- [ ] Share golden test vectors with Python

## Impact

### For Pack Authors
- Clear, machine-readable schemas for tool definitions
- Validation tools to ensure pack compliance
- Stable contract that won't change without major version bump

### For RIG Runtime
- Formal validation rules for all inputs
- Standardized error handling across all tools
- Clear API contract for integrations

### For MCP Bridge (Milestone 3)
- Well-defined mapping from RTP to MCP
- Consistent error handling
- Header propagation rules

## Metrics

- **Schemas Created**: 5 JSON Schema files
- **Tests Written**: 44 (100% passing)
- **API Endpoints Specified**: 7
- **Error Types Defined**: 12
- **Risk Classes Defined**: 5
- **Lines of Test Code**: ~330
- **Lines of Schema**: ~510

## Next Steps

1. Complete RSP documentation for Python and Node packs
2. Create pack contract test harnesses
3. Update example packs to match finalized contracts
4. Begin Milestone 2: npm packs first class

## Files Created/Modified

### Created
- `schemas/rtp/ToolDef.schema.json`
- `schemas/rtp/ToolError.schema.json`
- `schemas/rtp/ToolResult.schema.json`
- `schemas/rtp/CallContext.schema.json`
- `schemas/rtp/ApprovalRequired.schema.json`
- `schemas/rtp/README.md`
- `specs/rgp-openapi.yaml`
- `specs/README.md`
- `tests/test_rtp_schemas.py`
- `tests/test_rgp_conformance.py`
- `tests/conftest.py`
- `pytest.ini`
- `TASKS.md`
- `docs/milestone-1-progress.md`

### Modified
- None (all new files)

## Conclusion

Milestone 1 is approximately **60% complete**. The core RIG Standard (RTP and RGP) is now formally specified with JSON schemas and OpenAPI, with comprehensive test coverage. The remaining work focuses on finalizing the RSP pack contracts for Python and Node.

The foundation is solid and ready for Milestone 2 (npm packs) and Milestone 3 (MCP bridge).

