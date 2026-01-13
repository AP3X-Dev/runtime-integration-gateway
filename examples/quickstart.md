# RIG Quickstart Guide

Get up and running with RIG in under 5 minutes.

## Prerequisites

- Python 3.10+
- pip or uv package manager

## Installation

```bash
# Install RIG CLI
pip install rig-cli

# Or with uv (faster)
uv pip install rig-cli
```

## Quick Start

### 1. Initialize a new project

```bash
# Create a new directory
mkdir my-agent && cd my-agent

# Initialize RIG configuration
rig init
```

This creates a `rig.yaml` file with default settings.

### 2. Install a pack

```bash
# Install the Stripe pack
rig install stripe

# Install multiple packs
rig install slack twilio sendgrid
```

### 3. Configure secrets

Add your API keys to `.env`:

```bash
STRIPE_API_KEY=sk_test_...
SLACK_BOT_TOKEN=xoxb-...
```

### 4. Start the gateway

```bash
rig serve
```

The RIG gateway is now running at `http://localhost:8741`.

### 5. List available tools

```bash
rig list
```

### 6. Call a tool

```bash
rig call stripe.customers.create '{"email": "test@example.com"}'
```

## Available Packs

| Pack | Description | Install |
|------|-------------|---------|
| stripe | Payment processing | `rig install stripe` |
| twilio | SMS and voice | `rig install twilio` |
| slack | Team messaging | `rig install slack` |
| sendgrid | Email delivery | `rig install sendgrid` |
| github | Repository management | `rig install github` |
| google | Sheets, Drive, Gmail | `rig install google` |
| notion | Workspace management | `rig install notion` |
| airtable | Database management | `rig install airtable` |
| supabase | Backend services | `rig install supabase` |
| elevenlabs | AI voice synthesis | `rig install elevenlabs` |

## Configuration

Edit `rig.yaml` to customize:

```yaml
packs:
  - rig-pack-stripe
  - rig-pack-slack

policy:
  default_risk_threshold: write
  require_approval:
    - money
    - destructive

secrets:
  provider: env
```

## Node.js Packs

For Node.js packs, start the node runner:

```bash
npm install
RIG_NODE_PACKS=@rig/pack-echo npm --workspace packages/rig-node-runner start
```

Enable in `rig.yaml`:

```yaml
node_runner:
  enabled: true
  url: http://127.0.0.1:8790
```

## Next Steps

- Read the [Pack Developer Guide](../docs/pack-developer-guide.md)
- Explore the [API Reference](../specs/rgp-openapi.yaml)
- Join the community on Discord
