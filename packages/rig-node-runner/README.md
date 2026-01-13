# rig-node-runner

Node runner for RIG Packs installed from npm.

It loads packs listed in the RIG_NODE_PACKS environment variable and exposes an HTTP API compatible with the RIG Gateway Protocol endpoints used by the Python runtime.

## Run

npm install
RIG_NODE_PACKS=@rig/pack-echo npm start

Default listen address is 127.0.0.1:8790
