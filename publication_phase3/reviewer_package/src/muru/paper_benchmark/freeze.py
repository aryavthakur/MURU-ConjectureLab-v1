"""Content-freeze preparation status, distinct from final executable freeze."""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

from .artifacts import verify_hash_inventory
from .governance import ImplementationLock


@dataclass(frozen=True)
class FreezePreparation:
    status: str
    hashes_verified: bool
    final_executable_freeze: bool
    blocker: str
    preflight_sha256: str
    hash_inventory_sha256: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def prepare_content_freeze(artifact_dir: Path, lock: ImplementationLock, preflight: dict[str, object]) -> FreezePreparation:
    try:
        hashes_verified = bool(verify_hash_inventory(artifact_dir))
    except FileNotFoundError:
        hashes_verified = False
    preflight_path = artifact_dir / "paper_benchmark_preflight.json"
    inventory_path = artifact_dir / "paper_benchmark_hash_inventory.json"
    preflight_hash = hashlib.sha256(preflight_path.read_bytes()).hexdigest() if preflight_path.exists() else ""
    inventory_hash = hashlib.sha256(inventory_path.read_bytes()).hexdigest() if inventory_path.exists() else ""
    if lock.status == "PENDING_LOCK":
        return FreezePreparation("WAITING_FOR_LOCKED_IMPLEMENTATION", hashes_verified, False, "evaluated MURU implementation lock and complete engine runtime preflight are pending", preflight_hash, inventory_hash)
    if not hashes_verified or preflight.get("complete") is not True:
        return FreezePreparation("REQUIRES_REVISION_BEFORE_FREEZE", hashes_verified, False, "hash verification or runtime preflight is incomplete", preflight_hash, inventory_hash)
    return FreezePreparation("READY_FOR_ONE_SHOT_HELD_OUT_EXECUTION", True, True, "", preflight_hash, inventory_hash)
