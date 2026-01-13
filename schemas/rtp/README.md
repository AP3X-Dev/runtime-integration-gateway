# RIG Tool Protocol (RTP) JSON Schemas

This directory contains the canonical JSON Schema definitions for the RIG Tool Protocol (RTP).

## Overview

RTP defines the contract between tool packs and the RIG Runtime. All packs (Python and Node) must conform to these schemas.

## Schema Files

### Core Types

- **`ToolDef.schema.json`** - Tool definition including name, description, input/output schemas, risk class, and auth requirements
- **`ToolResult.schema.json`** - Standardized tool execution result (success or error)
- **`ToolError.schema.json`** - Standardized error structure with error taxonomy
- **`CallContext.schema.json`** - Execution context metadata (tenant, actor, request ID)
- **`ApprovalRequired.schema.json`** - Approval request payload when policy requires explicit approval

## Error Taxonomy

RTP defines a standard set of error types for consistent error handling:

- `validation_error` - Input validation failed
- `auth_error` - Authentication failed
- `permission_error` - Authorization failed
- `not_found` - Requested resource not found
- `conflict` - Resource conflict (e.g., already exists)
- `rate_limited` - Rate limit exceeded
- `transient` - Temporary failure (network, service unavailable)
- `timeout` - Operation timed out
- `upstream_error` - Upstream service error
- `policy_blocked` - Blocked by RIG policy
- `approval_required` - Requires explicit approval
- `internal_error` - Internal tool implementation error

## Risk Classes

Tools are classified by risk level for policy enforcement:

- `read` - Read-only operations (default, lowest risk)
- `write` - Write operations that modify data
- `infra` - Infrastructure changes (create/delete resources)
- `money` - Financial transactions
- `destructive` - Irreversible destructive operations (highest risk)

## Usage

### Python Packs

Python packs should use the `rig_core.rtp` module which implements these schemas:

```python
from rig_core.rtp import ToolDef, ToolResult, ToolError

def rig_tools():
    return [
        ToolDef(
            name="my_tool",
            description="Does something useful",
            input_schema={"type": "object", "properties": {...}},
            output_schema={"type": "object", "properties": {...}},
            error_schema={"type": "object", "properties": {...}},
            risk_class="read",
            auth_slots=["API_KEY"]
        )
    ]
```

### Node Packs

Node packs must export tools that match these schemas exactly:

```typescript
export function tools(): ToolDef[] {
  return [
    {
      name: "my_tool",
      description: "Does something useful",
      input_schema: {type: "object", properties: {...}},
      output_schema: {type: "object", properties: {...}},
      error_schema: {type: "object", properties: {...}},
      risk_class: "read",
      auth_slots: ["API_KEY"],
      tags: [],
      policy_defaults: {},
      examples: []
    }
  ];
}
```

## Validation

All tool definitions are validated against these schemas at:

1. **Pack load time** - When packs are discovered and registered
2. **Runtime** - Before tool execution (input validation)
3. **Contract tests** - In pack test suites

## Versioning

These schemas follow semantic versioning:

- **Major version** changes indicate breaking changes to the protocol
- **Minor version** changes add optional fields or new error types
- **Patch version** changes fix documentation or clarify existing behavior

Current version: **1.0.0** (frozen as of Milestone 1)

## References

- [RIG Standard (RTP, RSP, RGP)](../../docs/PRP-RIG.md)
- [Pack Author Guide - Python](../../docs/pack-author-guide-python.md)
- [Pack Author Guide - Node](../../docs/pack-author-guide-node.md)

