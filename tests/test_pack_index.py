"""
Tests for pack index and lockfile functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from rig_core.pack_index import PackIndex, PackIndexClient, PackIndexEntry, PackRuntime
from rig_core.lockfile import RigLock, LockedPack, compute_package_hash


class TestPackIndex:
    """Test pack index parsing and resolution."""

    def test_parse_minimal_index(self):
        """Test parsing a minimal pack index."""
        data = {
            "api_version": 1,
            "generated_at": "2026-01-13T00:00:00Z",
            "packs": {
                "echo": {
                    "display_name": "Echo",
                    "python": {"package": "rig-pack-echo", "min_rig": "0.1.0"},
                }
            },
        }

        index = PackIndex.from_dict(data)
        assert index.api_version == 1
        assert "echo" in index.packs
        assert index.packs["echo"].display_name == "Echo"
        assert index.packs["echo"].python is not None
        assert index.packs["echo"].python.package == "rig-pack-echo"

    def test_parse_full_index(self):
        """Test parsing a full pack index with all fields."""
        data = {
            "api_version": 1,
            "generated_at": "2026-01-13T00:00:00Z",
            "packs": {
                "notion": {
                    "display_name": "Notion",
                    "description": "Notion integration",
                    "homepage": "https://notion.so",
                    "tags": ["productivity"],
                    "python": {"package": "rig-pack-notion", "min_rig": "0.1.0"},
                    "node": {"package": "@rig/pack-notion", "min_rig": "0.1.0"},
                }
            },
        }

        index = PackIndex.from_dict(data)
        notion = index.get("notion")
        assert notion is not None
        assert notion.display_name == "Notion"
        assert notion.description == "Notion integration"
        assert notion.homepage == "https://notion.so"
        assert "productivity" in notion.tags
        assert notion.python is not None
        assert notion.node is not None

    def test_resolve_package_python(self):
        """Test resolving pack ID to Python package name."""
        data = {
            "api_version": 1,
            "generated_at": "2026-01-13T00:00:00Z",
            "packs": {
                "stripe": {
                    "display_name": "Stripe",
                    "python": {"package": "rig-pack-stripe", "min_rig": "0.1.0"},
                }
            },
        }

        index = PackIndex.from_dict(data)
        package = index.resolve_package("stripe", "python")
        assert package == "rig-pack-stripe"

    def test_resolve_package_node(self):
        """Test resolving pack ID to Node package name."""
        data = {
            "api_version": 1,
            "generated_at": "2026-01-13T00:00:00Z",
            "packs": {
                "slack": {
                    "display_name": "Slack",
                    "node": {"package": "@rig/pack-slack", "min_rig": "0.1.0"},
                }
            },
        }

        index = PackIndex.from_dict(data)
        package = index.resolve_package("slack", "node")
        assert package == "@rig/pack-slack"

    def test_resolve_nonexistent_pack(self):
        """Test resolving a pack that doesn't exist."""
        data = {"api_version": 1, "generated_at": "2026-01-13T00:00:00Z", "packs": {}}

        index = PackIndex.from_dict(data)
        package = index.resolve_package("nonexistent", "python")
        assert package is None


class TestPackIndexClient:
    """Test pack index client with caching."""

    def test_cache_directory_creation(self, tmp_path):
        """Test that cache directory is created."""
        cache_dir = tmp_path / "cache"
        client = PackIndexClient(cache_dir=cache_dir)
        assert cache_dir.exists()

    def test_cache_save_and_load(self, tmp_path):
        """Test saving and loading from cache."""
        cache_dir = tmp_path / "cache"
        client = PackIndexClient(cache_dir=cache_dir)

        data = {
            "api_version": 1,
            "generated_at": "2026-01-13T00:00:00Z",
            "packs": {"echo": {"display_name": "Echo", "python": {"package": "rig-pack-echo"}}},
        }

        client._save_cache(data)
        assert client.cache_file.exists()

        loaded = client._load_cache()
        assert loaded is not None
        assert "echo" in loaded.packs

    def test_cache_validity(self, tmp_path):
        """Test cache validity checking."""
        cache_dir = tmp_path / "cache"
        client = PackIndexClient(cache_dir=cache_dir, cache_ttl_seconds=1)

        # No cache yet
        assert not client._is_cache_valid()

        # Create cache
        data = {"api_version": 1, "generated_at": "2026-01-13T00:00:00Z", "packs": {}}
        client._save_cache(data)

        # Should be valid
        assert client._is_cache_valid()


class TestRigLock:
    """Test lockfile functionality."""

    def test_create_empty_lock(self):
        """Test creating an empty lockfile."""
        lock = RigLock()
        assert lock.version == 1
        assert len(lock.packs) == 0

    def test_add_pack_to_lock(self):
        """Test adding a pack to lockfile."""
        lock = RigLock()
        pack = LockedPack(
            pack_id="echo", package="rig-pack-echo", version="0.1.0", runtime="python", integrity="abc123"
        )

        lock.add_pack(pack)
        assert "echo" in lock.packs
        assert lock.packs["echo"].version == "0.1.0"

    def test_remove_pack_from_lock(self):
        """Test removing a pack from lockfile."""
        lock = RigLock()
        pack = LockedPack(pack_id="echo", package="rig-pack-echo", version="0.1.0", runtime="python")

        lock.add_pack(pack)
        assert "echo" in lock.packs

        lock.remove_pack("echo")
        assert "echo" not in lock.packs

    def test_save_and_load_lock(self, tmp_path):
        """Test saving and loading lockfile."""
        lock_path = tmp_path / "rig.lock"
        lock = RigLock(rig_version="0.1.0", index_url="https://example.com/index.json")

        pack = LockedPack(pack_id="notion", package="rig-pack-notion", version="1.0.0", runtime="python")
        lock.add_pack(pack)

        lock.save(lock_path)
        assert lock_path.exists()

        loaded = RigLock.load(lock_path)
        assert loaded.rig_version == "0.1.0"
        assert "notion" in loaded.packs
        assert loaded.packs["notion"].version == "1.0.0"

    def test_load_nonexistent_lock(self, tmp_path):
        """Test loading a lockfile that doesn't exist."""
        lock_path = tmp_path / "nonexistent.lock"
        lock = RigLock.load(lock_path)
        assert len(lock.packs) == 0


class TestPackageHash:
    """Test package integrity hashing."""

    def test_compute_hash(self):
        """Test computing package hash."""
        hash1 = compute_package_hash("rig-pack-echo", "0.1.0")
        hash2 = compute_package_hash("rig-pack-echo", "0.1.0")
        hash3 = compute_package_hash("rig-pack-echo", "0.2.0")

        assert hash1 is not None
        assert hash1 == hash2  # Same package/version = same hash
        assert hash1 != hash3  # Different version = different hash

