# RIG Protocol Specifications

This directory contains the formal specifications for RIG protocols.

## RGP (RIG Gateway Protocol)

**File**: `rgp-openapi.yaml`

RGP is the native HTTP API for RIG. It provides:

- **Tool Discovery**: List and inspect available tools
- **Tool Invocation**: Execute tools through the RIG Runtime pipeline
- **Approval Workflow**: Approve or deny risky operations
- **Audit Queries**: Query execution history (planned)

### Key Features

1. **Standardized Headers**
   - `X-RIG-Correlation-ID`: Request tracing
   - `X-RIG-Tenant-ID`: Multi-tenancy support
   - `X-RIG-Actor-ID`: Actor identification

2. **Runtime Pipeline Integration**
   - All tool calls go through RIG Runtime
   - Automatic validation, policy enforcement, approvals
   - Secrets injection and audit logging

3. **Error Taxonomy**
   - Standardized error types (validation_error, auth_error, etc.)
   - Retryable flag for transient failures
   - Remediation hints for error resolution

### Endpoints

- `GET /v1/health` - Health check
- `GET /v1/tools` - List all tools
- `GET /v1/tools/{name}` - Get tool definition
- `POST /v1/tools/{name}:call` - Call a tool
- `POST /v1/approvals/{token}:approve` - Approve pending call
- `POST /v1/approvals/{token}:deny` - Deny pending call
- `POST /v1/audit/query` - Query audit logs (planned)

### Usage Example

```bash
# List tools
curl http://localhost:8788/v1/tools

# Call a tool
curl -X POST http://localhost:8788/v1/tools/echo:call \
  -H "Content-Type: application/json" \
  -H "X-RIG-Correlation-ID: req-123" \
  -d '{"args": {"message": "hello"}}'

# Approve a risky operation
curl -X POST http://localhost:8788/v1/approvals/{token}:approve \
  -H "X-RIG-Actor-ID: admin@example.com"
```

### Validation

The OpenAPI spec can be validated using standard tools:

```bash
# Using openapi-spec-validator
pip install openapi-spec-validator
openapi-spec-validator specs/rgp-openapi.yaml

# Using Swagger Editor
# Visit https://editor.swagger.io and paste the spec
```

### Conformance Testing

RGP server implementations must pass conformance tests in `tests/test_rgp_conformance.py`.

## Future Specifications

- **MCP Bridge Protocol**: Mapping between RGP and MCP
- **Pack Contract Specification**: Formal RSP for Python and Node packs
- **Update Protocol**: Snapshot management and canary rollout

## Versioning

Specifications follow semantic versioning:

- **Major**: Breaking changes to the protocol
- **Minor**: Backward-compatible additions
- **Patch**: Documentation or clarification

Current versions:
- RGP: 1.0.0 (frozen as of Milestone 1)

