#!/usr/bin/env bash
set -e

python -m pip install -U pip
python -m pip install -e packages/rig-core
python -m pip install -e packages/rig-protocol-rgp
python -m pip install -e packages/rig-cli
python -m pip install -e packages/rig-pack-echo
