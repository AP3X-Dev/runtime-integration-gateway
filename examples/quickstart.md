## Node packs via rig-node-runner

Install node dependencies at repo root:

npm install

Start the node runner with the demo pack:

RIG_NODE_PACKS=@rig/pack-echo npm --workspace packages/rig-node-runner start

Then enable the node runner URL in rig.yaml:

node_runner:
  enabled: true
  url: http://127.0.0.1:8790

Now start the RIG server:

rig serve

The tool echo_node will appear in rig list and can be called with rig call.
