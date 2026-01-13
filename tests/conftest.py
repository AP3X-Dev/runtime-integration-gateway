"""
Pytest configuration for RIG tests.
"""

import sys
from pathlib import Path

# Add packages to path for testing
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "packages" / "rig-core"))
sys.path.insert(0, str(repo_root / "packages" / "rig-protocol-rgp"))
sys.path.insert(0, str(repo_root / "packages" / "rig-cli"))

