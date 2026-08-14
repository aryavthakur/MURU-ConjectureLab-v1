"""Engineering RC3: structural-null calibration runner.

BUILD ONLY.  Importing or constructing this runner executes nothing.  The
100 calibration worlds are executed only by an explicit, separately
authorized invocation of :func:`run_calibration`.

What this module owns
---------------------
* the search backend adapter (PySR under the frozen settings)
* per-seed status assignment from *actual execution outcome*
* the prefix-monotonicity canary
* resumable incremental per-seed persistence
* world aggregation, validity, and threshold construction, all delegated to
  the frozen ``calibration_contract`` functions

What this module does NOT own
-----------------------------
Every frozen number.  Allocation, seed derivation, aggregation rules,
validity floor, quantile method, bootstrap settings: all imported.

Failure semantics
-----------------
``np.isfinite`` never determines a status.  Status is assigned from what the
execution did:

``COMPLETED_WITH_CANDIDATES``
    the search ran to completion and returned at least one candidate
``COMPLETED_NO_CANDIDATE``
    the search ran to completion and returned none; contributes ``-inf``
``EXECUTION_FAILURE``
    any exception, crash, timeout, OOM, malformed result, contract
    execution failure, or prefix-monotonicity violation

A single ``EXECUTION_FAILURE`` seed forces its world's whole S(w,1..20) row
to +1.0, which is conservative: it can only raise a threshold.
"""
from __future__ import annotations

import hashlib
import json
import math
import signal
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping, Protocol, Sequence

import numpy as np

from .calibration_contract import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    CONSTRUCTION_ALLOCATION,
    MAX_COMPLEXITY,
    MIN_VALID_WORLDS,
    N_CALIBRATION_WORLDS,
    N_SEEDS_PER_WORLD,
    QUANTILE_LEVEL,
    SEARCH_SETTINGS,
    CalibrationValidity,
    SeedResult,
    SeedStatus,
    check_calibration_validity,
    compute_bootstrap_uncertainty,
    compute_threshold_table,
    compute_world_null_statistic,
    count_failed_worlds,
)
from .rc3_calibration_worlds import CalibrationWorld, build_world
from .rc3_provenance import a3_2_world_construction

__all__ = [
    "SearchOutcome",
    "SearchBackend",
    "PySRBackend",
    "PrefixMonotonicityViolation",
    "SeedTimeout",
    "check_prefix_monotonicity",
    "run_seed",
    "run_world",
    "run_calibration",
    "CalibrationRunResult",
    "SeedRecordStore",
    "ENGINEERING_SMOKE_MARKER",
    "FROZEN_SETTINGS_DIGEST",
    "search_settings_digest",
]


# -----------------------------------------------------------------------
# Search backend contract
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class SearchOutcome:
    """What a completed search returned.

    ``best_valid_r2_by_complexity`` maps complexity to the best validation R2
    achieved *at* that complexity.  A sparse map is normal: a Pareto front
    does not populate every complexity.

    An empty map means the search completed and produced no candidate.  A
    backend signals failure by *raising*, never by returning a sentinel.
    """

    best_valid_r2_by_complexity: Mapping[int, float]
    n_candidates: int


class SearchBackend(Protocol):
    """A search engine that can be run on one world at one seed."""

    def search(self, world: CalibrationWorld, seed: int) -> SearchOutcome: ...


# -----------------------------------------------------------------------
# Prefix-monotonicity canary
# -----------------------------------------------------------------------

class PrefixMonotonicityViolation(RuntimeError):
    """The complexity curve violated the frozen contract canary."""


def check_prefix_monotonicity(
    best_r2_by_complexity: Mapping[int, float],
) -> None:
    """Enforce the frozen contract canary on a raw per-complexity map.

    Runs *before* the frozen ``compute_seed_complexity_curve``, which repairs
    rather than reports.  RC3 must report.

    What is actually checked, stated precisely because the amendment's
    phrasing invites a vacuous reading:

    1. Every complexity key is an integer in 1..20.  A key outside that range
       is malformed engine output, not something to skip silently.
    2. Every present value is either finite or ``-inf``.  ``NaN`` and ``+inf``
       are malformed engine output.
    3. The resulting cumulative-max curve is non-decreasing.

    The amendment's canary - "once finite at c, cannot become non-finite at
    larger c" - is a *tautology* on the cumulative-max curve, since a running
    maximum that has become finite can never return to ``-inf``.  It is
    therefore not implemented as a separate branch: doing so would be dead
    code masquerading as a safety check.  Applying it instead to the raw
    per-complexity map would be wrong in the other direction - a sparse
    Pareto front legitimately has a candidate at complexity 8 that scores
    ``-inf`` on validation after a finite score at complexity 6.  Conditions
    1-3 are what remains with real content.

    Raises
    ------
    PrefixMonotonicityViolation
        The caller maps this to ``EXECUTION_FAILURE`` for that seed.
    """
    for complexity, value in sorted(best_r2_by_complexity.items()):
        if not isinstance(complexity, (int, np.integer)):
            raise PrefixMonotonicityViolation(
                f"complexity key {complexity!r} is not an integer"
            )
        if complexity < 1 or complexity > MAX_COMPLEXITY:
            raise PrefixMonotonicityViolation(
                f"complexity {complexity} outside 1..{MAX_COMPLEXITY}"
            )
        value = float(value)
        if math.isnan(value):
            raise PrefixMonotonicityViolation(
                f"NaN validation R2 at complexity {complexity}"
            )
        if math.isinf(value) and value > 0:
            raise PrefixMonotonicityViolation(
                f"+inf validation R2 at complexity {complexity}"
            )

    running = float("-inf")
    for complexity in range(1, MAX_COMPLEXITY + 1):
        value = float(best_r2_by_complexity.get(complexity, float("-inf")))
        nxt = max(running, value)
        if nxt < running:  # pragma: no cover - cumulative max cannot decrease
            raise PrefixMonotonicityViolation(
                f"cumulative curve decreased at complexity {complexity}"
            )
        running = nxt


# -----------------------------------------------------------------------
# Per-seed execution
# -----------------------------------------------------------------------

class SeedTimeout(RuntimeError):
    """A seed exceeded its wall-clock budget."""


@contextmanager
def _wall_clock_budget(seconds: float | None):
    """Raise :class:`SeedTimeout` if the body outlives ``seconds``.

    Implemented with ``SIGALRM``, so it fires only when control is inside the
    Python interpreter.  A Julia call that blocks without yielding cannot be
    interrupted from here; the alarm lands as soon as PySR returns to Python.
    This bounds a stuck *seed loop*, not a wedged Julia worker, and it is
    only armed on the main thread of a POSIX host.  ``seconds=None``
    disables it.
    """
    if seconds is None or not hasattr(signal, "SIGALRM"):
        yield
        return
    if threading.current_thread() is not threading.main_thread():
        yield
        return

    def _fire(signum, frame):  # pragma: no cover - timing dependent
        raise SeedTimeout(f"seed exceeded {seconds}s wall-clock budget")

    previous = signal.signal(signal.SIGALRM, _fire)
    signal.setitimer(signal.ITIMER_REAL, float(seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0.0)
        signal.signal(signal.SIGALRM, previous)


def run_seed(
    world: CalibrationWorld,
    seed: int,
    backend: SearchBackend,
    timeout_seconds: float | None = None,
) -> SeedResult:
    """Execute one search seed and assign its status.

    The status comes from what happened, not from what the numbers look
    like.  Crashes, ``MemoryError`` (an OOM), :class:`SeedTimeout`, malformed
    results and contract violations all become ``EXECUTION_FAILURE``.

    ``KeyboardInterrupt`` and ``SystemExit`` are deliberately NOT caught.  An
    operator pressing Ctrl-C is aborting the run, not observing a failed
    seed; recording it as ``EXECUTION_FAILURE`` would durably poison that
    world's whole S(w,1..20) row to +1.0, and the no-retry rule would make
    that unrecoverable.  The interrupt propagates with no record written, so
    the seed is simply not yet done and a resumed run re-executes it.
    """
    try:
        with _wall_clock_budget(timeout_seconds):
            outcome = backend.search(world, seed)
    except (KeyboardInterrupt, SystemExit):
        raise
    except BaseException as exc:  # noqa: BLE001 - OOM and timeouts must land here
        return SeedResult(
            seed=seed,
            status=SeedStatus.EXECUTION_FAILURE,
            best_valid_r2_by_complexity=None,
            error_message=f"{type(exc).__name__}: {exc}".strip()[:2000],
        )

    if not isinstance(outcome, SearchOutcome):
        return SeedResult(
            seed=seed,
            status=SeedStatus.EXECUTION_FAILURE,
            best_valid_r2_by_complexity=None,
            error_message=(
                f"malformed backend result: {type(outcome).__name__}"
            ),
        )

    curve = dict(outcome.best_valid_r2_by_complexity)

    try:
        check_prefix_monotonicity(curve)
    except PrefixMonotonicityViolation as exc:
        return SeedResult(
            seed=seed,
            status=SeedStatus.EXECUTION_FAILURE,
            best_valid_r2_by_complexity=None,
            error_message=f"PrefixMonotonicityViolation: {exc}",
        )

    # Completed.  Candidate presence is an execution fact reported by the
    # backend, not an inference from finiteness.
    if outcome.n_candidates <= 0:
        return SeedResult(
            seed=seed,
            status=SeedStatus.COMPLETED_NO_CANDIDATE,
            best_valid_r2_by_complexity=None,
        )

    return SeedResult(
        seed=seed,
        status=SeedStatus.COMPLETED_WITH_CANDIDATES,
        best_valid_r2_by_complexity={int(k): float(v) for k, v in curve.items()},
    )


# -----------------------------------------------------------------------
# Incremental, resumable persistence
# -----------------------------------------------------------------------

def _sanitize(world_id: str) -> str:
    return world_id.replace("|", "__")


def search_settings_digest(settings: Mapping[str, object]) -> str:
    """SHA-256 over a canonical rendering of the effective search settings.

    Stamped into every seed record so a record produced under reduced
    ``niterations`` can never be mistaken for one produced under the frozen
    settings.  Deleting the smoke marker is not enough to launder a record:
    the digest still says what actually ran.
    """
    canonical = json.dumps(
        {str(k): settings[k] for k in sorted(settings)},
        sort_keys=True, separators=(",", ":"), default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


#: The digest of the frozen settings, computed once.  A record whose digest
#: differs from this did not run under the frozen search configuration.
FROZEN_SETTINGS_DIGEST = search_settings_digest(SEARCH_SETTINGS)


def _seed_record_payload(
    world_id: str, result: SeedResult, settings_digest: str
) -> dict:
    curve = result.best_valid_r2_by_complexity
    return {
        "world_id": world_id,
        "seed": int(result.seed),
        "status": result.status.value,
        "best_valid_r2_by_complexity": (
            None if curve is None
            else {str(k): _json_float(v) for k, v in sorted(curve.items())}
        ),
        "error_message": result.error_message,
        "search_settings_digest": settings_digest,
    }


def _json_float(value: float) -> object:
    value = float(value)
    if math.isnan(value):
        return "NaN"
    if math.isinf(value):
        return "Infinity" if value > 0 else "-Infinity"
    return value


def _parse_float(value: object) -> float:
    if isinstance(value, str):
        return {"NaN": math.nan, "Infinity": math.inf, "-Infinity": -math.inf}[value]
    return float(value)


#: Stamped into every record of a quarantined store, and checked by
#: :func:`run_calibration` so engineering output can never reach the
#: threshold computation path.
ENGINEERING_SMOKE_MARKER = "ENGINEERING_SMOKE_NOT_SCIENTIFIC"


class SeedRecordStore:
    """Append-only per-seed record store, one JSONL file per world.

    A record is written the moment its seed finishes, so an interrupted run
    resumes without re-executing any completed seed.  Records are never
    rewritten or deleted: a resumed run appends only.

    ``quarantined=True`` marks the store as engineering-smoke output.  Every
    record then carries the smoke marker, and :func:`run_calibration`
    refuses such a store outright.

    Append-only is a durability property, not a permission to revise.  A
    second record for a seed already present is rejected on load: otherwise
    appending one line would silently convert a recorded
    ``EXECUTION_FAILURE`` into a clean status, un-poisoning that world's
    ``+1.0`` row and lowering the Q95 threshold - precisely the selective
    retry the amendment forbids.
    """

    def __init__(
        self,
        root: Path,
        quarantined: bool = False,
        settings_digest: str = FROZEN_SETTINGS_DIGEST,
    ):
        self.root = Path(root)
        self.quarantined = bool(quarantined)
        self.settings_digest = settings_digest
        self.root.mkdir(parents=True, exist_ok=True)

    def path_for(self, world_id: str) -> Path:
        return self.root / f"{_sanitize(world_id)}.jsonl"

    def append(self, world_id: str, result: SeedResult) -> None:
        payload = _seed_record_payload(world_id, result, self.settings_digest)
        if self.quarantined:
            payload["marker"] = ENGINEERING_SMOKE_MARKER
        line = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        with self.path_for(world_id).open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()

    def load(self, world_id: str) -> dict[int, SeedResult]:
        """Load completed seeds for a world.

        A truncated final line (an interrupted write) is discarded, so a
        half-written record can never be mistaken for a completed seed.

        Everything else is verified rather than trusted: the smoke marker,
        the record's own ``world_id``, its search-settings digest, and
        first-write-wins on the seed.  Any mismatch raises; none is repaired.
        """
        path = self.path_for(world_id)
        if not path.exists():
            return {}
        results: dict[int, SeedResult] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue  # truncated tail
            if payload.get("marker") == ENGINEERING_SMOKE_MARKER and not self.quarantined:
                raise RuntimeError(
                    f"{path} contains engineering-smoke records; a scientific "
                    f"store must never read them"
                )
            recorded_world = payload.get("world_id")
            if recorded_world != world_id:
                raise RuntimeError(
                    f"{path} contains a record for {recorded_world!r} but was "
                    f"read as {world_id!r}; a renamed or copied record file "
                    f"must not be adopted as another world's completed seeds"
                )
            recorded_digest = payload.get("search_settings_digest")
            if recorded_digest != self.settings_digest:
                raise RuntimeError(
                    f"{path} seed {payload.get('seed')} was produced under "
                    f"search settings {recorded_digest} but this store expects "
                    f"{self.settings_digest}; a record produced under different "
                    f"settings must not be adopted"
                )
            seed = int(payload["seed"])
            if seed in results:
                raise RuntimeError(
                    f"{path} contains a duplicate record for seed {seed}; "
                    f"records are append-only and a seed is decided once - "
                    f"a second record would be a selective retry"
                )
            curve = payload.get("best_valid_r2_by_complexity")
            results[seed] = SeedResult(
                seed=seed,
                status=SeedStatus(payload["status"]),
                best_valid_r2_by_complexity=(
                    None if curve is None
                    else {int(k): _parse_float(v) for k, v in curve.items()}
                ),
                error_message=payload.get("error_message", ""),
            )
        return results


# -----------------------------------------------------------------------
# World execution
# -----------------------------------------------------------------------

def run_world(
    world: CalibrationWorld,
    backend: SearchBackend,
    store: SeedRecordStore,
    seeds: Sequence[int] | None = None,
    on_seed: Callable[[str, SeedResult], None] | None = None,
    timeout_seconds: float | None = None,
) -> list[SeedResult]:
    """Execute one world's seeds, resuming from any already-recorded seeds.

    No selective retry: a seed already recorded as ``EXECUTION_FAILURE`` is
    *not* re-run.  It stays failed and its world stays failed.
    """
    seeds = list(world.seeds if seeds is None else seeds)
    completed = store.load(world.world_id)

    results: list[SeedResult] = []
    for seed in seeds:
        if seed in completed:
            results.append(completed[seed])
            continue
        result = run_seed(world, seed, backend, timeout_seconds=timeout_seconds)
        store.append(world.world_id, result)
        if on_seed is not None:
            on_seed(world.world_id, result)
        results.append(result)
    return results


# -----------------------------------------------------------------------
# Full calibration
# -----------------------------------------------------------------------

@dataclass(frozen=True)
class CalibrationRunResult:
    """The outcome of a full calibration execution."""

    validity: CalibrationValidity
    failed_worlds: int
    clean_worlds: int
    world_statistics: Mapping[str, dict[int, float]]
    thresholds: Mapping[int, float] | None
    bootstrap: Mapping[int, tuple[float, float]] | None
    search_settings: Mapping[str, object] = field(
        default_factory=lambda: dict(SEARCH_SETTINGS)
    )
    #: A3.2 world-construction identity: which base target and which split
    #: produced these worlds.  A threshold table must never be readable
    #: without it.
    world_construction: Mapping[str, object] = field(
        default_factory=lambda: dict(a3_2_world_construction())
    )

    def threshold_table_active(self) -> bool:
        return self.validity == CalibrationValidity.VALID and self.thresholds is not None


def run_calibration(
    backend: SearchBackend,
    store: SeedRecordStore,
    world_specs: Sequence[tuple[str, int]] | None = None,
    compute_bootstrap: bool = True,
    on_seed: Callable[[str, SeedResult], None] | None = None,
    timeout_seconds: float | None = None,
) -> CalibrationRunResult:
    """Execute the calibration and build the threshold table.

    This is the only entry point that runs searches.  Calling it with the
    default ``world_specs`` executes all 100 worlds x 30 seeds and is the
    authorized-execution path, not an engineering path.

    Aggregation, validity and threshold construction are delegated
    unchanged to the frozen contract functions.
    """
    if store.quarantined:
        raise RuntimeError(
            "refusing to compute thresholds from a quarantined "
            f"({ENGINEERING_SMOKE_MARKER}) record store"
        )

    # Determined from what the backend will actually do, not from a settable
    # flag: clearing ``engineering_smoke`` on a reduced-niterations backend
    # must not buy a pass.
    effective = getattr(backend, "effective_settings", None)
    if effective is not None:
        digest = search_settings_digest(effective)
        if digest != FROZEN_SETTINGS_DIGEST:
            raise RuntimeError(
                "refusing to run calibration under non-frozen search settings "
                f"(digest {digest}, frozen {FROZEN_SETTINGS_DIGEST}); the "
                "frozen search settings must not be overridden"
            )
    if store.settings_digest != FROZEN_SETTINGS_DIGEST:
        raise RuntimeError(
            "refusing to compute thresholds from a store bound to non-frozen "
            f"search settings ({store.settings_digest})"
        )

    if world_specs is None:
        world_specs = [
            (construction, index)
            for construction, count in CONSTRUCTION_ALLOCATION.items()
            for index in range(count)
        ]
    _check_allocation(world_specs)

    world_results: dict[str, list[SeedResult]] = {}
    world_statistics: dict[str, dict[int, float]] = {}

    for construction, index in world_specs:
        world = build_world(construction, index)
        results = run_world(
            world, backend, store, on_seed=on_seed, timeout_seconds=timeout_seconds
        )
        world_results[world.world_id] = results
        # Frozen aggregation: any EXECUTION_FAILURE seed -> whole row +1.0
        world_statistics[world.world_id] = compute_world_null_statistic(results)

    failed = count_failed_worlds(world_results)
    validity = check_calibration_validity(world_results)

    thresholds = None
    bootstrap = None
    if validity == CalibrationValidity.VALID:
        thresholds = compute_threshold_table(world_statistics)
        _assert_threshold_table_defined(thresholds, world_statistics)
        if compute_bootstrap:
            bootstrap = compute_bootstrap_uncertainty(world_statistics)

    return CalibrationRunResult(
        validity=validity,
        failed_worlds=failed,
        clean_worlds=len(world_results) - failed,
        world_statistics=world_statistics,
        thresholds=thresholds,
        bootstrap=bootstrap,
        search_settings=dict(effective) if effective is not None else dict(SEARCH_SETTINGS),
    )


def _check_allocation(world_specs: Sequence[tuple[str, int]]) -> None:
    """Refuse any world set that is not the frozen 34/33/33 allocation.

    A partial or lopsided set would still satisfy ``check_calibration_validity``
    at 100 entries, so without this a threshold table could be built from 100
    worlds of a single null construction and would report itself VALID.
    """
    if not world_specs:
        return  # an explicitly empty run computes nothing
    counts: dict[str, int] = {}
    for construction, index in world_specs:
        counts[construction] = counts.get(construction, 0) + 1
    if counts != dict(CONSTRUCTION_ALLOCATION):
        raise RuntimeError(
            f"world allocation {counts} does not match the frozen allocation "
            f"{dict(CONSTRUCTION_ALLOCATION)}"
        )
    seen = set(world_specs)
    if len(seen) != len(world_specs):
        raise RuntimeError("world_specs contains duplicate (construction, index) pairs")


def _assert_threshold_table_defined(
    thresholds: Mapping[int, float],
    world_statistics: Mapping[str, dict[int, float]],
) -> None:
    """Refuse a threshold table containing an undefined entry.

    ``np.quantile(..., method="linear")`` interpolates ``a + 0.05*(b - a)``.
    When the 95th order statistic is ``-inf`` and the 96th is finite, that is
    ``-inf + inf``, which is **NaN** - and ``np.maximum.accumulate`` then
    propagates the NaN across every complexity.  The run would still report
    VALID with a full table, while every downstream ``valid_r2 > threshold``
    comparison silently returned False.

    This is reachable in normal operation: ``COMPLETED_NO_CANDIDATE``
    legitimately contributes ``-inf``, and a Pareto front often has nothing at
    complexity 1 or 2, so ``S(w,1) = -inf`` for most worlds.  It is an
    engineering guard, not a science rule: it refuses to hand back a table
    that is not a number, rather than deciding what the number should be.
    """
    undefined = sorted(
        c for c, value in thresholds.items() if not math.isfinite(value)
    )
    if not undefined:
        return
    detail = {
        c: sum(
            1 for stat in world_statistics.values()
            if not math.isfinite(stat[c])
        )
        for c in undefined
    }
    raise RuntimeError(
        f"threshold table is undefined at complexities {undefined} "
        f"(non-finite world statistics per complexity: {detail}). "
        f"A NaN or infinite threshold must never be activated: every "
        f"downstream comparison against it would silently be False. "
        f"Resolve how the null statistic is defined at these complexities "
        f"before any threshold table is used."
    )


# -----------------------------------------------------------------------
# PySR backend, under the frozen search settings
# -----------------------------------------------------------------------

def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    if ss_tot == 0.0:
        return float("-inf")
    return 1.0 - float(np.sum((y_true - y_pred) ** 2)) / ss_tot


class PySRBackend:
    """PySR under the frozen A3.1 search settings.

    Every setting is read from ``SEARCH_SETTINGS``; none is written here.
    ``niterations_override`` exists solely for the quarantined engineering
    smoke and is refused unless the caller marks the run as non-scientific.
    """

    def __init__(
        self,
        niterations_override: int | None = None,
        engineering_smoke: bool = False,
        work_dir: Path | None = None,
    ):
        if niterations_override is not None and not engineering_smoke:
            raise ValueError(
                "niterations may only be overridden for the quarantined "
                "engineering smoke (engineering_smoke=True)"
            )
        self.engineering_smoke = engineering_smoke
        self.niterations = (
            int(niterations_override)
            if niterations_override is not None
            else int(SEARCH_SETTINGS["niterations"])
        )
        self.work_dir = work_dir

    @property
    def effective_settings(self) -> dict[str, object]:
        """What this backend will actually run.

        ``run_calibration`` digests this rather than trusting the
        ``engineering_smoke`` flag, which is an ordinary mutable attribute
        and so buys nothing on its own.
        """
        return {**SEARCH_SETTINGS, "niterations": self.niterations}

    def _make_regressor(self, seed: int):
        from pysr import PySRRegressor

        excluded = set(SEARCH_SETTINGS["excluded_unary"])
        unary = list(SEARCH_SETTINGS["unary_operators"])
        overlap = excluded.intersection(unary)
        if overlap:  # pragma: no cover - frozen settings exclude these
            raise RuntimeError(f"excluded operators present in grammar: {overlap}")

        kwargs = dict(
            binary_operators=list(SEARCH_SETTINGS["binary_operators"]),
            unary_operators=unary,
            maxsize=int(SEARCH_SETTINGS["maxsize"]),
            niterations=self.niterations,
            populations=int(SEARCH_SETTINGS["populations"]),
            population_size=int(SEARCH_SETTINGS["population_size"]),
            parsimony=float(SEARCH_SETTINGS["parsimony"]),
            adaptive_parsimony_scaling=float(
                SEARCH_SETTINGS["adaptive_parsimony_scaling"]
            ),
            deterministic=bool(SEARCH_SETTINGS["deterministic"]),
            parallelism="serial",
            random_state=int(seed),
            progress=False,
            verbosity=0,
            temp_equation_file=True,
        )
        if self.work_dir is not None:
            kwargs["tempdir"] = str(self.work_dir)
        return PySRRegressor(**kwargs)

    def search(self, world: CalibrationWorld, seed: int) -> SearchOutcome:
        masks = world.split_masks()
        design = world.design_matrix()
        target = world.target

        train = masks["train"]
        validation = masks["validation"]
        if not train.any() or not validation.any():
            raise RuntimeError("world has an empty train or validation partition")

        model = self._make_regressor(seed)
        model.fit(design[train], target[train])

        equations = getattr(model, "equations_", None)
        if equations is None or len(equations) == 0:
            return SearchOutcome(best_valid_r2_by_complexity={}, n_candidates=0)

        scores_by_complexity: dict[int, list[float]] = {}
        for row in range(len(equations)):
            complexity = int(equations["complexity"].iloc[row])
            # Out-of-range complexity is malformed engine output, not
            # something to skip.  It is passed through so the canary reports
            # it; silently dropping it would sanitize away the very condition
            # check_prefix_monotonicity exists to catch.
            if complexity < 1 or complexity > MAX_COMPLEXITY:
                scores_by_complexity.setdefault(complexity, []).append(float("nan"))
                continue

            predictions = np.asarray(
                model.predict(design[validation], index=row), dtype=np.float64
            )
            if not np.all(np.isfinite(predictions)):
                # The equation does not evaluate on the validation rows (a
                # divergent log or inv, say).  That is a real modelling
                # outcome, not an engine failure: it explains nothing on
                # validation, so it scores -inf.  Recorded explicitly, rather
                # than arriving as a swallowed NaN.
                scores_by_complexity.setdefault(complexity, []).append(float("-inf"))
                continue

            # Passed through unscrubbed: a NaN or +inf arising from a finite
            # prediction vector is malformed and must reach the canary
            # rather than be laundered into -inf.
            scores_by_complexity.setdefault(complexity, []).append(
                _r2(target[validation], predictions)
            )

        curve: dict[int, float] = {}
        for complexity, scores in scores_by_complexity.items():
            # A malformed score anywhere at this complexity dominates: it must
            # survive to the canary, and max() would hide it.
            malformed = [s for s in scores if math.isnan(s) or s == float("inf")]
            curve[complexity] = malformed[0] if malformed else max(scores)

        return SearchOutcome(
            best_valid_r2_by_complexity=curve,
            n_candidates=int(len(equations)),
        )
