# RIG Pack Developer Guide

This guide explains how to create and publish RIG packs.

## What is a RIG Pack?

A RIG pack is a Python or Node.js package that provides tools for AI agents. Each pack:

1. Exports a `rig_pack.json` manifest
2. Implements tools using the RIG Tool Protocol (RTP)
3. Can be installed with `rig install <pack-name>`

## Creating a Python Pack

### 1. Project Structure

```
rig-pack-notion/
├── pyproject.toml
├── README.md
├── rig_pack.json          # Pack manifest
└── rig_pack_notion/
    ├── __init__.py
    ├── tools.py           # Tool implementations
    └── auth.py            # Auth handlers (optional)
```

### 2. Pack Manifest (rig_pack.json)

```json
{
  "name": "notion",
  "version": "1.0.0",
  "description": "Notion workspace integration",
  "author": "Your Name",
  "homepage": "https://github.com/yourname/rig-pack-notion",
  "license": "MIT",
  "runtime": "python",
  "min_rig_version": "0.1.0",
  "tools": [
    {
      "name": "notion_search",
      "description": "Search Notion workspace",
      "risk_class": "low",
      "auth_slot": "notion",
      "input_schema": {
        "type": "object",
        "properties": {
          "query": {"type": "string", "description": "Search query"}
        },
        "required": ["query"]
      }
    }
  ],
  "auth_slots": {
    "notion": {
      "type": "oauth2",
      "provider": "notion",
      "scopes": ["read_content"]
    }
  }
}
```

### 3. Tool Implementation

```python
# rig_pack_notion/tools.py
from rig_core.tool import ToolDef, ToolResult, CallContext

async def notion_search(query: str, context: CallContext) -> ToolResult:
    """Search Notion workspace."""
    try:
        # Get auth token from context
        token = context.auth.get("notion")
        if not token:
            return ToolResult.error("AUTH_REQUIRED", "Notion auth required")
        
        # Call Notion API
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.notion.com/v1/search",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Notion-Version": "2022-06-28"
                },
                json={"query": query}
            )
            response.raise_for_status()
            results = response.json()
        
        return ToolResult.success(results)
    
    except Exception as e:
        return ToolResult.error("EXECUTION_ERROR", str(e))
```

### 4. Package Configuration (pyproject.toml)

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "rig-pack-notion"
version = "1.0.0"
description = "Notion integration for RIG"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "rig-core>=0.1.0",
    "httpx>=0.27.0",
]

[project.entry-points."rig.packs"]
notion = "rig_pack_notion"
```

### 5. Package Entry Point

```python
# rig_pack_notion/__init__.py
from pathlib import Path
import json

def get_manifest():
    """Return pack manifest."""
    manifest_path = Path(__file__).parent.parent / "rig_pack.json"
    with open(manifest_path) as f:
        return json.load(f)

def get_tools():
    """Return tool implementations."""
    from .tools import notion_search
    return {
        "notion_search": notion_search,
    }
```

## Publishing Your Pack

### 1. Test Locally

```bash
# Install in development mode
pip install -e .

# Test with RIG
cd /path/to/your/project
rig init
rig add /path/to/rig-pack-notion
rig list
rig serve
```

### 2. Publish to PyPI

```bash
# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

### 3. Add to Pack Index

Submit a PR to the RIG pack index repository:

```json
{
  "notion": {
    "display_name": "Notion",
    "description": "Notion workspace integration",
    "homepage": "https://github.com/yourname/rig-pack-notion",
    "tags": ["productivity", "database"],
    "python": {
      "package": "rig-pack-notion",
      "min_rig": "0.1.0"
    }
  }
}
```

## Best Practices

### Security

1. **Never log secrets** - Use `context.auth` for credentials
2. **Validate inputs** - Use JSON schema for input validation
3. **Set appropriate risk classes**:
   - `low` - Read-only operations
   - `medium` - Write operations
   - `high` - Destructive operations
   - `critical` - Financial transactions

### Error Handling

```python
# Good: Specific error types
return ToolResult.error("AUTH_REQUIRED", "API key not found")
return ToolResult.error("RATE_LIMIT", "API rate limit exceeded")
return ToolResult.error("VALIDATION_ERROR", "Invalid input")

# Bad: Generic errors
return ToolResult.error("ERROR", "Something went wrong")
```

### Documentation

1. **Clear descriptions** - Explain what each tool does
2. **Example inputs** - Show example usage
3. **Auth requirements** - Document required credentials
4. **Rate limits** - Mention API limitations

### Testing

```python
# tests/test_tools.py
import pytest
from rig_core.tool import CallContext, ToolResult
from rig_pack_notion.tools import notion_search

@pytest.mark.asyncio
async def test_notion_search():
    context = CallContext(
        auth={"notion": "test_token"},
        correlation_id="test-123"
    )
    
    result = await notion_search("test query", context)
    assert result.success
    assert "results" in result.data
```

## Example Packs

- **rig-pack-echo** - Simple example pack
- **rig-pack-notion** - Notion integration
- **rig-pack-stripe** - Stripe payments
- **rig-pack-slack** - Slack messaging

## Resources

- [RIG Tool Protocol Spec](./rtp-spec.md)
- [Pack Index Format](./pack-distribution.md)
- [Example Pack Template](https://github.com/rig-project/pack-template)

## Support

- GitHub Issues: https://github.com/rig-project/rig/issues
- Discord: https://discord.gg/rig
- Email: support@rig.dev

