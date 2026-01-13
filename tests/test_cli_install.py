"""
Tests for CLI install/uninstall commands.
"""

import json
import tempfile
from pathlib import Path

import pytest

from rig_cli.installer import PackInstaller, InstallResult
from rig_core.pack_index import PackIndex
from rig_core.lockfile import RigLock


class TestPackInstaller:
    """Test pack installer functionality."""

    def test_install_dry_run(self, tmp_path):
        """Test dry run installation."""
        # Create a mock index
        index_data = {
            "api_version": 1,
            "generated_at": "2026-01-13T00:00:00Z",
            "packs": {
                "echo": {
                    "display_name": "Echo",
                    "python": {"package": "rig-pack-echo", "min_rig": "0.1.0"},
                }
            },
        }

        # Save index to temp file
        index_file = tmp_path / "index.json"
        with open(index_file, "w") as f:
            json.dump(index_data, f)

        # Create installer with temp paths
        lock_path = tmp_path / "rig.lock"
        installer = PackInstaller(lock_path=lock_path)

        # Override index client to use local file
        installer.index_client.cache_file = index_file

        # Test dry run
        result = installer.install("echo", runtime="python", dry_run=True, index_url=f"file://{index_file}")

        assert result.success
        assert result.pack_id == "echo"
        assert result.package == "rig-pack-echo"
        assert "Dry run" in result.message

    def test_install_nonexistent_pack(self, tmp_path):
        """Test installing a pack that doesn't exist."""
        index_data = {"api_version": 1, "generated_at": "2026-01-13T00:00:00Z", "packs": {}}

        index_file = tmp_path / "index.json"
        with open(index_file, "w") as f:
            json.dump(index_data, f)

        lock_path = tmp_path / "rig.lock"
        installer = PackInstaller(lock_path=lock_path)
        installer.index_client.cache_file = index_file

        result = installer.install("nonexistent", runtime="python", dry_run=True, index_url=f"file://{index_file}")

        assert not result.success
        assert "not found" in result.error.lower()

    def test_uninstall_pack(self, tmp_path):
        """Test uninstalling a pack."""
        lock_path = tmp_path / "rig.lock"

        # Create a lockfile with a pack
        lock = RigLock()
        from rig_core.lockfile import LockedPack

        pack = LockedPack(pack_id="echo", package="rig-pack-echo", version="0.1.0", runtime="python")
        lock.add_pack(pack)
        lock.save(lock_path)

        # Uninstall
        installer = PackInstaller(lock_path=lock_path)
        result = installer.uninstall("echo", remove_package=False)

        assert result is True

        # Verify removed from lockfile
        lock = RigLock.load(lock_path)
        assert "echo" not in lock.packs

    def test_uninstall_nonexistent_pack(self, tmp_path):
        """Test uninstalling a pack that isn't installed."""
        lock_path = tmp_path / "rig.lock"
        lock = RigLock()
        lock.save(lock_path)

        installer = PackInstaller(lock_path=lock_path)
        result = installer.uninstall("nonexistent", remove_package=False)

        assert result is False

