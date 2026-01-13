# RIG

RIG is the Runtime Integration Gateway.

This repo is a v0 starter implementation with:
- RTP: tool schema and call contract
- RIG Registry: tool catalog and interface hashing
- RIG Runtime: validation, policy gates, approvals, retries, audit
- RGP: HTTP discovery and invocation
- rig CLI
- One demo pack: rig-pack-echo

## Local quickstart

Create a virtual environment, then from the repo root run:

```bash
python -m pip install -U pip
python -m pip install -e packages/rig-core
python -m pip install -e packages/rig-protocol-rgp
python -m pip install -e packages/rig-cli
python -m pip install -e packages/rig-pack-echo
```

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

Call the echo tool:

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
