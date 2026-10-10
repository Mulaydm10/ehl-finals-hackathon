"""Load tacto/starter-kit/.env and give an ArenaClient (read-only use from analysis scripts)."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "tacto" / "starter-kit"
sys.path.insert(0, str(KIT))

for line in (KIT / ".env").read_text().splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

from arena_kit import ArenaClient  # noqa: E402


def client():
    return ArenaClient()
