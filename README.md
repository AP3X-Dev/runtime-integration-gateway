# RIG (Runtime Integration Gateway)

RIG is a tool platform for AI agents that acts as an "SDK tool operating system."

## Core Functions

- **Turns SDKs into tools** - Install "packs" (pip or npm packages) that wrap SDKs and expose them as structured tools with JSON schemas
- **Runs tools safely** - Enforces validation, secrets isolation, policies, approvals, retries, and audit logging through RIG Runtime
- **Exports as MCP** - Instantly exposes your tool catalog as an MCP server via RIG Bridge

## Key Architecture

- **Packs**: pip/npm packages that wrap SDKs (like "drivers")
- **Registry**: Tool discovery and version management
- **Runtime**: Policy enforcement kernel (approvals, secrets, retries, audit)
- **RGP**: Native API for calling tools
- **MCP Bridge**: Compatibility layer for MCP clients
- **Hub**: Optional hosted control plane for teams

## Quick Start

### Installation

```powershell
# Clone the repository
git clone https://github.com/AP3X-Dev/runtime-integration-gateway.git
cd runtime-integration-gateway

# Install in development mode (Windows)
.\install-dev.ps1

# Or manually (cross-platform)
pip install -e packages/rig-core
pip install -e packages/rig-protocol-rgp
pip install -e packages/rig-cli
pip install -e packages/rig-bridge-mcp
```

### Add to PATH (Windows)

```powershell
# PowerShell (run as Administrator)
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
$scriptsPath = "$env:LOCALAPPDATA\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\Scripts"
[Environment]::SetEnvironmentVariable("Path", "$userPath;$scriptsPath", "User")

# Restart your terminal, then verify
rig --help
```

### Usage

```bash
# View available packs from the pack index
rig packs --available

# Install a pack (e.g., Stripe)
rig install stripe

# List installed tools
rig list

# Start the RGP server
rig serve

# Start the MCP server
rig mcp
```

## Available Packs

| Pack | Tools | Description |
|------|-------|-------------|
| [stripe](packages/rig-pack-stripe) | 8 | Payment processing |
| [twilio](packages/rig-pack-twilio) | 5 | SMS, voice, verification |
| [slack](packages/rig-pack-slack) | 4 | Team messaging |
| [sendgrid](packages/rig-pack-sendgrid) | 2 | Email delivery |
| [github](packages/rig-pack-github) | 4 | Repository management |
| [google](packages/rig-pack-google) | 3 | Sheets, Drive, Gmail |
| [notion](packages/rig-pack-notion) | 4 | Workspace management |
| [airtable](packages/rig-pack-airtable) | 3 | Database management |
| [supabase](packages/rig-pack-supabase) | 4 | Backend services |
| [elevenlabs](packages/rig-pack-elevenlabs) | 2 | AI voice synthesis |

**Total: 39 tools across 10 packs**

## Documentation

- [Quickstart Guide](examples/quickstart.md) - 5-minute setup guide
- [Milestone 2 Summary](docs/milestone-2-complete.md) - Pack ecosystem details
- [Pack Index](https://raw.githubusercontent.com/AP3X-Dev/runtime-integration-gateway/master/specs/pack-index-example.json) - Available packs registry

## Example Usage

Initialize config:

```bash
rig init
```

Start the gateway:

```bash
rig serve
```

List tools:

```bash
rig list
```

Call a tool:

```bash
rig call echo '{"message":"hi"}'
```

If a tool requires approval, the call will return an approval_required error with a token. Approve it:

```bash
rig approve <token>
```

## Notes

- The MCP bridge and updater are stubbed in this v0 repo.
- Pack discovery uses Python entry points under the group rig.packs.


## Node packs via rig-node-runner

This repo also includes a Node runner that can load npm packs and expose their tools to the Python runtime.

From the repo root:

```bash
npm install
RIG_NODE_PACKS=@rig/pack-echo npm --workspace packages/rig-node-runner start
```

Enable the node runner in rig.yaml:

```yaml
node_runner:
  enabled: true
  url: http://127.0.0.1:8790
```

Now start the RIG server and call the node tool:

```bash
rig serve
rig list
rig call echo_node '{"message":"hi"}'
```
