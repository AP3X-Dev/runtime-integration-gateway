"""
Pack Index

Provides pack discovery and resolution from a central index.
The index maps short pack names (e.g., "notion") to actual package names
on PyPI and npm.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import httpx


@dataclass
class PackRuntime:
    """Package information for a specific runtime (Python or Node)."""

    package: str  # PyPI or npm package name
    min_rig: str = "0.1.0"  # Minimum RIG version required


@dataclass
class PackIndexEntry:
    """Entry in the pack index for a single pack."""

    display_name: str
    python: Optional[PackRuntime] = None
    node: Optional[PackRuntime] = None
    description: str = ""
    homepage: str = ""
    tags: list[str] = field(default_factory=list)


@dataclass
class PackIndex:
    """Pack index containing all available packs."""

    api_version: int
    generated_at: str
    packs: Dict[str, PackIndexEntry]

    @classmethod
    def from_dict(cls, data: dict) -> PackIndex:
        """Parse pack index from JSON dict."""
        packs = {}
        for pack_id, pack_data in data.get("packs", {}).items():
            python_data = pack_data.get("python")
            node_data = pack_data.get("node")

            packs[pack_id] = PackIndexEntry(
                display_name=pack_data.get("display_name", pack_id),
                python=PackRuntime(**python_data) if python_data else None,
                node=PackRuntime(**node_data) if node_data else None,
                description=pack_data.get("description", ""),
                homepage=pack_data.get("homepage", ""),
                tags=pack_data.get("tags", []),
            )

        return cls(
            api_version=data.get("api_version", 1),
            generated_at=data.get("generated_at", datetime.utcnow().isoformat()),
            packs=packs,
        )

    def get(self, pack_id: str) -> Optional[PackIndexEntry]:
        """Get pack entry by ID."""
        return self.packs.get(pack_id)

    def resolve_package(self, pack_id: str, runtime: str = "python") -> Optional[str]:
        """Resolve pack ID to package name for given runtime."""
        entry = self.get(pack_id)
        if not entry:
            return None

        if runtime == "python" and entry.python:
            return entry.python.package
        elif runtime == "node" and entry.node:
            return entry.node.package

        return None


DEFAULT_INDEX_URL = "https://raw.githubusercontent.com/AP3X-Dev/runtime-integration-gateway/master/specs/pack-index-example.json"


class PackIndexClient:
    """Client for fetching and caching pack index."""

    def __init__(self, cache_dir: Path | str = ".rig/cache", cache_ttl_seconds: int = 86400):
        """
        Initialize pack index client.

        Args:
            cache_dir: Directory to store cached index
            cache_ttl_seconds: Cache time-to-live in seconds (default: 24 hours)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_ttl = cache_ttl_seconds
        self.cache_file = self.cache_dir / "pack_index.json"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _is_cache_valid(self) -> bool:
        """Check if cached index is still valid."""
        if not self.cache_file.exists():
            return False

        age = time.time() - self.cache_file.stat().st_mtime
        return age < self.cache_ttl

    def _load_cache(self) -> Optional[PackIndex]:
        """Load index from cache."""
        if not self.cache_file.exists():
            return None

        try:
            with open(self.cache_file, "r") as f:
                data = json.load(f)
            return PackIndex.from_dict(data)
        except Exception:
            return None

    def _save_cache(self, data: dict) -> None:
        """Save index to cache."""
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def fetch(self, index_url: str = DEFAULT_INDEX_URL, force_refresh: bool = False) -> PackIndex:
        """
        Fetch pack index, using cache if valid.

        Args:
            index_url: URL to fetch index from
            force_refresh: Force refresh even if cache is valid

        Returns:
            PackIndex instance

        Raises:
            httpx.HTTPError: If fetch fails and no cache available
        """
        if not force_refresh and self._is_cache_valid():
            cached = self._load_cache()
            if cached:
                return cached

        # Fetch from remote
        response = httpx.get(index_url, timeout=10.0, follow_redirects=True)
        response.raise_for_status()
        data = response.json()

        # Save to cache
        self._save_cache(data)

        return PackIndex.from_dict(data)

