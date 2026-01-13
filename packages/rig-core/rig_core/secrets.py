from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class SecretsStore:
    """Secrets resolver.

    v0: environment variables only.
    Future: file based encrypted store, Vault, KMS, etc.
    """

    def resolve(self, slots: List[str], tenant_id: Optional[str] = None) -> Dict[str, str]:
        out: Dict[str, str] = {}
        for s in slots:
            v = os.environ.get(s)
            if v:
                out[s] = v
        return out
