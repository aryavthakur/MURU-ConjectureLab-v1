"""Content-freeze preparation status, distinct from final executable freeze."""
from __future__ import annotations

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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def prepare_content_freeze(artifact_dir: Path, lock: ImplementationLock, preflight: dict[str, object]) -> FreezePreparation:
    try:
        hashes_verified = bool(verify_hash_inventory(artifact_dir))
    except FileNotFoundError:
        hashes_verified = False
    if lock.status == "PENDING_LOCK":
        return FreezePreparation("WAITING_FOR_LOCKED_IMPLEMENTATION", hashes_verified, False, "evaluated MURU implementation lock and complete engine runtime preflight are pending")
    if not hashes_verified or preflight.get("complete") is not True:
        return FreezePreparation("REQUIRES_REVISION_BEFORE_FREEZE", hashes_verified, False, "hash verification or runtime preflight is incomplete")
    return FreezePreparation("READY_FOR_ONE_SHOT_HELD_OUT_EXECUTION", True, True, "")
