"""Held-out execution refusal gate for the prospective benchmark."""
from __future__ import annotations

from dataclasses import dataclass


class HeldOutAccessRefused(RuntimeError):
    """Raised before any held-out input can be loaded for evaluation."""


@dataclass(frozen=True)
class ImplementationLock:
    status: str
    implementation_commit: str
    strict_evaluator_version: str
    grammar_version: str
    engine_version: str

    @classmethod
    def pending(cls) -> "ImplementationLock":
        return cls("PENDING_LOCK", "PENDING_LOCK", "PENDING_LOCK", "PENDING_LOCK", "PENDING_LOCK")

    @classmethod
    def locked(cls, implementation_commit: str, strict_evaluator_version: str, grammar_version: str, engine_version: str) -> "ImplementationLock":
        return cls("LOCKED", implementation_commit, strict_evaluator_version, grammar_version, engine_version)


def assert_held_out_execution_allowed(lock: ImplementationLock, hashes: dict[str, str], preflight: dict[str, object], tree_clean: bool) -> None:
    """Check all refusal conditions before a caller may request held-out input."""
    if lock.status == "PENDING_LOCK" or "PENDING_LOCK" in lock.__dict__.values():
        raise HeldOutAccessRefused("implementation lock is PENDING_LOCK")
    if not all(lock.__dict__.values()):
        raise HeldOutAccessRefused("implementation lock is incomplete")
    if not hashes or any(not value for value in hashes.values()):
        raise HeldOutAccessRefused("hash verification is incomplete")
    if preflight.get("complete") is not True:
        raise HeldOutAccessRefused("development and engine preflight is incomplete")
    if not tree_clean:
        raise HeldOutAccessRefused("tracked tree is not clean")
