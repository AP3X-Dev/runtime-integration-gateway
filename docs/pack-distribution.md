# RIG Pack Distribution System

**Status**: Phase 0 and Phase 1 Complete  
**Date**: 2026-01-13

## Overview

The RIG Pack Distribution System enables one-command installation of integration packs, making it easy for developers to add real integrations to their agents with minimal setup.

## Quick Start

```bash
# Initialize RIG project
rig init

# Install a pack
rig install notion

# List installed packs
rig packs

# Show pack information
rig info notion

# List available tools
rig list

# Start the gateway
rig serve
```

## Architecture

### Components

1. **Pack Index** - Central registry mapping short names to packages
2. **Lockfile (rig.lock)** - Records exact versions for reproducibility
3. **Pack Installer** - Handles installation and uninstallation
4. **CLI Commands** - User-facing commands for pack management

### Pack Index Format

The pack index is a JSON file that maps short pack names to actual package names on PyPI and npm:

```json
{
  "api_version": 1,
  "generated_at": "2026-01-13T00:00:00Z",
  "packs": {
    "notion": {
      "display_name": "Notion",
      "description": "Notion workspace integration",
      "homepage": "https://notion.so",
      "tags": ["productivity", "database"],
      "python": {
        "package": "rig-pack-notion",
        "min_rig": "0.1.0"
      },
      "node": {
        "package": "@rig/pack-notion",
        "min_rig": "0.1.0"
      }
    }
  }
}
```

### Lockfile Format (rig.lock)

The lockfile records exact versions of installed packs:

```json
{
  "version": 1,
  "rig_version": "0.1.0",
  "index_url": "https://example.com/index.json",
  "index_generated_at": "2026-01-13T00:00:00Z",
  "created_at": "2026-01-13T10:00:00Z",
  "updated_at": "2026-01-13T10:05:00Z",
  "packs": {
    "notion": {
      "pack_id": "notion",
      "package": "rig-pack-notion",
      "version": "1.0.0",
      "runtime": "python",
      "integrity": "sha256:abc123...",
      "installed_at": "2026-01-13T10:00:00Z"
    }
  }
}
```

## CLI Commands

### `rig install <pack>`

Install a pack from the pack index.

**Options:**
- `--runtime python|node` - Choose runtime (default: python)
- `--version <version>` - Install specific version
- `--dry-run` - Show what would be installed
- `--index-url <url>` - Use custom pack index

**Examples:**
```bash
# Install latest version
rig install notion

# Install specific version
rig install stripe --version 1.2.0

# Install Node pack
rig install slack --runtime node

# Dry run
rig install github --dry-run
```

### `rig uninstall <pack>`

Uninstall a pack.

**Options:**
- `--remove-package` - Also remove the package from system

**Examples:**
```bash
# Remove from lockfile only
rig uninstall notion

# Remove package too
rig uninstall stripe --remove-package
```

### `rig packs`

List installed packs.

**Options:**
- `--available` - Show available packs from index

**Examples:**
```bash
# Show installed packs
rig packs

# Show available packs
rig packs --available
```

### `rig info <pack>`

Show detailed information about a pack.

**Options:**
- `--index-url <url>` - Use custom pack index

**Examples:**
```bash
# Show pack info
rig info notion

# Check if installed
rig info stripe
```

## Implementation Status

### ✅ Phase 0: Core Scaffolding (Complete)

- [x] Pack index format and parser
- [x] Pack index fetcher with caching (24hr TTL)
- [x] Lockfile format and writer
- [x] Enhanced config schema
- [x] Unit tests (14 tests passing)

**Files Created:**
- `packages/rig-core/rig_core/pack_index.py`
- `packages/rig-core/rig_core/lockfile.py`
- `specs/pack-index-example.json`
- `tests/test_pack_index.py`

### ✅ Phase 1: Python Pack Installation (Complete)

- [x] Pack installer module
- [x] `rig install` command
- [x] `rig uninstall` command
- [x] `rig packs` command
- [x] `rig info` command
- [x] Virtual environment detection
- [x] Lockfile integration
- [x] Unit tests (4 tests passing)

**Files Created:**
- `packages/rig-cli/rig_cli/installer.py`
- `tests/test_cli_install.py`

**Files Modified:**
- `packages/rig-cli/rig_cli/main.py` - Added new commands

### 🚧 Phase 2: Node Pack Support (Planned)

- [ ] npm package installation
- [ ] Node runner integration
- [ ] Package.json management
- [ ] Node pack discovery

### 🚧 Phase 3: Update and Integrity (Planned)

- [ ] `rig update <pack>` command
- [ ] `rig update --all` command
- [ ] Integrity hash verification
- [ ] Index signature validation

## Test Coverage

**Total Tests**: 62 (all passing)
- Pack index tests: 14
- CLI installer tests: 4
- RGP conformance tests: 17
- RTP schema tests: 27

## Next Steps

1. Implement Node pack support (Phase 2)
2. Add pack update functionality (Phase 3)
3. Create hosted pack index
4. Build example packs (notion, stripe, slack, etc.)
5. Add pack signing and verification

## Security Considerations

- Secrets never exposed in logs or outputs
- Package integrity hashes recorded in lockfile
- Warnings for unknown publishers
- Safe defaults for high-risk tools (money, destructive)

## Example Workflow

```bash
# 1. Initialize project
rig init

# 2. Install packs
rig install notion
rig install stripe
rig install slack

# 3. Verify installation
rig packs
# Output:
# ┌─────────┬──────────────────┬─────────┬─────────┬────────────┐
# │ ID      │ Package          │ Version │ Runtime │ Installed  │
# ├─────────┼──────────────────┼─────────┼─────────┼────────────┤
# │ notion  │ rig-pack-notion  │ 1.0.0   │ python  │ 2026-01-13 │
# │ stripe  │ rig-pack-stripe  │ 0.5.0   │ python  │ 2026-01-13 │
# │ slack   │ rig-pack-slack   │ 2.1.0   │ python  │ 2026-01-13 │
# └─────────┴──────────────────┴─────────┴─────────┴────────────┘

# 4. List available tools
rig list

# 5. Start gateway
rig serve

# 6. Use with MCP
rig serve mcp
```

## Files and Directories

```
.
├── rig.yaml              # Config file
├── rig.lock              # Lockfile
├── .rig/
│   ├── cache/
│   │   └── pack_index.json  # Cached index
│   └── rig_audit.sqlite     # Audit log
└── .venv/                # Virtual environment (auto-created)
```

