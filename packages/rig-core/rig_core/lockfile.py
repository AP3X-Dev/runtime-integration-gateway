"""
RIG Lockfile

Provides reproducible pack installations by recording exact versions
and integrity hashes.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


@dataclass
class LockedPack:
    """A locked pack entry with exact version information."""

    pack_id: str  # Short name from index (e.g., "notion")
    package: str  # Actual package name (e.g., "rig-pack-notion")
    version: str  # Installed version
    runtime: str  # "python" or "node"
    integrity: Optional[str] = None  # SHA256 hash if available
    installed_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class RigLock:
    """RIG lockfile containing all locked packs."""

    version: int = 1  # Lockfile format version
    rig_version: str = "0.1.0"  # RIG version used to create lock
    index_url: str = ""  # Pack index URL used
    index_generated_at: str = ""  # Index timestamp
    packs: Dict[str, LockedPack] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add_pack(self, locked_pack: LockedPack) -> None:
        """Add or update a locked pack."""
        self.packs[locked_pack.pack_id] = locked_pack
        self.updated_at = datetime.utcnow().isoformat()

    def remove_pack(self, pack_id: str) -> None:
        """Remove a locked pack."""
        if pack_id in self.packs:
            del self.packs[pack_id]
            self.updated_at = datetime.utcnow().isoformat()

    def get_pack(self, pack_id: str) -> Optional[LockedPack]:
        """Get a locked pack by ID."""
        return self.packs.get(pack_id)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "rig_version": self.rig_version,
            "index_url": self.index_url,
            "index_generated_at": self.index_generated_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "packs": {
                pack_id: {
                    "pack_id": pack.pack_id,
                    "package": pack.package,
                    "version": pack.version,
                    "runtime": pack.runtime,
                    "integrity": pack.integrity,
                    "installed_at": pack.installed_at,
                }
                for pack_id, pack in self.packs.items()
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> RigLock:
        """Parse lockfile from dictionary."""
        packs = {}
        for pack_id, pack_data in data.get("packs", {}).items():
            packs[pack_id] = LockedPack(
                pack_id=pack_data["pack_id"],
                package=pack_data["package"],
                version=pack_data["version"],
                runtime=pack_data["runtime"],
                integrity=pack_data.get("integrity"),
                installed_at=pack_data.get("installed_at", ""),
            )

        return cls(
            version=data.get("version", 1),
            rig_version=data.get("rig_version", "0.1.0"),
            index_url=data.get("index_url", ""),
            index_generated_at=data.get("index_generated_at", ""),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            packs=packs,
        )

    def save(self, path: Path | str) -> None:
        """Save lockfile to disk."""
        path = Path(path)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path | str) -> RigLock:
        """Load lockfile from disk."""
        path = Path(path)
        if not path.exists():
            return cls()

        with open(path, "r") as f:
            data = json.load(f)

        return cls.from_dict(data)


def compute_package_hash(package_name: str, version: str) -> Optional[str]:
    """
    Compute integrity hash for a package.

    For v0, this is a placeholder. In production, this would:
    - For Python: fetch from PyPI JSON API and hash the wheel/sdist
    - For Node: use npm's integrity field from package-lock.json

    Args:
        package_name: Package name
        version: Package version

    Returns:
        SHA256 hash or None if unavailable
    """
    # Placeholder implementation
    # In production, fetch actual package and compute hash
    content = f"{package_name}@{version}".encode()
    return hashlib.sha256(content).hexdigest()

