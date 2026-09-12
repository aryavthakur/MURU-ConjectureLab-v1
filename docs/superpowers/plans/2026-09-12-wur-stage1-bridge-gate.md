# WUR Stage 0 close-out, preregistration freeze, and Stage 1 bridge gate

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close the two Stage 0 review items (rule D6 and environment provenance), freeze `MURU_WUR_REAL_DATA_PREREGISTRATION.md`, and execute the Stage 1 cross-instrument bridge gate exactly once, writing `artifacts/wur_bridge_gate.json`.

**Architecture:** Stage 0 gains a post-hoc `apply_d6` filter over the D1-D5 partition result plus a shared `environment_provenance()` helper, neither of which re-runs the partition. Stage 1 factors the per-spectrum acceptance gates out of `build_qualifying_trajectories` into a reusable `accepted_rows()` table, reads peak blobs against that exact lineage, computes base-cell `features.mu`, and applies a rule frozen in the preregistration before any real delta exists.

**Tech Stack:** Python 3.13, pandas 3.0.5, numpy 2.5.2, scipy 1.18.0, rdkit 2026.03.5, pyarrow 25.0.1, pytest.

**Spec:** `docs/superpowers/specs/2026-09-11-wur-real-data-program-design.md` (sections 5 and 8)

## Global Constraints

- Execution order is strict and non-negotiable: Tasks 1-4 (Stage 0 close-out) must be committed before Task 5 (preregistration) is committed, and the preregistration commit must exist before any Stage 1 `mu` is computed (Tasks 6-10). The single real gate run is Task 11.
- No real WUR peak data (`blobMass` / `blobIntensity`) may be read until the preregistration commit exists. Tasks 6-10 use synthetic fixtures and in-test SQLite databases only.
- Thresholds do not move after real deltas are seen. `MEDIAN_ABS_DELTA_MAX = 0.05`, `SPEARMAN_MIN = 0.80`, `MIN_PASSING_ENERGIES = 5`, `OFFSET_MAX = 0.15` are frozen constants.
- `SEED = 20260911` everywhere a seed is needed.
- The LCSB sealed confirmation set is never opened. `artifacts/confirmation_set_sealed.json` is read for connectivity keys only.
- The WUR sealed partition (`artifacts/wur_sealed_partition.json`) is never opened for any `mu` or descriptor value.
- `pytest.ini` sets `pythonpath = src`. Tests import from `src/` and from `tests/` only, never from `scripts/`.
- Ladder energies are exactly `(15.0, 30.0, 45.0, 60.0, 75.0, 90.0)`.
- Base preprocessing cell, from `configs/preprocessing.yaml`: `relative_cutoff=0.0`, `include_precursor=True`, `intensity_transform="raw"`, `precursor_match_ppm=10.0`.
- House style for prose in this repo: no em dashes.

## Established facts (do not re-derive)

These were measured before this plan was written and are inputs, not open questions:

| Fact | Value |
|---|---|
| Realized Stage 0 POS census | 1,010 trajectories, 610 scaffold groups |
| Realized Stage 0 NEG census | 241 trajectories, 178 scaffold groups |
| POS WUR-DEV / WUR-SEALED | 606 / 404 trajectories; 335 / 275 groups |
| NEG WUR-DEV pre-D6 | 241 trajectories, 178 groups |
| D6 effect on NEG | 32 trajectories in 21 groups move to EXCLUDED, leaving 209 DEV |
| D6 effect on POS | none (provable no-op) |
| NEG rows whose own key is sealed | 19 (a strict subset of the 32) |
| Population B realized size | 124 |
| Identity audit (a) multi-adduct keys | 0 POS, 0 NEG |
| Identity audit (b) complete only across adducts | 0 POS, 0 NEG |
| Identity audit (c) complete only across libraries | 0 POS, 0 NEG |
| Blob probe `WUR POS / SpectrumId=1` | Azaperol, key `LVXYAFNPMXCRJI`, scaffold group `c1ccc(CCCCN2CCN(c3ccccn3)CC2)cc1`, side **WUR-DEV**. Not sealed. No quarantine required. |
| Accepted rows | 13,552 POS, 3,800 NEG |
| Peak blob encoding | little-endian float64, `blobMass` and `blobIntensity` equal byte length, mass ascending |

---

### Task 1: Factor the accepted-row table out of the Stage 0 identity gates

`build_qualifying_trajectories` currently inlines the HCD / polarity / energy / identity / adduct gates and then groups. Stage 1 needs the pre-grouping table so it can read exactly the spectra Stage 0 accepted, with no independent reimplementation of the gates. This task extracts that table and makes the existing function consume it, so the two can never drift.

**Files:**
- Modify: `src/muru/io/wur_identity.py`
- Test: `tests/test_wur_identity.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `accepted_rows(raw: pd.DataFrame, polarity: str) -> pd.DataFrame` with columns `source_library, source_polarity_file, spectrum_id, compound_id, connectivity_key, smiles, adduct, energy, precursor_mass, polarity`. One row per accepted spectrum. `build_qualifying_trajectories(raw, polarity)` keeps its existing signature and return columns.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_wur_identity.py`:

```python
from muru.io.wur_identity import accepted_rows

ACETAMINOPHEN = "CC(=O)Nc1ccc(O)cc1"
ACETAMINOPHEN_IK = "RZVAJINKPMORJF-UHFFFAOYSA-N"
ACETAMINOPHEN_MH = 152.070605  # [M+H]+


def _raw_row(**over):
    row = {
        "source_library": "WUR",
        "source_polarity_file": "POS",
        "compound_id": 1,
        "name": "Acetaminophen",
        "formula": "C8H9NO2",
        "smiles": ACETAMINOPHEN,
        "inchikey": ACETAMINOPHEN_IK,
        "spectrum_id": 1,
        "precursor_mass": ACETAMINOPHEN_MH,
        "collision_energy_raw": "15.0",
        "fragmentation_mode": "HCD",
        "polarity": "+",
        "precursor_ion_type": None,
    }
    row.update(over)
    return row


def _raw(rows):
    return pd.DataFrame(rows)


def test_accepted_rows_keeps_one_row_per_accepted_spectrum():
    raw = _raw([_raw_row(spectrum_id=i, collision_energy_raw=f"{e}")
                for i, e in enumerate([15, 30, 45, 60, 75, 90], start=1)])
    acc = accepted_rows(raw, "+")
    assert len(acc) == 6
    assert sorted(acc["energy"]) == [15.0, 30.0, 45.0, 60.0, 75.0, 90.0]
    assert set(acc["spectrum_id"]) == {1, 2, 3, 4, 5, 6}


def test_accepted_rows_carries_the_columns_stage1_needs():
    acc = accepted_rows(_raw([_raw_row()]), "+")
    assert set(acc.columns) >= {
        "source_library", "source_polarity_file", "spectrum_id",
        "connectivity_key", "smiles", "adduct", "energy", "precursor_mass",
    }
    assert acc.iloc[0]["connectivity_key"] == "RZVAJINKPMORJF"
    assert acc.iloc[0]["adduct"] == "[M+H]+"


def test_accepted_rows_rejects_uvpd_offladder_and_wrong_polarity():
    raw = _raw([
        _raw_row(spectrum_id=1, fragmentation_mode="UVPD"),
        _raw_row(spectrum_id=2, collision_energy_raw="40.67"),
        _raw_row(spectrum_id=3, collision_energy_raw="25,38,59"),
        _raw_row(spectrum_id=4, polarity="-"),
        _raw_row(spectrum_id=5),
    ])
    acc = accepted_rows(raw, "+")
    assert list(acc["spectrum_id"]) == [5]


def test_accepted_rows_rejects_unexplained_precursor_mass():
    acc = accepted_rows(_raw([_raw_row(precursor_mass=999.9999)]), "+")
    assert len(acc) == 0


def test_accepted_rows_rejects_smiles_contradicting_its_own_inchikey():
    acc = accepted_rows(_raw([_raw_row(smiles="CCO")]), "+")
    assert len(acc) == 0


def test_build_qualifying_trajectories_agrees_with_accepted_rows():
    raw = _raw([_raw_row(spectrum_id=i, collision_energy_raw=f"{e}")
                for i, e in enumerate([15, 30, 45, 60, 75, 90], start=1)])
    traj = build_qualifying_trajectories(raw, "+")
    acc = accepted_rows(raw, "+")
    assert len(traj) == 1
    assert traj.iloc[0]["connectivity_key"] == "RZVAJINKPMORJF"
    assert traj.iloc[0]["n_source_rows"] == len(acc)
```

Add `import pandas as pd` and `from muru.io.wur_identity import build_qualifying_trajectories` to the file's imports if they are not already present.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_wur_identity.py -v`
Expected: FAIL with `ImportError: cannot import name 'accepted_rows'`

- [ ] **Step 3: Implement `accepted_rows` and rewrite `build_qualifying_trajectories` on top of it**

In `src/muru/io/wur_identity.py`, replace the body of `build_qualifying_trajectories` and add `accepted_rows` above it:

```python
ACCEPTED_COLUMNS = [
    "source_library", "source_polarity_file", "spectrum_id", "compound_id",
    "connectivity_key", "smiles", "adduct", "energy", "precursor_mass",
    "polarity",
]


def accepted_rows(raw: pd.DataFrame, polarity: str) -> pd.DataFrame:
    """One row per spectrum that passes every Stage 0 identity gate.

    This is the single definition of "a spectrum MURU accepted from the WUR
    release". `build_qualifying_trajectories` groups it; Stage 1's mu builder
    reads peaks for exactly these rows. Neither re-implements the gates, so
    they cannot drift apart and a rejected UVPD, off-ladder, wrong-polarity
    or wrong-adduct spectrum cannot leak back in downstream.

    Gates, in order: HCD only; the compound's own Polarity field (not the
    source file name); a collision energy that parses and snaps to a ladder
    rung; a deposited SMILES that verifies against its own InChIKey; and
    exactly one adduct explaining the precursor mass.
    """
    df = raw[
        (raw["fragmentation_mode"] == "HCD")
        & (raw["polarity"] == polarity)
        & raw["smiles"].notna()
        & raw["inchikey"].notna()
    ].copy()

    df["energy"] = (
        df["collision_energy_raw"].map(normalize_collision_energy).map(snap_to_ladder)
    )
    df = df[df["energy"].notna()].copy()

    df["identity_ok"] = pd.array(
        [verify_identity(s, k) for s, k in zip(df["smiles"], df["inchikey"])],
        dtype=bool,
    )
    df = df[df["identity_ok"]].copy()
    df["connectivity_key"] = df["inchikey"].map(connectivity_key)

    df["adduct"] = [
        infer_adduct(s, m, polarity)
        for s, m in zip(df["smiles"], df["precursor_mass"])
    ]
    df = df[df["adduct"].notna()].copy()
    return df.reindex(columns=ACCEPTED_COLUMNS).reset_index(drop=True)
```

Then replace the tail of `build_qualifying_trajectories` so it delegates:

```python
def build_qualifying_trajectories(raw: pd.DataFrame, polarity: str) -> pd.DataFrame:
    """Reduce accepted spectra to one row per qualifying trajectory.

    A trajectory qualifies if its accepted spectra cover the full six-point
    ladder. Duplicate and cross-library deposits of the same connectivity key
    are merged into one row here, not dropped -- this is where defect
    "62/61 duplicate combos" (spec section 3.2) is resolved.

    Returns: connectivity_key, smiles (lexicographically first deposited
    SMILES for that key -- design rule D1), adduct, polarity, n_source_rows,
    source_libraries (sorted tuple).
    """
    df = accepted_rows(raw, polarity)

    columns = ["connectivity_key", "smiles", "adduct", "polarity",
               "n_source_rows", "source_libraries"]
    rows = []
    for key, grp in df.groupby("connectivity_key"):
        if set(grp["energy"]) != set(LADDER_ENERGIES):
            continue
        rows.append({
            "connectivity_key": key,
            "smiles": min(grp["smiles"]),
            "adduct": grp["adduct"].value_counts().idxmax(),
            "polarity": polarity,
            "n_source_rows": len(grp),
            "source_libraries": tuple(sorted(grp["source_library"].unique())),
        })
    return pd.DataFrame(rows, columns=columns)
```

- [ ] **Step 4: Run the full WUR test suite to verify nothing regressed**

Run: `pytest tests/test_wur_identity.py tests/test_wur_qualifying_trajectories.py tests/test_wur_census.py tests/test_wur_raw.py -v`
Expected: PASS, all tests.

- [ ] **Step 5: Commit**

```bash
git add src/muru/io/wur_identity.py tests/test_wur_identity.py
git commit -m "wur: factor the accepted-row table out of the Stage 0 identity gates

Stage 1 must read exactly the spectra Stage 0 accepted. Extracting
accepted_rows() and making build_qualifying_trajectories consume it means
the gates have one definition rather than two that can drift.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 2: Record the identity-only population-definition audit

Three questions had to be answered before Stage 1 could be trusted: whether any qualifying key carries more than one inferred adduct, whether any six-energy ladder is complete only by mixing adducts, and whether any is complete only by unioning separate deposits. All nine counts (three questions, POS and NEG, plus the totals) are zero. This task makes that a tracked artifact and a regression test rather than a claim in prose.

**Files:**
- Create: `src/muru/io/wur_population_audit.py`
- Create: `scripts/build_wur_population_audit.py`
- Create: `tests/test_wur_population_audit.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `accepted_rows` from Task 1.
- Produces: `audit_population(accepted: pd.DataFrame) -> dict` with keys `n_qualifying_keys`, `n_keys_multi_adduct`, `keys_multi_adduct`, `n_keys_complete_only_across_adducts`, `keys_complete_only_across_adducts`, `n_keys_complete_only_across_libraries`, `keys_complete_only_across_libraries`, `is_clean`. Artifact `artifacts/wur_population_audit.json`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_wur_population_audit.py`:

```python
import pandas as pd

from muru.io.wur_population_audit import audit_population

LADDER = [15.0, 30.0, 45.0, 60.0, 75.0, 90.0]


def _rows(key, energies, adduct="[M+H]+", library="WUR"):
    return [{"connectivity_key": key, "energy": e, "adduct": adduct,
             "source_library": library, "spectrum_id": i}
            for i, e in enumerate(energies)]


def test_a_clean_single_adduct_single_library_ladder_is_clean():
    acc = pd.DataFrame(_rows("AAAAAAAAAAAAAA", LADDER))
    result = audit_population(acc)
    assert result["n_qualifying_keys"] == 1
    assert result["n_keys_multi_adduct"] == 0
    assert result["n_keys_complete_only_across_adducts"] == 0
    assert result["n_keys_complete_only_across_libraries"] == 0
    assert result["is_clean"] is True


def test_incomplete_ladders_are_not_qualifying_keys():
    acc = pd.DataFrame(_rows("AAAAAAAAAAAAAA", LADDER[:5]))
    assert audit_population(acc)["n_qualifying_keys"] == 0


def test_a_key_with_two_adducts_is_counted_and_named():
    acc = pd.DataFrame(
        _rows("BBBBBBBBBBBBBB", LADDER)
        + _rows("BBBBBBBBBBBBBB", [45.0], adduct="[M+Na]+")
    )
    result = audit_population(acc)
    assert result["n_keys_multi_adduct"] == 1
    assert result["keys_multi_adduct"] == ["BBBBBBBBBBBBBB"]
    assert result["is_clean"] is False


def test_a_ladder_complete_only_by_mixing_adducts_is_counted():
    acc = pd.DataFrame(
        _rows("CCCCCCCCCCCCCC", LADDER[:3])
        + _rows("CCCCCCCCCCCCCC", LADDER[3:], adduct="[M+NH4]+")
    )
    result = audit_population(acc)
    assert result["n_keys_complete_only_across_adducts"] == 1
    assert result["keys_complete_only_across_adducts"] == ["CCCCCCCCCCCCCC"]
    assert result["is_clean"] is False


def test_a_ladder_complete_only_by_unioning_libraries_is_counted():
    acc = pd.DataFrame(
        _rows("DDDDDDDDDDDDDD", LADDER[:3], library="WUR")
        + _rows("DDDDDDDDDDDDDD", LADDER[3:], library="FCH")
    )
    result = audit_population(acc)
    assert result["n_keys_complete_only_across_libraries"] == 1
    assert result["keys_complete_only_across_libraries"] == ["DDDDDDDDDDDDDD"]
    assert result["is_clean"] is False


def test_one_library_covering_the_ladder_alone_is_clean_even_with_a_second():
    acc = pd.DataFrame(
        _rows("EEEEEEEEEEEEEE", LADDER, library="WUR")
        + _rows("EEEEEEEEEEEEEE", [45.0], library="FCH")
    )
    result = audit_population(acc)
    assert result["n_keys_complete_only_across_libraries"] == 0
    assert result["is_clean"] is True
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_wur_population_audit.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'muru.io.wur_population_audit'`

- [ ] **Step 3: Implement the audit**

Create `src/muru/io/wur_population_audit.py`:

```python
"""Identity-only correctness audit of the Stage 0 population definition.

`build_qualifying_trajectories` calls a connectivity key qualifying when the
UNION of its accepted rows covers the six-point ladder, then picks the modal
adduct. That union is doing real work only if ladders are ever completed by
mixing adducts or by mixing source deposits. This module measures whether
they are, before any mu exists, so that a population-definition defect is
caught as a Stage 0 issue rather than silently absorbed by the Stage 1 mu
builder.

Reads identity columns only. No peak data.
"""
from datetime import datetime, timezone

import pandas as pd

from muru.io.wur_identity import LADDER_ENERGIES


def audit_population(accepted: pd.DataFrame) -> dict:
    """The three population-definition questions, over one polarity's
    accepted-row table."""
    ladder = set(LADDER_ENERGIES)
    qualifying = sorted(
        key for key, grp in accepted.groupby("connectivity_key")
        if set(grp["energy"]) == ladder
    )
    q = accepted[accepted["connectivity_key"].isin(qualifying)]

    multi_adduct = sorted(
        key for key, grp in q.groupby("connectivity_key")
        if grp["adduct"].nunique() > 1
    )
    only_across_adducts = sorted(
        key for key, grp in q.groupby("connectivity_key")
        if not any(set(sub["energy"]) == ladder
                   for _, sub in grp.groupby("adduct"))
    )
    only_across_libraries = sorted(
        key for key, grp in q.groupby("connectivity_key")
        if not any(set(sub["energy"]) == ladder
                   for _, sub in grp.groupby("source_library"))
    )
    return {
        "n_accepted_rows": int(len(accepted)),
        "n_qualifying_keys": len(qualifying),
        "n_keys_multi_adduct": len(multi_adduct),
        "keys_multi_adduct": multi_adduct,
        "n_keys_complete_only_across_adducts": len(only_across_adducts),
        "keys_complete_only_across_adducts": only_across_adducts,
        "n_keys_complete_only_across_libraries": len(only_across_libraries),
        "keys_complete_only_across_libraries": only_across_libraries,
        "is_clean": not (multi_adduct or only_across_adducts
                         or only_across_libraries),
    }


def build_population_audit(accepted: dict[str, pd.DataFrame]) -> dict:
    """The audit over both polarities, as a writable artifact."""
    polarities = {pf: audit_population(df) for pf, df in accepted.items()}
    return {
        "purpose": "Identity-only correctness audit of the Stage 0 "
                   "population definition. Run before any mu exists.",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "questions": {
            "multi_adduct": "qualifying keys carrying more than one inferred "
                            "adduct across accepted rows",
            "complete_only_across_adducts": "six-energy ladders that stop "
                                            "being complete when completeness "
                                            "is required within one adduct",
            "complete_only_across_libraries": "six-energy ladders that exist "
                                              "only because rows from "
                                              "different source deposits were "
                                              "unioned",
        },
        "polarities": polarities,
        "is_clean": all(p["is_clean"] for p in polarities.values()),
    }
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_wur_population_audit.py -v`
Expected: PASS, 6 tests.

- [ ] **Step 5: Add the CLI**

Create `scripts/build_wur_population_audit.py`:

```python
"""CLI: write artifacts/wur_population_audit.json from data/external/wur/.

No logic lives here -- everything testable is in
muru.io.wur_population_audit. Identity-only: no peak blobs are read.
"""
import json
import sys
from pathlib import Path

from muru.io import wur_raw
from muru.io.wur_identity import accepted_rows
from muru.io.wur_population_audit import build_population_audit

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"
    accepted = {}
    for polarity_file, symbol in (("POS", "+"), ("NEG", "-")):
        raw = wur_raw.read_all_libraries(data_dir, polarity_file)
        accepted[polarity_file] = accepted_rows(raw, symbol)

    audit = build_population_audit(accepted)
    (ROOT / "artifacts" / "wur_population_audit.json").write_text(
        json.dumps(audit, indent=2) + "\n")

    print("Wrote wur_population_audit.json")
    for polarity_file, entry in audit["polarities"].items():
        print(f"  {polarity_file}: {entry['n_accepted_rows']} accepted rows, "
              f"{entry['n_qualifying_keys']} qualifying keys, "
              f"clean={entry['is_clean']}")
    if not audit["is_clean"]:
        print("POPULATION DEFINITION DEFECT: see the artifact", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 6: Track the new artifact**

In `.gitignore`, immediately after the line `!artifacts/wur_identity_census.json`, add:

```
!artifacts/wur_population_audit.json
```

- [ ] **Step 7: Run the CLI and confirm every count is zero**

Run: `PYTHONPATH=src python scripts/build_wur_population_audit.py`
Expected output:
```
Wrote wur_population_audit.json
  POS: 13552 accepted rows, 1010 qualifying keys, clean=True
  NEG: 3800 accepted rows, 241 qualifying keys, clean=True
```
Exit code 0. If any count is nonzero, STOP and escalate: that is a Stage 0 population-definition correctness issue and must not be solved inside `wur_spectra.py`.

- [ ] **Step 8: Commit**

```bash
git add src/muru/io/wur_population_audit.py scripts/build_wur_population_audit.py tests/test_wur_population_audit.py artifacts/wur_population_audit.json .gitignore
git commit -m "wur: audit the Stage 0 population definition, identity-only

The qualifying rule unions a key's accepted rows before checking ladder
coverage. This measures whether that union ever does load-bearing work:
multi-adduct keys, ladders complete only across adducts, and ladders
complete only across source deposits. All nine counts are zero.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 3: Add rule D6 as a development-exposure exclusion

D5 sends every negative-mode trajectory to WUR-DEV without consulting the scaffold-group logic that D2-D4 use, so a NEG compound can sit in development while its scaffold group is sealed on the positive side. D6 closes that. It is scoped to development exposure only: a WUR-SEALED row is never relabelled.

**Files:**
- Modify: `src/muru/io/wur_partition.py`
- Modify: `scripts/build_wur_partition.py`
- Create: `tests/test_wur_d6.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `partition()` output from `wur_partition`.
- Produces: `sealed_scaffold_groups(pos_partitioned) -> set[str]`, `apply_d6(partitioned, sealed_groups) -> dict[str, pd.DataFrame]` (adds `"EXCLUDED"` as a third value of `side`), `build_dev_neg_keys(neg_partitioned) -> dict`. Artifact `artifacts/wur_dev_neg_keys.json`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_wur_d6.py`:

```python
import pandas as pd

from muru.io.wur_partition import (
    apply_d6, build_dev_neg_keys, partition, sealed_scaffold_groups,
)


def _partitioned():
    """POS: one dev group, one sealed group. NEG: one row in a scaffold group
    that is sealed on the POS side, one row in a group that is not."""
    pos = pd.DataFrame({
        "connectivity_key": ["PDEV", "PSEAL"],
        "scaffold_group": ["gdev", "gseal"],
        "side": ["WUR-DEV", "WUR-SEALED"],
    })
    neg = pd.DataFrame({
        "connectivity_key": ["NOVERLAP", "NFREE"],
        "scaffold_group": ["gseal", "gneg"],
        "side": ["WUR-DEV", "WUR-DEV"],
    })
    return {"POS": pos, "NEG": neg}


def test_sealed_scaffold_groups_reads_the_pos_sealed_side():
    assert sealed_scaffold_groups(_partitioned()["POS"]) == {"gseal"}


def test_d6_excludes_a_neg_dev_row_in_a_sealed_pos_scaffold_group():
    part = _partitioned()
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    neg = out["NEG"].set_index("connectivity_key")["side"]
    assert neg["NOVERLAP"] == "EXCLUDED"
    assert neg["NFREE"] == "WUR-DEV"


def test_d6_never_relabels_a_sealed_row():
    part = _partitioned()
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    pos = out["POS"].set_index("connectivity_key")["side"]
    assert pos["PSEAL"] == "WUR-SEALED"
    assert pos["PDEV"] == "WUR-DEV"


def test_d6_leaves_the_pos_sealed_key_list_identical():
    part = _partitioned()
    before = sorted(part["POS"].loc[part["POS"]["side"] == "WUR-SEALED",
                                    "connectivity_key"])
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    after = sorted(out["POS"].loc[out["POS"]["side"] == "WUR-SEALED",
                                   "connectivity_key"])
    assert before == after


def test_d6_is_a_no_op_on_pos():
    part = _partitioned()
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    pd.testing.assert_series_equal(
        part["POS"].set_index("connectivity_key")["side"].sort_index(),
        out["POS"].set_index("connectivity_key")["side"].sort_index(),
    )


def test_d6_is_idempotent():
    part = _partitioned()
    groups = sealed_scaffold_groups(part["POS"])
    once = apply_d6(part, groups)
    twice = apply_d6(once, sealed_scaffold_groups(once["POS"]))
    for polarity in ("POS", "NEG"):
        pd.testing.assert_frame_equal(
            once[polarity].sort_values("connectivity_key").reset_index(drop=True),
            twice[polarity].sort_values("connectivity_key").reset_index(drop=True),
        )


def test_after_d6_no_dev_row_in_either_polarity_is_in_a_sealed_group():
    part = _partitioned()
    groups = sealed_scaffold_groups(part["POS"])
    out = apply_d6(part, groups)
    for polarity in ("POS", "NEG"):
        dev = out[polarity][out[polarity]["side"] == "WUR-DEV"]
        assert not (set(dev["scaffold_group"]) & groups)


def test_sides_still_account_for_every_row_in_each_polarity():
    part = _partitioned()
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    for polarity in ("POS", "NEG"):
        df = out[polarity]
        counts = df["side"].value_counts()
        total = (counts.get("WUR-DEV", 0) + counts.get("WUR-SEALED", 0)
                 + counts.get("EXCLUDED", 0))
        assert total == len(part[polarity])


def test_build_dev_neg_keys_lists_only_post_d6_dev_keys():
    part = _partitioned()
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    listing = build_dev_neg_keys(out["NEG"])
    assert listing["connectivity_keys"] == ["NFREE"]
    assert listing["n_compounds"] == 1


def test_d6_runs_on_a_real_shaped_partition_without_touching_free_groups():
    pos = pd.DataFrame({
        "connectivity_key": [f"K{i}" for i in range(20)],
        "scaffold_group": [f"g{i}" for i in range(20)],
        "in_lcsb_dev": [False] * 20,
        "in_lcsb_sealed": [False] * 20,
    })
    neg = pd.DataFrame({
        "connectivity_key": ["N0"], "scaffold_group": ["ng0"],
        "in_lcsb_dev": [False], "in_lcsb_sealed": [False],
    })
    part = partition({"POS": pos, "NEG": neg})
    out = apply_d6(part, sealed_scaffold_groups(part["POS"]))
    assert (out["NEG"]["side"] == "WUR-DEV").all()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_wur_d6.py -v`
Expected: FAIL with `ImportError: cannot import name 'apply_d6'`

- [ ] **Step 3: Implement D6**

Append to `src/muru/io/wur_partition.py`:

```python
def sealed_scaffold_groups(pos_partitioned: pd.DataFrame) -> set[str]:
    """The positive-mode scaffold groups held by WUR-SEALED. D6's input."""
    return set(pos_partitioned.loc[
        pos_partitioned["side"] == "WUR-SEALED", "scaffold_group"])


def apply_d6(partitioned: dict[str, pd.DataFrame],
             sealed_groups: set[str]) -> dict[str, pd.DataFrame]:
    """D6: a development-exposure exclusion, applied over D1-D5.

    D5 routes every negative-mode trajectory to WUR-DEV without consulting
    the scaffold-group logic that D2-D4 use, so a negative-mode compound can
    sit in development while its scaffold group is sealed on the positive
    side. D6 removes exactly those rows:

        side == "WUR-DEV" AND scaffold_group in sealed_groups -> "EXCLUDED"

    Scope is deliberately narrow. A WUR-SEALED row is never relabelled, so
    the sealed key list is untouched and the sealed-part floor is unmoved.
    The rule is written for both polarities and is a provable no-op on POS,
    because D1-D4 never split a scaffold group across sides. It is applied
    as a filter over the D1-D5 result; it does not re-run the partition.
    """
    out = {}
    for polarity_file, df in partitioned.items():
        df = df.copy()
        excluded = (df["side"] == "WUR-DEV") & df["scaffold_group"].isin(sealed_groups)
        df.loc[excluded, "side"] = "EXCLUDED"
        out[polarity_file] = df
    return out


def build_dev_neg_keys(neg_partitioned: pd.DataFrame) -> dict:
    """The corrected negative-mode WUR-DEV list, after D6."""
    dev = neg_partitioned[neg_partitioned["side"] == "WUR-DEV"]
    return {
        "purpose": "Negative-mode WUR-DEV connectivity keys after rule D6. "
                   "No negative-mode external claim is made (rule D5).",
        "constructed_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "n_compounds": int(len(dev)),
        "n_scaffold_groups": int(dev["scaffold_group"].nunique()) if len(dev) else 0,
        "connectivity_keys": sorted(dev["connectivity_key"].tolist()),
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_wur_d6.py -v`
Expected: PASS, 10 tests.

- [ ] **Step 5: Extend the split manifest to carry D6's accounting**

In `src/muru/io/wur_partition.py`, replace `build_split_manifest` with a version that takes both the pre-D6 and post-D6 partitions so the before/after counts are preserved rather than history being rewritten:

```python
def build_split_manifest(partitioned: dict[str, pd.DataFrame],
                         pre_d6: dict[str, pd.DataFrame] | None = None) -> dict:
    """The split manifest. `partitioned` is the post-D6 assignment; `pre_d6`
    is the D1-D5 assignment, preserved so the D6 record shows what moved."""
    manifest = {"seed": SEED, "created_utc": datetime.now(timezone.utc).isoformat(),
                "polarities": {}}
    for polarity_file, df in partitioned.items():
        entry = {
            "n_trajectories": int(len(df)),
            "n_scaffold_groups": int(df["scaffold_group"].nunique()) if len(df) else 0,
        }
        for side in ("WUR-DEV", "WUR-SEALED", "EXCLUDED"):
            sub = df[df["side"] == side]
            entry[side] = {
                "n_trajectories": int(len(sub)),
                "n_scaffold_groups": int(sub["scaffold_group"].nunique()) if len(sub) else 0,
            }
        entry["sides_account_for_all_rows"] = bool(
            entry["WUR-DEV"]["n_trajectories"]
            + entry["WUR-SEALED"]["n_trajectories"]
            + entry["EXCLUDED"]["n_trajectories"] == entry["n_trajectories"])
        if pre_d6 is not None:
            before = pre_d6[polarity_file]
            before_dev = before[before["side"] == "WUR-DEV"]
            after_dev = df[df["side"] == "WUR-DEV"]
            moved = df[df["side"] == "EXCLUDED"]
            entry["d6"] = {
                "rule": "side == WUR-DEV AND scaffold_group in positive-mode "
                        "WUR-SEALED groups -> EXCLUDED",
                "dev_trajectories_before": int(len(before_dev)),
                "dev_trajectories_after": int(len(after_dev)),
                "excluded_trajectories": int(len(moved)),
                "excluded_scaffold_groups": int(moved["scaffold_group"].nunique())
                    if len(moved) else 0,
            }
        if polarity_file == "POS":
            entry["sealed_floor_check"] = check_sealed_floor(
                df[df["side"] == "WUR-SEALED"])
        manifest["polarities"][polarity_file] = entry
    return manifest
```

- [ ] **Step 6: Run the manifest tests**

Run: `pytest tests/test_wur_partition.py tests/test_wur_partition_manifests.py -v`
Expected: PASS. `build_split_manifest` keeps its old one-argument call signature, so existing tests are unaffected.

- [ ] **Step 7: Commit**

```bash
git add src/muru/io/wur_partition.py tests/test_wur_d6.py
git commit -m "wur: add rule D6, a development-exposure exclusion over D1-D5

D5 routes every negative-mode trajectory to WUR-DEV without consulting the
scaffold-group logic D2-D4 use, so a NEG compound can sit in development
while its scaffold group is sealed on the positive side. D6 removes exactly
those rows and never relabels a WUR-SEALED row, so the sealed key list and
the sealed-part floor are untouched. Provably a no-op on POS.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 4: Add environment provenance and canonical content hashes, then re-run Stage 0

The Stage 0 review asked for library versions and a source-manifest hash in both manifests, plus a reproducibility check that the 404-key sealed list comes back unchanged. Whole-file byte-identity is impossible because both manifests stamp a creation time, so the reproducibility contract is a canonical content hash over the scientific payload, defined exactly.

**Files:**
- Create: `src/muru/io/wur_provenance.py`
- Modify: `src/muru/io/wur_partition.py`
- Modify: `scripts/build_wur_partition.py`
- Create: `tests/test_wur_provenance.py`
- Modify: `tests/test_wur_partition_manifests.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: `apply_d6`, `sealed_scaffold_groups`, `build_dev_neg_keys` from Task 3.
- Produces: `environment_provenance(root: Path) -> dict`, `canonical_key_hash(keys: Iterable[str]) -> str`. Both `build_sealed_partition` and `build_split_manifest` gain an `environment` block; the sealed partition and the NEG dev list gain `connectivity_keys_sha256`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_wur_provenance.py`:

```python
import hashlib
from pathlib import Path

from muru.io.wur_provenance import canonical_key_hash, environment_provenance

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_key_hash_is_sha256_of_sorted_keys_joined_by_newline():
    keys = ["BBB", "AAA", "CCC"]
    expected = hashlib.sha256("AAA\nBBB\nCCC".encode("utf-8")).hexdigest()
    assert canonical_key_hash(keys) == expected


def test_canonical_key_hash_ignores_input_order():
    assert canonical_key_hash(["B", "A"]) == canonical_key_hash(["A", "B"])


def test_canonical_key_hash_of_an_empty_list_is_the_empty_string_hash():
    assert canonical_key_hash([]) == hashlib.sha256(b"").hexdigest()


def test_canonical_key_hash_distinguishes_different_key_sets():
    assert canonical_key_hash(["A", "B"]) != canonical_key_hash(["A", "C"])


def test_environment_provenance_records_every_required_library():
    env = environment_provenance(ROOT)
    assert set(env) >= {
        "python", "rdkit", "pandas", "numpy", "scipy", "pyarrow",
        "git_commit_sha", "wur_retrieval_manifest_sha256",
    }
    for field in ("python", "rdkit", "pandas", "numpy", "scipy", "pyarrow"):
        assert isinstance(env[field], str) and env[field]


def test_environment_provenance_hashes_the_real_retrieval_manifest():
    env = environment_provenance(ROOT)
    raw = (ROOT / "artifacts" / "wur_retrieval_manifest.json").read_bytes()
    assert env["wur_retrieval_manifest_sha256"] == hashlib.sha256(raw).hexdigest()


def test_environment_provenance_is_json_serializable():
    import json
    json.dumps(environment_provenance(ROOT))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_wur_provenance.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'muru.io.wur_provenance'`

- [ ] **Step 3: Implement the provenance helpers**

Create `src/muru/io/wur_provenance.py`:

```python
"""Environment provenance and canonical content hashes for WUR artifacts.

Both Stage 0 manifests stamp a creation time, so whole-file byte-identity
across runs is impossible by construction. The reproducibility contract is
instead a canonical hash over the scientific payload: re-running the Stage 0
CLI must reproduce `connectivity_keys_sha256` exactly. Timestamps are
allowed to move; content hashes are not.
"""
import hashlib
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

import numpy
import pandas
import scipy
from rdkit import rdBase


def canonical_key_hash(keys: Iterable[str]) -> str:
    """SHA-256 over the UTF-8 bytes of the sorted keys joined by "\\n".

    Sorted, newline-joined, no trailing newline, no separators beyond the
    joins. This exact serialization is the contract; changing it invalidates
    every recorded hash.
    """
    payload = "\n".join(sorted(keys)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _git_commit_sha(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=30,
        )
        return out.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return "unavailable"


def _pyarrow_version() -> str:
    try:
        import pyarrow
        return pyarrow.__version__
    except ImportError:
        return "absent"


def environment_provenance(root: Path) -> dict:
    """The interpreter, the libraries whose behaviour the results depend on,
    the commit that produced them, and the hash of the frozen release
    manifest they were computed against.

    rdkit sets the scaffold groups and the identity gate; pandas and numpy
    set the grouping and the medians; scipy supplies Spearman and PCHIP;
    pyarrow is the parquet engine that reads the LCSB corpus.
    """
    manifest = root / "artifacts" / "wur_retrieval_manifest.json"
    return {
        "python": sys.version.split()[0],
        "rdkit": rdBase.rdkitVersion,
        "pandas": pandas.__version__,
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "pyarrow": _pyarrow_version(),
        "git_commit_sha": _git_commit_sha(root),
        "wur_retrieval_manifest_sha256":
            hashlib.sha256(manifest.read_bytes()).hexdigest(),
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_wur_provenance.py -v`
Expected: PASS, 7 tests.

- [ ] **Step 5: Wire provenance into the manifest builders**

In `src/muru/io/wur_partition.py`, add to the imports:

```python
from pathlib import Path

from muru.io.wur_provenance import canonical_key_hash, environment_provenance

ROOT = Path(__file__).resolve().parents[3]
```

Change the three builders to carry provenance. In `build_split_manifest`, change the opening dict to:

```python
    manifest = {"seed": SEED, "created_utc": datetime.now(timezone.utc).isoformat(),
                "environment": environment_provenance(ROOT),
                "polarities": {}}
```

In `build_sealed_partition`, replace the returned dict with:

```python
    keys = sorted(sealed["connectivity_key"].tolist())
    return {
        "purpose": "SEALED WUR external-validation partition. Do not open "
                   "during Stage 2 development fitting.",
        "constructed_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "selection_unit": "bemis_murcko_scaffold_group",
        "environment": environment_provenance(ROOT),
        "n_scaffold_groups": int(sealed["scaffold_group"].nunique()),
        "n_compounds": int(len(sealed)),
        "connectivity_keys": keys,
        "connectivity_keys_sha256": canonical_key_hash(keys),
        "disclosure": "These WUR compounds are reserved for one look at a "
                      "candidate frozen on development (Stage 3). Not read "
                      "for any mu or descriptor value before that freeze.",
    }
```

In `build_dev_neg_keys`, add the same hash. Replace its return statement with:

```python
    keys = sorted(dev["connectivity_key"].tolist())
    return {
        "purpose": "Negative-mode WUR-DEV connectivity keys after rule D6. "
                   "No negative-mode external claim is made (rule D5).",
        "constructed_utc": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "environment": environment_provenance(ROOT),
        "n_compounds": int(len(dev)),
        "n_scaffold_groups": int(dev["scaffold_group"].nunique()) if len(dev) else 0,
        "connectivity_keys": keys,
        "connectivity_keys_sha256": canonical_key_hash(keys),
    }
```

- [ ] **Step 6: Update the sealed-partition key-set test**

In `tests/test_wur_partition_manifests.py`, replace the assertion inside `test_sealed_partition_is_json_serializable_with_only_identifiers` with:

```python
    assert set(sealed) == {
        "purpose", "constructed_utc", "seed", "selection_unit", "environment",
        "n_scaffold_groups", "n_compounds", "connectivity_keys",
        "connectivity_keys_sha256", "disclosure",
    }
```

and append to the same file:

```python
def test_sealed_partition_hash_matches_its_own_key_list():
    from muru.io.wur_provenance import canonical_key_hash
    sealed = build_sealed_partition(partition(_annotated())["POS"])
    assert sealed["connectivity_keys_sha256"] == canonical_key_hash(
        sealed["connectivity_keys"])


def test_sealed_partition_environment_carries_no_compound_identity():
    sealed = build_sealed_partition(partition(_annotated())["POS"])
    env_text = json.dumps(sealed["environment"])
    for key in sealed["connectivity_keys"]:
        assert key not in env_text
```

- [ ] **Step 7: Run the manifest tests**

Run: `pytest tests/test_wur_partition_manifests.py -v`
Expected: PASS.

- [ ] **Step 8: Wire D6 and the NEG dev list into the Stage 0 CLI**

Replace the body of `scripts/build_wur_partition.py` below the imports:

```python
"""CLI: build artifacts/wur_split_manifest.json,
artifacts/wur_sealed_partition.json and artifacts/wur_dev_neg_keys.json
from data/external/wur/.

No logic lives here -- everything testable is in
muru.io.wur_partition (see that module's own tests). This script only
wires it to real files. Identity-only: no peak blobs are read.
"""
import json
import sys
from pathlib import Path

from muru.io.wur_census import load_annotated_trajectories
from muru.io.wur_partition import (
    apply_d6, build_dev_neg_keys, build_sealed_partition, build_split_manifest,
    partition, sealed_scaffold_groups,
)

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"
    pre_d6 = partition(load_annotated_trajectories(data_dir))

    sealed_groups = sealed_scaffold_groups(pre_d6["POS"])
    partitioned = apply_d6(pre_d6, sealed_groups)

    # D6 invariants, asserted rather than assumed.
    sealed_before = sorted(pre_d6["POS"].loc[
        pre_d6["POS"]["side"] == "WUR-SEALED", "connectivity_key"])
    sealed_after = sorted(partitioned["POS"].loc[
        partitioned["POS"]["side"] == "WUR-SEALED", "connectivity_key"])
    assert sealed_before == sealed_after, "D6 moved a sealed row"
    assert partitioned["POS"]["side"].equals(pre_d6["POS"]["side"]), \
        "D6 was not a no-op on POS"
    for polarity_file, df in partitioned.items():
        dev_groups = set(df.loc[df["side"] == "WUR-DEV", "scaffold_group"])
        assert not (dev_groups & sealed_groups), \
            f"{polarity_file}: a WUR-DEV row sits in a sealed scaffold group"
        assert len(df) == len(pre_d6[polarity_file]), \
            f"{polarity_file}: D6 changed the row count"

    split_manifest = build_split_manifest(partitioned, pre_d6=pre_d6)
    (ROOT / "artifacts" / "wur_split_manifest.json").write_text(
        json.dumps(split_manifest, indent=2) + "\n")

    sealed_partition = build_sealed_partition(partitioned["POS"])
    (ROOT / "artifacts" / "wur_sealed_partition.json").write_text(
        json.dumps(sealed_partition, indent=2) + "\n")

    dev_neg = build_dev_neg_keys(partitioned["NEG"])
    (ROOT / "artifacts" / "wur_dev_neg_keys.json").write_text(
        json.dumps(dev_neg, indent=2) + "\n")

    floor = split_manifest["polarities"]["POS"]["sealed_floor_check"]
    print("Wrote wur_split_manifest.json, wur_sealed_partition.json and "
          "wur_dev_neg_keys.json")
    print(f"  POS WUR-SEALED: {floor['n_trajectories']} trajectories, "
          f"{floor['n_scaffold_groups']} scaffold groups")
    print(f"  sealed key hash: {sealed_partition['connectivity_keys_sha256']}")
    for polarity_file, entry in split_manifest["polarities"].items():
        d6 = entry.get("d6", {})
        print(f"  {polarity_file} D6: dev {d6.get('dev_trajectories_before')} -> "
              f"{d6.get('dev_trajectories_after')}, excluded "
              f"{d6.get('excluded_trajectories')} in "
              f"{d6.get('excluded_scaffold_groups')} groups")
    if not (floor["passes_trajectory_floor"] and floor["passes_scaffold_group_floor"]):
        print(f"WARNING: sealed part below floor: {floor}", file=sys.stderr)
        sys.exit(1)
```

- [ ] **Step 9: Track the new artifact**

In `.gitignore`, immediately after the line `!artifacts/wur_sealed_partition.json`, add:

```
!artifacts/wur_dev_neg_keys.json
```

- [ ] **Step 10: Capture the pre-change sealed key hash**

Before re-running, record what the current committed sealed list hashes to, so the reproducibility check has a baseline:

```bash
python - <<'PY'
import hashlib, json, pathlib
keys = json.loads(pathlib.Path("artifacts/wur_sealed_partition.json").read_text())["connectivity_keys"]
print(len(keys), hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest())
PY
```

Write the printed count and hash down. Expected count: 404.

- [ ] **Step 11: Re-run the Stage 0 CLI once**

Run: `PYTHONPATH=src python scripts/build_wur_partition.py`
Expected: exit 0, `POS WUR-SEALED: 404 trajectories, 275 scaffold groups`, `NEG D6: dev 241 -> 209, excluded 32 in 21 groups`, `POS D6: dev 606 -> 606, excluded 0 in 0 groups`.

- [ ] **Step 12: Confirm the sealed list reproduced**

```bash
python - <<'PY'
import hashlib, json, pathlib
d = json.loads(pathlib.Path("artifacts/wur_sealed_partition.json").read_text())
keys = d["connectivity_keys"]
recomputed = hashlib.sha256("\n".join(sorted(keys)).encode()).hexdigest()
print("n_keys          ", len(keys))
print("recorded hash   ", d["connectivity_keys_sha256"])
print("recomputed hash ", recomputed)
print("self-consistent ", d["connectivity_keys_sha256"] == recomputed)
PY
git diff --stat artifacts/wur_sealed_partition.json
```

The hash must equal the Step 10 baseline and the key count must be 404. Confirm via `git diff artifacts/wur_sealed_partition.json` that the only changed lines are `constructed_utc`, the new `environment` block, and the new `connectivity_keys_sha256` line. If any connectivity key changed, STOP and escalate.

- [ ] **Step 13: Run the whole WUR suite**

Run: `pytest tests/ -k wur -v`
Expected: PASS.

- [ ] **Step 14: Commit**

```bash
git add src/muru/io/wur_provenance.py src/muru/io/wur_partition.py scripts/build_wur_partition.py tests/test_wur_provenance.py tests/test_wur_partition_manifests.py artifacts/wur_split_manifest.json artifacts/wur_sealed_partition.json artifacts/wur_dev_neg_keys.json .gitignore
git commit -m "wur: add environment provenance, canonical key hashes, and D6 accounting

Both manifests now carry python/rdkit/pandas/numpy/scipy/pyarrow versions,
the git commit, and the sha256 of the frozen retrieval manifest. Whole-file
byte-identity is impossible because both stamp a creation time, so the
reproducibility contract is connectivity_keys_sha256, defined as sha256 over
the sorted keys joined by newline. Re-running the CLI reproduced the 404-key
sealed list unchanged.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 5: Freeze `MURU_WUR_REAL_DATA_PREREGISTRATION.md`

This is the governance boundary. Every Stage 1 degree of freedom is fixed here, in a commit that exists before any real `mu` is computed. The document is prose plus one small module of frozen constants that the code imports, so a threshold cannot be changed in code without the diff showing it.

**Files:**
- Create: `MURU_WUR_REAL_DATA_PREREGISTRATION.md`
- Create: `src/muru/wur_bridge_constants.py`
- Create: `tests/test_wur_bridge_constants.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `LADDER_ENERGIES`, `MEDIAN_ABS_DELTA_MAX = 0.05`, `SPEARMAN_MIN = 0.80`, `MIN_PASSING_ENERGIES = 5`, `OFFSET_MAX = 0.15`, `ALIGNMENT_A_BOUNDS = (-30.0, 30.0)`, `ALIGNMENT_B_BOUNDS = (0.5, 2.0)`, `SEED = 20260911`, `BASE_CELL`, `PRECURSOR_MATCH_PPM = 10.0`, `DUPLICATE_AGGREGATOR = "median"`.

- [ ] **Step 1: Write the failing test**

Create `tests/test_wur_bridge_constants.py`:

```python
"""The preregistered constants are a contract. These tests exist so that
changing one shows up as a failing test, not a silent edit."""
from muru import wur_bridge_constants as K


def test_gate_thresholds_match_the_preregistration():
    assert K.MEDIAN_ABS_DELTA_MAX == 0.05
    assert K.SPEARMAN_MIN == 0.80
    assert K.MIN_PASSING_ENERGIES == 5
    assert K.OFFSET_MAX == 0.15


def test_ladder_is_the_six_point_nce_ladder():
    assert K.LADDER_ENERGIES == (15.0, 30.0, 45.0, 60.0, 75.0, 90.0)


def test_base_cell_matches_configs_preprocessing_yaml():
    import yaml
    from pathlib import Path
    cfg = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / "configs" / "preprocessing.yaml").read_text())
    assert K.BASE_CELL["relative_cutoff"] == cfg["base_cell"]["relative_cutoff"]
    assert K.BASE_CELL["include_precursor"] == cfg["base_cell"]["include_precursor"]
    assert K.BASE_CELL["intensity_transform"] == cfg["base_cell"]["intensity_transform"]
    assert K.PRECURSOR_MATCH_PPM == cfg["precursor_match_ppm"]


def test_alignment_bounds_are_a_positive_monotone_box():
    lo, hi = K.ALIGNMENT_B_BOUNDS
    assert lo > 0 and hi > lo
    a_lo, a_hi = K.ALIGNMENT_A_BOUNDS
    assert a_lo < 0 < a_hi


def test_duplicate_aggregator_is_the_preregistered_median():
    assert K.DUPLICATE_AGGREGATOR == "median"


def test_seed_matches_the_stage_zero_seed():
    from muru.io.wur_partition import SEED as STAGE0_SEED
    assert K.SEED == STAGE0_SEED == 20260911
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_wur_bridge_constants.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'muru.wur_bridge_constants'`

- [ ] **Step 3: Write the constants module**

Create `src/muru/wur_bridge_constants.py`:

```python
"""Frozen Stage 1 constants, from MURU_WUR_REAL_DATA_PREREGISTRATION.md.

Every value here was fixed before any real delta was computed. They live in
one module, imported rather than inlined, so that changing one is a visible
diff against a preregistered document and not an edit buried in an analysis
script. A change to any of them voids the gate, and the preregistration says
so in those words.
"""

SEED = 20260911

LADDER_ENERGIES = (15.0, 30.0, 45.0, 60.0, 75.0, 90.0)

# Base preprocessing cell, configs/preprocessing.yaml.
BASE_CELL = {
    "relative_cutoff": 0.0,
    "include_precursor": True,
    "intensity_transform": "raw",
}
PRECURSOR_MATCH_PPM = 10.0

# Duplicate (connectivity_key, energy) spectra collapse to one mu by this
# aggregator, chosen before any real mu existed.
DUPLICATE_AGGREGATOR = "median"

# The gate.
MEDIAN_ABS_DELTA_MAX = 0.05   # ~1.7x the 0.0295 inter-mixture repeatability SD
SPEARMAN_MIN = 0.80
MIN_PASSING_ENERGIES = 5      # of 6

# Entry condition for the POOL_AFTER_ENERGY_ALIGNMENT branch.
OFFSET_MAX = 0.15

# The monotone affine energy map T(E) = a + b*E, fitted only if that branch
# is entered. A generous a-priori box, not tuned.
ALIGNMENT_A_BOUNDS = (-30.0, 30.0)
ALIGNMENT_B_BOUNDS = (0.5, 2.0)
ALIGNMENT_MAXITER = 1000
ALIGNMENT_TOL = 1e-8
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `pytest tests/test_wur_bridge_constants.py -v`
Expected: PASS, 6 tests.

- [ ] **Step 5: Write the preregistration**

Create `MURU_WUR_REAL_DATA_PREREGISTRATION.md` with the content given in the appendix of this plan (see "Appendix A: preregistration text" below). Copy it verbatim; it is not a sketch.

- [ ] **Step 6: Verify the document is internally consistent with the code**

Run: `pytest tests/test_wur_bridge_constants.py tests/ -k wur -v`
Expected: PASS.

Then confirm by eye that every numeric threshold quoted in the preregistration appears in `src/muru/wur_bridge_constants.py` with the same value, and that the realized counts quoted in its section 3 match `artifacts/wur_split_manifest.json` and `artifacts/wur_population_audit.json`.

- [ ] **Step 7: Commit the freeze**

```bash
git add MURU_WUR_REAL_DATA_PREREGISTRATION.md src/muru/wur_bridge_constants.py tests/test_wur_bridge_constants.py
git commit -m "prereg: freeze MURU_WUR_REAL_DATA_PREREGISTRATION.md

Supersedes wfsr-external-1.0. Carries the drift record, rules D1-D6 with the
realized Stage 0 counts, the Stage 1 bridge rule with every remaining degree
of freedom fixed (median duplicate aggregation, the exact energy-alignment
algorithm, the Spearman and median definitions), the Stage 2 adequacy
fractions, the inherited thresholds, the sealed-part floor, and the CC-BY
permission basis.

Frozen before any Stage 1 mu exists. No WUR peak data has been read at this
commit beyond the single disclosed format probe recorded in section 9.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

- [ ] **Step 8: Record the freeze commit SHA**

```bash
git rev-parse HEAD
```

Write it down. It is the boundary: everything after it may compute `mu`.

---

### Task 6: Read peak blobs from mzVault

The mzVault `blobMass` and `blobIntensity` columns are little-endian float64 arrays of equal length. This task decodes them and nothing else, so the decoder can be tested against in-test SQLite databases with no real release file present.

**Files:**
- Create: `src/muru/io/wur_spectra.py`
- Create: `tests/test_wur_spectra.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: `decode_blob(blob: bytes) -> np.ndarray`, `BlobDefect` (exception), `read_spectrum_peaks(db_path, spectrum_ids) -> dict[int, tuple[np.ndarray, np.ndarray]]`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_wur_spectra.py`:

```python
import sqlite3

import numpy as np
import pytest

from muru.io.wur_spectra import BlobDefect, decode_blob, read_spectrum_peaks


def test_decode_blob_reads_little_endian_float64():
    values = np.array([52.9174027, 121.07587178, 330.19774367])
    assert np.allclose(decode_blob(values.astype("<f8").tobytes()), values)


def test_decode_blob_rejects_a_length_that_is_not_a_multiple_of_eight():
    with pytest.raises(BlobDefect, match="length"):
        decode_blob(b"\x00" * 12)


def test_decode_blob_rejects_an_empty_blob():
    with pytest.raises(BlobDefect, match="empty"):
        decode_blob(b"")


def test_decode_blob_rejects_none():
    with pytest.raises(BlobDefect, match="missing"):
        decode_blob(None)


def _tiny_db(tmp_path, rows):
    """rows: (spectrum_id, mz_array, intensity_array)"""
    path = tmp_path / "tiny.db"
    con = sqlite3.connect(str(path))
    con.execute("CREATE TABLE SpectrumTable "
                "(SpectrumId INTEGER, blobMass BLOB, blobIntensity BLOB)")
    for sid, mz, inten in rows:
        con.execute("INSERT INTO SpectrumTable VALUES (?, ?, ?)",
                    (sid, np.asarray(mz, dtype="<f8").tobytes(),
                     np.asarray(inten, dtype="<f8").tobytes()))
    con.commit()
    con.close()
    return path


def test_read_spectrum_peaks_returns_parallel_arrays_by_spectrum_id(tmp_path):
    path = _tiny_db(tmp_path, [
        (1, [100.0, 200.0], [10.0, 20.0]),
        (2, [150.0], [5.0]),
    ])
    peaks = read_spectrum_peaks(path, [1, 2])
    assert np.allclose(peaks[1][0], [100.0, 200.0])
    assert np.allclose(peaks[1][1], [10.0, 20.0])
    assert np.allclose(peaks[2][0], [150.0])


def test_read_spectrum_peaks_only_returns_requested_ids(tmp_path):
    path = _tiny_db(tmp_path, [(1, [100.0], [10.0]), (2, [150.0], [5.0])])
    assert set(read_spectrum_peaks(path, [2])) == {2}


def test_read_spectrum_peaks_raises_when_an_id_is_absent(tmp_path):
    path = _tiny_db(tmp_path, [(1, [100.0], [10.0])])
    with pytest.raises(BlobDefect, match="absent"):
        read_spectrum_peaks(path, [1, 99])


def test_read_spectrum_peaks_raises_on_mismatched_blob_lengths(tmp_path):
    path = tmp_path / "bad.db"
    con = sqlite3.connect(str(path))
    con.execute("CREATE TABLE SpectrumTable "
                "(SpectrumId INTEGER, blobMass BLOB, blobIntensity BLOB)")
    con.execute("INSERT INTO SpectrumTable VALUES (?, ?, ?)",
                (1, np.array([100.0, 200.0], dtype="<f8").tobytes(),
                 np.array([10.0], dtype="<f8").tobytes()))
    con.commit()
    con.close()
    with pytest.raises(BlobDefect, match="mismatch"):
        read_spectrum_peaks(path, [1])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_wur_spectra.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'muru.io.wur_spectra'`

- [ ] **Step 3: Implement the decoder**

Create `src/muru/io/wur_spectra.py`:

```python
"""Peak-level reader for the WUR release, and the Stage 1 mu builder.

Stage 0 read header columns only. This module reads `blobMass` and
`blobIntensity` for spectra that Stage 0 already ACCEPTED, and never
selects spectra on its own: it is handed an accepted-row table from
`wur_identity.accepted_rows` so that a rejected UVPD, off-ladder,
wrong-polarity or wrong-adduct spectrum cannot re-enter here.

Both blobs are little-endian float64 arrays of equal length. Anything else
is a defect and is raised or censused, never silently dropped.
"""
import sqlite3
from pathlib import Path

import numpy as np


class BlobDefect(ValueError):
    """A peak blob that cannot be read as a valid peak list."""


def decode_blob(blob) -> np.ndarray:
    """A little-endian float64 array from an mzVault peak blob."""
    if blob is None:
        return _fail("missing blob")
    if len(blob) == 0:
        return _fail("empty blob")
    if len(blob) % 8 != 0:
        return _fail(f"blob length {len(blob)} is not a multiple of 8")
    return np.frombuffer(bytes(blob), dtype="<f8")


def _fail(message: str):
    raise BlobDefect(message)


def read_spectrum_peaks(db_path: Path,
                        spectrum_ids) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    """Peak arrays for the requested SpectrumIds in one mzVault file.

    SpectrumId is unique per file, not across the release, so the caller
    must group its accepted rows by source file before calling this.
    """
    wanted = sorted({int(s) for s in spectrum_ids})
    if not wanted:
        return {}
    con = sqlite3.connect(str(db_path))
    try:
        placeholders = ",".join("?" * len(wanted))
        rows = con.execute(
            f"SELECT SpectrumId, blobMass, blobIntensity FROM SpectrumTable "
            f"WHERE SpectrumId IN ({placeholders})",
            wanted,
        ).fetchall()
    finally:
        con.close()

    out = {}
    for sid, blob_mz, blob_inten in rows:
        mz = decode_blob(blob_mz)
        inten = decode_blob(blob_inten)
        if mz.size != inten.size:
            raise BlobDefect(
                f"spectrum {sid} in {db_path.name}: blob length mismatch, "
                f"{mz.size} masses against {inten.size} intensities")
        out[int(sid)] = (mz, inten)

    missing = set(wanted) - set(out)
    if missing:
        raise BlobDefect(
            f"{db_path.name}: SpectrumId absent from SpectrumTable: "
            f"{sorted(missing)}")
    return out
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_wur_spectra.py -v`
Expected: PASS, 9 tests.

- [ ] **Step 5: Commit**

```bash
git add src/muru/io/wur_spectra.py tests/test_wur_spectra.py
git commit -m "wur: decode mzVault peak blobs

Little-endian float64, equal length for mass and intensity. Length
mismatch, an unreadable blob and an absent SpectrumId are raised, never
silently dropped.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 7: Build the WUR mu table against the Stage 0 accepted lineage

**Files:**
- Modify: `src/muru/io/wur_spectra.py`
- Modify: `tests/test_wur_spectra.py`

**Interfaces:**
- Consumes: `decode_blob`, `read_spectrum_peaks` from Task 6; `accepted_rows` from Task 1; `muru.spectra.Spectrum`, `muru.features.mu`; `wur_bridge_constants` from Task 5.
- Produces: `spectrum_mu(mz, intensity, precursor_mz) -> float`, `build_mu_table(accepted: pd.DataFrame, data_dir: Path) -> tuple[pd.DataFrame, list[dict]]`. The table has columns `connectivity_key, ce_numeric, mu, n_spectra, spectrum_ids, source_libraries`; the second element is the defect census.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_wur_spectra.py`:

```python
import pandas as pd

from muru.io.wur_spectra import build_mu_table, spectrum_mu


def test_spectrum_mu_is_the_intensity_weighted_normalized_mass():
    # Two peaks of equal intensity at 100 and 200, precursor 200.
    # mu = ((100 + 200) / 2) / 200 = 0.75
    assert spectrum_mu(np.array([100.0, 200.0]),
                       np.array([1.0, 1.0]), 200.0) == pytest.approx(0.75)


def test_spectrum_mu_is_one_for_a_precursor_only_spectrum():
    assert spectrum_mu(np.array([200.0]), np.array([7.0]), 200.0) == pytest.approx(1.0)


def test_spectrum_mu_sorts_unsorted_input_without_changing_the_value():
    unsorted_mu = spectrum_mu(np.array([200.0, 100.0]), np.array([1.0, 3.0]), 200.0)
    sorted_mu = spectrum_mu(np.array([100.0, 200.0]), np.array([3.0, 1.0]), 200.0)
    assert unsorted_mu == pytest.approx(sorted_mu)


def test_spectrum_mu_rejects_a_nonfinite_mass():
    with pytest.raises(BlobDefect, match="nonfinite"):
        spectrum_mu(np.array([100.0, np.nan]), np.array([1.0, 1.0]), 200.0)


def test_spectrum_mu_rejects_a_negative_intensity():
    with pytest.raises(BlobDefect, match="negative"):
        spectrum_mu(np.array([100.0, 200.0]), np.array([1.0, -1.0]), 200.0)


def test_spectrum_mu_rejects_an_unusable_precursor():
    with pytest.raises(BlobDefect, match="precursor"):
        spectrum_mu(np.array([100.0]), np.array([1.0]), 0.0)


def test_spectrum_mu_rejects_zero_total_intensity():
    with pytest.raises(BlobDefect, match="intensity"):
        spectrum_mu(np.array([100.0, 200.0]), np.array([0.0, 0.0]), 200.0)


def _accepted(rows):
    return pd.DataFrame(rows)


def _acc_row(sid, key, energy, library="WUR", precursor=200.0):
    return {"source_library": library, "source_polarity_file": "POS",
            "spectrum_id": sid, "compound_id": 1, "connectivity_key": key,
            "smiles": "CCO", "adduct": "[M+H]+", "energy": energy,
            "precursor_mass": precursor, "polarity": "+"}


def test_build_mu_table_has_one_row_per_key_and_energy(tmp_path, monkeypatch):
    db = _tiny_db(tmp_path, [(1, [100.0, 200.0], [1.0, 1.0]),
                             (2, [100.0, 200.0], [3.0, 1.0])])
    monkeypatch.setattr("muru.io.wur_spectra.LIBRARY_DB_FILES",
                        {("WUR", "POS"): db.stem})
    acc = _accepted([_acc_row(1, "AAA", 15.0), _acc_row(2, "AAA", 30.0)])
    table, census = build_mu_table(acc, tmp_path)
    assert census == []
    assert len(table) == 2
    assert set(table["ce_numeric"]) == {15.0, 30.0}
    assert table.set_index("ce_numeric").loc[15.0, "mu"] == pytest.approx(0.75)


def test_build_mu_table_takes_the_median_over_duplicate_spectra(tmp_path, monkeypatch):
    # Three deposits at the same (key, energy): mu = 1.0, 0.75, 0.625.
    # Median is 0.75, mean would be 0.7917.
    db = _tiny_db(tmp_path, [
        (1, [200.0], [1.0]),
        (2, [100.0, 200.0], [1.0, 1.0]),
        (3, [100.0, 200.0], [3.0, 1.0]),
    ])
    monkeypatch.setattr("muru.io.wur_spectra.LIBRARY_DB_FILES",
                        {("WUR", "POS"): db.stem})
    acc = _accepted([_acc_row(1, "AAA", 15.0), _acc_row(2, "AAA", 15.0),
                     _acc_row(3, "AAA", 15.0)])
    table, census = build_mu_table(acc, tmp_path)
    assert len(table) == 1
    assert table.iloc[0]["mu"] == pytest.approx(0.75)
    assert table.iloc[0]["n_spectra"] == 3


def test_build_mu_table_preserves_contributing_spectrum_ids_and_libraries(
        tmp_path, monkeypatch):
    db = _tiny_db(tmp_path, [(1, [200.0], [1.0]), (2, [100.0, 200.0], [1.0, 1.0])])
    monkeypatch.setattr("muru.io.wur_spectra.LIBRARY_DB_FILES",
                        {("WUR", "POS"): db.stem})
    acc = _accepted([_acc_row(1, "AAA", 15.0), _acc_row(2, "AAA", 15.0)])
    table, _ = build_mu_table(acc, tmp_path)
    assert table.iloc[0]["spectrum_ids"] == (("WUR", 1), ("WUR", 2))
    assert table.iloc[0]["source_libraries"] == ("WUR",)


def test_build_mu_table_censuses_a_defective_spectrum_rather_than_dropping_it(
        tmp_path, monkeypatch):
    db = _tiny_db(tmp_path, [(1, [100.0, 200.0], [1.0, 1.0]),
                             (2, [100.0, 200.0], [0.0, 0.0])])
    monkeypatch.setattr("muru.io.wur_spectra.LIBRARY_DB_FILES",
                        {("WUR", "POS"): db.stem})
    acc = _accepted([_acc_row(1, "AAA", 15.0), _acc_row(2, "BBB", 15.0)])
    table, census = build_mu_table(acc, tmp_path)
    assert len(census) == 1
    assert census[0]["connectivity_key"] == "BBB"
    assert census[0]["spectrum_id"] == 2
    assert "intensity" in census[0]["reason"]
    assert set(table["connectivity_key"]) == {"AAA"}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_wur_spectra.py -v`
Expected: FAIL with `ImportError: cannot import name 'build_mu_table'`

- [ ] **Step 3: Implement the mu builder**

Append to `src/muru/io/wur_spectra.py`:

```python
import pandas as pd

from muru.features import mu as feature_mu
from muru.io.wur_raw import LIBRARY_DB_FILES
from muru.spectra import Spectrum
from muru.wur_bridge_constants import BASE_CELL, PRECURSOR_MATCH_PPM

MU_TABLE_COLUMNS = ["connectivity_key", "ce_numeric", "mu", "n_spectra",
                    "spectrum_ids", "source_libraries"]


def spectrum_mu(mz: np.ndarray, intensity: np.ndarray,
                precursor_mz: float) -> float:
    """Base-cell `features.mu` for one peak list.

    Peaks are sorted by m/z, the declared PrecursorMass is used as the
    precursor (the WUR analogue of MassBank's MS$FOCUSED_ION), and the
    base preprocessing cell is applied through the same `Spectrum` path the
    LCSB corpus used. A nonfinite value, a negative intensity, an empty or
    all-zero peak list, or an unusable precursor raises rather than
    returning NaN, so a defect becomes a census entry upstream instead of a
    silent hole in the table.
    """
    if mz.size == 0 or intensity.size == 0:
        raise BlobDefect("empty peak list")
    if mz.size != intensity.size:
        raise BlobDefect(
            f"blob length mismatch: {mz.size} masses, {intensity.size} intensities")
    if not np.all(np.isfinite(mz)) or not np.all(np.isfinite(intensity)):
        raise BlobDefect("nonfinite value in the peak list")
    if np.any(intensity < 0):
        raise BlobDefect("negative intensity in the peak list")
    if intensity.sum() <= 0:
        raise BlobDefect("total intensity is not positive")
    if precursor_mz is None or not np.isfinite(precursor_mz) or precursor_mz <= 0:
        raise BlobDefect(f"unusable declared precursor m/z: {precursor_mz!r}")

    order = np.argsort(mz)
    spectrum = Spectrum(mz=mz[order], intensity=intensity[order],
                        precursor_mz=float(precursor_mz))
    value = feature_mu(spectrum.preprocess(ppm=PRECURSOR_MATCH_PPM, **BASE_CELL))
    if not np.isfinite(value):
        raise BlobDefect("mu is not finite")
    return float(value)


def build_mu_table(accepted: pd.DataFrame,
                   data_dir: Path) -> tuple[pd.DataFrame, list[dict]]:
    """One base-cell mu per (connectivity_key, ce_numeric), over exactly the
    spectra in `accepted`.

    Duplicate deposits at the same (key, energy) collapse by the
    preregistered aggregator, the median. The contributing spectrum ids and
    source libraries are preserved so the value is traceable to its inputs.

    Returns (table, census). A spectrum with a defect produces a census
    entry naming it and its reason; it never disappears quietly. A
    (key, energy) whose every spectrum is defective yields no row, and its
    absence is visible both in the census and in the per-energy n.
    """
    census: list[dict] = []
    per_spectrum = []

    for (library, polarity_file), grp in accepted.groupby(
            ["source_library", "source_polarity_file"], sort=True):
        stem = LIBRARY_DB_FILES[(library, polarity_file)]
        db_path = data_dir / f"{stem}.db"
        peaks = read_spectrum_peaks(db_path, grp["spectrum_id"])
        for row in grp.itertuples(index=False):
            mz, intensity = peaks[int(row.spectrum_id)]
            try:
                value = spectrum_mu(mz, intensity, row.precursor_mass)
            except BlobDefect as exc:
                census.append({
                    "connectivity_key": row.connectivity_key,
                    "ce_numeric": float(row.energy),
                    "source_library": library,
                    "spectrum_id": int(row.spectrum_id),
                    "reason": str(exc),
                })
                continue
            per_spectrum.append({
                "connectivity_key": row.connectivity_key,
                "ce_numeric": float(row.energy),
                "source_library": library,
                "spectrum_id": int(row.spectrum_id),
                "mu": value,
            })

    if not per_spectrum:
        return pd.DataFrame(columns=MU_TABLE_COLUMNS), census

    df = pd.DataFrame(per_spectrum)
    rows = []
    for (key, energy), grp in df.groupby(["connectivity_key", "ce_numeric"],
                                          sort=True):
        grp = grp.sort_values(["source_library", "spectrum_id"])
        rows.append({
            "connectivity_key": key,
            "ce_numeric": float(energy),
            "mu": float(np.median(grp["mu"].to_numpy())),
            "n_spectra": int(len(grp)),
            "spectrum_ids": tuple(zip(grp["source_library"],
                                      grp["spectrum_id"].astype(int))),
            "source_libraries": tuple(sorted(set(grp["source_library"]))),
        })
    return pd.DataFrame(rows, columns=MU_TABLE_COLUMNS), census
```

Move the `import pandas as pd` and the other new imports to the top of the file with the existing imports rather than leaving them mid-file.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_wur_spectra.py -v`
Expected: PASS, 20 tests.

- [ ] **Step 5: Commit**

```bash
git add src/muru/io/wur_spectra.py tests/test_wur_spectra.py
git commit -m "wur: build the base-cell mu table against the Stage 0 accepted lineage

build_mu_table is handed an accepted-row table rather than selecting spectra
itself, so rejected UVPD, off-ladder, wrong-polarity and wrong-adduct rows
cannot leak back in. Duplicates collapse by the preregistered median, with
contributing spectrum ids and libraries preserved. Defects are censused, not
dropped.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 8: Build population B and the per-energy gate statistics

**Files:**
- Create: `src/muru/wur_bridge.py`
- Create: `tests/test_wur_bridge.py`

**Interfaces:**
- Consumes: `wur_bridge_constants` from Task 5.
- Produces: `build_population_b(wur_dev_keys, lcsb_keys, wur_sealed_keys, lcsb_sealed_keys) -> list[str]`, `per_energy_statistics(wur_mu, lcsb_mu, population_b) -> list[dict]`, `rule_passes(stats) -> bool`.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_wur_bridge.py`:

```python
import numpy as np
import pandas as pd
import pytest

from muru.wur_bridge import (
    build_population_b, per_energy_statistics, rule_passes,
)

LADDER = [15.0, 30.0, 45.0, 60.0, 75.0, 90.0]


def _mu_frame(keys, offsets=None, energies=LADDER, seed=0):
    """A synthetic mu table: a smooth decreasing ladder per compound, with a
    per-compound level so Spearman has something to correlate."""
    rng = np.random.default_rng(seed)
    levels = {k: 0.3 + 0.6 * rng.random() for k in keys}
    rows = []
    for k in keys:
        for e in energies:
            base = levels[k] * (1.0 - 0.008 * (e - 15.0))
            rows.append({"connectivity_key": k, "ce_numeric": e,
                         "mu": base + (offsets or {}).get(e, 0.0)})
    return pd.DataFrame(rows)


def _keys(n):
    return [f"K{i:04d}" for i in range(n)]


# -- population B ----------------------------------------------------------

def test_population_b_is_the_intersection_of_wur_dev_and_lcsb_development():
    b = build_population_b({"A", "B", "C"}, {"B", "C", "D"}, set(), set())
    assert b == ["B", "C"]


def test_population_b_is_sorted_and_deduplicated():
    b = build_population_b({"C", "A", "A"}, {"A", "C"}, set(), set())
    assert b == ["A", "C"]


def test_population_b_removes_anything_sealed_on_the_wur_side():
    b = build_population_b({"A", "B"}, {"A", "B"}, {"B"}, set())
    assert b == ["A"]


def test_population_b_removes_anything_sealed_on_the_lcsb_side():
    b = build_population_b({"A", "B"}, {"A", "B"}, set(), {"A"})
    assert b == ["B"]


def test_population_b_is_empty_when_the_corpora_do_not_overlap():
    assert build_population_b({"A"}, {"B"}, set(), set()) == []


# -- per-energy statistics -------------------------------------------------

def test_statistics_cover_every_ladder_energy():
    keys = _keys(30)
    stats = per_energy_statistics(_mu_frame(keys), _mu_frame(keys), keys)
    assert [s["ce_numeric"] for s in stats] == LADDER


def test_identical_corpora_give_zero_delta_and_unit_correlation():
    keys = _keys(30)
    frame = _mu_frame(keys)
    for s in per_energy_statistics(frame, frame, keys):
        assert s["median_abs_delta"] == pytest.approx(0.0)
        assert s["median_signed_delta"] == pytest.approx(0.0)
        assert s["spearman_rho"] == pytest.approx(1.0)
        assert s["n"] == 30
        assert s["passes"] is True


def test_a_constant_offset_shows_up_as_a_signed_delta_of_that_size():
    keys = _keys(30)
    lcsb = _mu_frame(keys)
    wur = _mu_frame(keys, offsets={e: 0.09 for e in LADDER})
    for s in per_energy_statistics(wur, lcsb, keys):
        assert s["median_signed_delta"] == pytest.approx(0.09)
        assert s["spearman_rho"] == pytest.approx(1.0)
        assert s["passes"] is False


def test_n_reports_only_compounds_present_on_both_sides_at_that_energy():
    keys = _keys(10)
    lcsb = _mu_frame(keys)
    lcsb = lcsb[~((lcsb["connectivity_key"] == "K0000")
                  & (lcsb["ce_numeric"] == 45.0))]
    stats = {s["ce_numeric"]: s for s in
             per_energy_statistics(_mu_frame(keys), lcsb, keys)}
    assert stats[45.0]["n"] == 9
    assert stats[15.0]["n"] == 10


def test_statistics_ignore_compounds_outside_population_b():
    keys = _keys(10)
    frame = _mu_frame(keys)
    stats = per_energy_statistics(frame, frame, keys[:5])
    assert all(s["n"] == 5 for s in stats)


def test_an_energy_with_fewer_than_three_pairs_cannot_pass():
    keys = _keys(2)
    frame = _mu_frame(keys)
    for s in per_energy_statistics(frame, frame, keys):
        assert s["spearman_rho"] is None
        assert s["passes"] is False


def test_an_energy_passes_only_when_both_conditions_hold():
    keys = _keys(30)
    lcsb = _mu_frame(keys)
    near = _mu_frame(keys, offsets={e: 0.049 for e in LADDER})
    over = _mu_frame(keys, offsets={e: 0.051 for e in LADDER})
    assert all(s["passes"] for s in per_energy_statistics(near, lcsb, keys))
    assert not any(s["passes"] for s in per_energy_statistics(over, lcsb, keys))


def test_uncorrelated_mu_fails_even_with_a_small_median_delta():
    keys = _keys(60)
    lcsb = _mu_frame(keys, seed=1)
    wur = _mu_frame(keys, seed=2)
    stats = per_energy_statistics(wur, lcsb, keys)
    assert any(s["spearman_rho"] < 0.80 for s in stats)


# -- the 5-of-6 rule -------------------------------------------------------

def _stats(passing):
    return [{"ce_numeric": e, "passes": p} for e, p in zip(LADDER, passing)]


def test_rule_passes_on_six_of_six():
    assert rule_passes(_stats([True] * 6)) is True


def test_rule_passes_on_exactly_five_of_six():
    assert rule_passes(_stats([True, True, True, True, True, False])) is True


def test_rule_fails_on_four_of_six():
    assert rule_passes(_stats([True, True, True, True, False, False])) is False


def test_rule_fails_on_none():
    assert rule_passes(_stats([False] * 6)) is False
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_wur_bridge.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'muru.wur_bridge'`

- [ ] **Step 3: Implement population B and the statistics**

Create `src/muru/wur_bridge.py`:

```python
"""Stage 1: the cross-instrument bridge gate.

Does the same compound produce the same fragmentation trajectory on the
IQ-X as on the Q Exactive at matching NCE labels? If not, pooling the WUR
and LCSB corpora is invalid and every later result must be reported per
corpus.

Pure logic. No file IO, no artifact writing, no data-directory knowledge.
Every threshold comes from `wur_bridge_constants`, which is frozen in
MURU_WUR_REAL_DATA_PREREGISTRATION.md.
"""
from collections.abc import Iterable

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from muru.wur_bridge_constants import (
    LADDER_ENERGIES, MEDIAN_ABS_DELTA_MAX, MIN_PASSING_ENERGIES, SPEARMAN_MIN,
)

MIN_PAIRS_FOR_CORRELATION = 3


def build_population_b(wur_dev_keys: Iterable[str],
                       lcsb_dev_keys: Iterable[str],
                       wur_sealed_keys: Iterable[str],
                       lcsb_sealed_keys: Iterable[str]) -> list[str]:
    """Compounds measured on both instruments and exposed on both sides.

    Constructed operationally as an intersection of realized key sets, never
    as arithmetic on expected counts. Anything sealed on either side is
    removed, even though D3 should already keep the LCSB seal out of
    WUR-DEV: the subtraction is cheap and its being a no-op is worth
    demonstrating rather than assuming.
    """
    b = set(wur_dev_keys) & set(lcsb_dev_keys)
    b -= set(wur_sealed_keys)
    b -= set(lcsb_sealed_keys)
    return sorted(b)


def _paired(wur_mu: pd.DataFrame, lcsb_mu: pd.DataFrame,
            population_b: list[str], energy: float) -> pd.DataFrame:
    keys = set(population_b)
    w = wur_mu[(wur_mu["ce_numeric"] == energy)
               & wur_mu["connectivity_key"].isin(keys)]
    l = lcsb_mu[(lcsb_mu["ce_numeric"] == energy)
                & lcsb_mu["connectivity_key"].isin(keys)]
    return w[["connectivity_key", "mu"]].merge(
        l[["connectivity_key", "mu"]], on="connectivity_key",
        suffixes=("_wur", "_lcsb"), how="inner",
    ).sort_values("connectivity_key")


def per_energy_statistics(wur_mu: pd.DataFrame, lcsb_mu: pd.DataFrame,
                          population_b: list[str]) -> list[dict]:
    """The gate statistics at each ladder rung.

    delta_i = mu_WUR,i - mu_LCSB,i over population B compounds carrying a
    value on both sides at that energy. An energy passes when the median
    absolute delta is at most MEDIAN_ABS_DELTA_MAX and the Spearman rank
    correlation is at least SPEARMAN_MIN. An energy with fewer than three
    pairs has no defined correlation and cannot pass.
    """
    stats = []
    for energy in LADDER_ENERGIES:
        pairs = _paired(wur_mu, lcsb_mu, population_b, energy)
        n = len(pairs)
        if n == 0:
            stats.append({
                "ce_numeric": float(energy), "n": 0,
                "median_signed_delta": None, "median_abs_delta": None,
                "spearman_rho": None, "passes": False,
            })
            continue
        delta = pairs["mu_wur"].to_numpy() - pairs["mu_lcsb"].to_numpy()
        if n >= MIN_PAIRS_FOR_CORRELATION:
            rho = float(spearmanr(pairs["mu_wur"].to_numpy(),
                                  pairs["mu_lcsb"].to_numpy()).statistic)
            rho = None if np.isnan(rho) else rho
        else:
            rho = None
        median_abs = float(np.median(np.abs(delta)))
        stats.append({
            "ce_numeric": float(energy),
            "n": int(n),
            "median_signed_delta": float(np.median(delta)),
            "median_abs_delta": median_abs,
            "spearman_rho": rho,
            "passes": bool(rho is not None
                           and median_abs <= MEDIAN_ABS_DELTA_MAX
                           and rho >= SPEARMAN_MIN),
        })
    return stats


def rule_passes(stats: list[dict]) -> bool:
    """The frozen rule: both conditions on at least 5 of the 6 energies."""
    return sum(1 for s in stats if s["passes"]) >= MIN_PASSING_ENERGIES
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_wur_bridge.py -v`
Expected: PASS, 17 tests.

- [ ] **Step 5: Commit**

```bash
git add src/muru/wur_bridge.py tests/test_wur_bridge.py
git commit -m "wur: population B and the per-energy bridge-gate statistics

Population B is built operationally as an intersection of realized key
sets, never as arithmetic on expected counts. Per-energy median delta and
Spearman correlation against the frozen thresholds, with the 5-of-6 rule.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 9: Implement the frozen energy-alignment branch

`POOL_AFTER_ENERGY_ALIGNMENT` is entered only when the base rule failed through a consistent offset. The map is a monotone affine transform of the nominal energy axis, the only fitted object. PCHIP is not fitted: it is the fixed, deterministic rule for reading an already-measured six-point ladder between its own rungs. Both must be frozen before real deltas exist, since after them there is no legitimate choice of alignment method left.

**Files:**
- Modify: `src/muru/wur_bridge.py`
- Modify: `tests/test_wur_bridge.py`

**Interfaces:**
- Consumes: `per_energy_statistics`, `rule_passes` from Task 8.
- Produces: `alignment_branch_applies(stats) -> bool`, `interpolate_ladder(energies, values, targets) -> np.ndarray`, `fit_energy_map(wur_mu, lcsb_mu, population_b) -> dict`, `apply_energy_map(wur_mu, a, b) -> tuple[pd.DataFrame, int]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_wur_bridge.py`:

```python
from muru.wur_bridge import (
    alignment_branch_applies, apply_energy_map, fit_energy_map,
    interpolate_ladder,
)


def _stat(energy, signed, rho):
    return {"ce_numeric": energy, "n": 30, "median_signed_delta": signed,
            "median_abs_delta": abs(signed), "spearman_rho": rho,
            "passes": abs(signed) <= 0.05 and rho >= 0.80}


def test_branch_applies_to_a_consistent_within_tolerance_offset():
    stats = [_stat(e, 0.09, 0.95) for e in LADDER]
    assert alignment_branch_applies(stats) is True


def test_branch_does_not_apply_when_signs_disagree():
    stats = [_stat(e, 0.09, 0.95) for e in LADDER[:5]] + [_stat(90.0, -0.09, 0.95)]
    assert alignment_branch_applies(stats) is False


def test_branch_does_not_apply_when_an_offset_exceeds_the_cap():
    stats = [_stat(e, 0.09, 0.95) for e in LADDER[:5]] + [_stat(90.0, 0.16, 0.95)]
    assert alignment_branch_applies(stats) is False


def test_branch_does_not_apply_when_correlation_is_weak_anywhere():
    stats = [_stat(e, 0.09, 0.95) for e in LADDER[:5]] + [_stat(90.0, 0.09, 0.79)]
    assert alignment_branch_applies(stats) is False


def test_branch_does_not_apply_when_the_base_rule_already_passed():
    stats = [_stat(e, 0.01, 0.99) for e in LADDER]
    assert alignment_branch_applies(stats) is False


def test_branch_does_not_apply_when_an_energy_has_no_pairs():
    stats = [_stat(e, 0.09, 0.95) for e in LADDER[:5]] + [
        {"ce_numeric": 90.0, "n": 0, "median_signed_delta": None,
         "median_abs_delta": None, "spearman_rho": None, "passes": False}]
    assert alignment_branch_applies(stats) is False


# -- interpolation ---------------------------------------------------------

def test_interpolate_ladder_reproduces_the_knots_exactly():
    values = np.array([1.0, 0.9, 0.7, 0.5, 0.35, 0.25])
    out = interpolate_ladder(np.array(LADDER), values, np.array(LADDER))
    assert np.allclose(out, values)


def test_interpolate_ladder_is_monotone_between_monotone_knots():
    values = np.array([1.0, 0.9, 0.7, 0.5, 0.35, 0.25])
    targets = np.linspace(15.0, 90.0, 200)
    out = interpolate_ladder(np.array(LADDER), values, targets)
    assert np.all(np.diff(out) <= 1e-12)


def test_interpolate_ladder_never_overshoots_its_knots():
    values = np.array([1.0, 0.9, 0.7, 0.5, 0.35, 0.25])
    out = interpolate_ladder(np.array(LADDER), values,
                             np.linspace(15.0, 90.0, 200))
    assert out.max() <= values.max() + 1e-12
    assert out.min() >= values.min() - 1e-12


def test_interpolate_ladder_clamps_instead_of_extrapolating():
    values = np.array([1.0, 0.9, 0.7, 0.5, 0.35, 0.25])
    out = interpolate_ladder(np.array(LADDER), values, np.array([-5.0, 200.0]))
    assert out[0] == pytest.approx(values[0])
    assert out[1] == pytest.approx(values[-1])


# -- the map ---------------------------------------------------------------

def test_apply_energy_map_counts_cells_clamped_at_the_ladder_ends():
    keys = _keys(5)
    mapped, n_clamped = apply_energy_map(_mu_frame(keys), a=20.0, b=1.0)
    # T(90) = 110 and T(75) = 95 are above the ladder for all 5 compounds.
    assert n_clamped == 10


def test_apply_energy_map_with_the_identity_changes_nothing():
    keys = _keys(5)
    frame = _mu_frame(keys)
    mapped, n_clamped = apply_energy_map(frame, a=0.0, b=1.0)
    assert n_clamped == 0
    merged = frame.merge(mapped, on=["connectivity_key", "ce_numeric"],
                         suffixes=("_in", "_out"))
    assert np.allclose(merged["mu_in"], merged["mu_out"])


def test_fit_energy_map_recovers_a_planted_energy_shift():
    keys = _keys(40)
    # WUR is the same physics read 10 NCE units later on its own dial, so
    # LCSB at E matches WUR at E + 10: the fit should find b=1, a=+10.
    lcsb = _mu_frame(keys, seed=3)
    wur = lcsb.copy()
    wur["ce_numeric"] = wur["ce_numeric"] - 10.0
    wur = wur[wur["ce_numeric"] >= 15.0]
    # Rebuild a full ladder for WUR by interpolating its own shifted curve.
    rows = []
    for key, grp in wur.groupby("connectivity_key"):
        grp = grp.sort_values("ce_numeric")
        vals = interpolate_ladder(grp["ce_numeric"].to_numpy(),
                                  grp["mu"].to_numpy(), np.array(LADDER))
        rows += [{"connectivity_key": key, "ce_numeric": e, "mu": v}
                 for e, v in zip(LADDER, vals)]
    wur_full = pd.DataFrame(rows)
    fit = fit_energy_map(wur_full, lcsb, keys)
    assert fit["b"] == pytest.approx(1.0, abs=0.2)
    assert fit["objective"] < 0.02


def test_fit_energy_map_is_deterministic_at_the_frozen_seed():
    keys = _keys(20)
    lcsb = _mu_frame(keys, seed=5)
    wur = _mu_frame(keys, seed=5, offsets={e: 0.08 for e in LADDER})
    first = fit_energy_map(wur, lcsb, keys)
    second = fit_energy_map(wur, lcsb, keys)
    assert first["a"] == second["a"]
    assert first["b"] == second["b"]


def test_fit_energy_map_stays_inside_the_frozen_box():
    from muru.wur_bridge_constants import ALIGNMENT_A_BOUNDS, ALIGNMENT_B_BOUNDS
    keys = _keys(20)
    lcsb = _mu_frame(keys, seed=7)
    wur = _mu_frame(keys, seed=7, offsets={e: 0.12 for e in LADDER})
    fit = fit_energy_map(wur, lcsb, keys)
    assert ALIGNMENT_A_BOUNDS[0] <= fit["a"] <= ALIGNMENT_A_BOUNDS[1]
    assert ALIGNMENT_B_BOUNDS[0] <= fit["b"] <= ALIGNMENT_B_BOUNDS[1]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_wur_bridge.py -v`
Expected: FAIL with `ImportError: cannot import name 'alignment_branch_applies'`

- [ ] **Step 3: Implement the alignment branch**

Append to `src/muru/wur_bridge.py`, and add to the imports at the top:

```python
from scipy.interpolate import PchipInterpolator
from scipy.optimize import differential_evolution

from muru.wur_bridge_constants import (
    ALIGNMENT_A_BOUNDS, ALIGNMENT_B_BOUNDS, ALIGNMENT_MAXITER, ALIGNMENT_TOL,
    OFFSET_MAX, SEED,
)
```

```python
def alignment_branch_applies(stats: list[dict]) -> bool:
    """Whether the base rule failed *only* through a consistent offset.

    Every condition is read off the raw pre-alignment statistics, before any
    map is fitted. All four must hold: the base rule failed; the median
    signed delta has the same sign at every energy; its magnitude is within
    OFFSET_MAX everywhere; and the correlation is at or above SPEARMAN_MIN
    everywhere. Anything else is NO_POOL and no map is fitted at all.
    """
    if rule_passes(stats):
        return False
    signed = [s["median_signed_delta"] for s in stats]
    rhos = [s["spearman_rho"] for s in stats]
    if any(v is None for v in signed) or any(r is None for r in rhos):
        return False
    if not (all(v > 0 for v in signed) or all(v < 0 for v in signed)):
        return False
    if any(abs(v) > OFFSET_MAX for v in signed):
        return False
    return all(r >= SPEARMAN_MIN for r in rhos)


def interpolate_ladder(energies: np.ndarray, values: np.ndarray,
                       targets: np.ndarray) -> np.ndarray:
    """Read a measured ladder at arbitrary energies, by PCHIP.

    Shape-preserving piecewise cubic Hermite interpolation, knots at the
    measured energies exactly. There is no knot selection and nothing here
    is fitted: this is a deterministic readout rule for a curve that has
    already been measured, which is why it can sit alongside the fitted
    affine map without the two being the same kind of object.

    Targets outside the measured range are CLAMPED to the end knots. The
    interpolator never extrapolates.
    """
    order = np.argsort(energies)
    x, y = np.asarray(energies)[order], np.asarray(values)[order]
    interpolator = PchipInterpolator(x, y, extrapolate=False)
    clamped = np.clip(np.asarray(targets, dtype=float), x[0], x[-1])
    return interpolator(clamped)


def apply_energy_map(wur_mu: pd.DataFrame, a: float,
                     b: float) -> tuple[pd.DataFrame, int]:
    """Re-read every WUR ladder at T(E) = a + b*E, for E on the ladder.

    Returns the re-read table, keyed by the LCSB energy E it is to be
    compared at, and the number of (compound, energy) cells whose mapped
    energy fell outside the ladder and was clamped.
    """
    targets = a + b * np.asarray(LADDER_ENERGIES, dtype=float)
    n_clamped = 0
    rows = []
    for key, grp in wur_mu.groupby("connectivity_key", sort=True):
        grp = grp.sort_values("ce_numeric")
        energies = grp["ce_numeric"].to_numpy()
        values = interpolate_ladder(energies, grp["mu"].to_numpy(), targets)
        n_clamped += int(np.sum((targets < energies[0]) | (targets > energies[-1])))
        rows += [{"connectivity_key": key, "ce_numeric": float(e), "mu": float(v)}
                 for e, v in zip(LADDER_ENERGIES, values)]
    return pd.DataFrame(rows, columns=["connectivity_key", "ce_numeric", "mu"]), n_clamped


def _alignment_objective(wur_mu: pd.DataFrame, lcsb_mu: pd.DataFrame,
                         population_b: list[str], a: float, b: float) -> float:
    """Sum over the six energies of |per-energy median signed delta|.

    This targets exactly the failure the branch exists for, a consistent
    offset, rather than overall scatter, which no energy map can fix.
    """
    mapped, _ = apply_energy_map(wur_mu, a, b)
    total = 0.0
    for stat in per_energy_statistics(mapped, lcsb_mu, population_b):
        if stat["median_signed_delta"] is None:
            return float("inf")
        total += abs(stat["median_signed_delta"])
    return total


def fit_energy_map(wur_mu: pd.DataFrame, lcsb_mu: pd.DataFrame,
                   population_b: list[str]) -> dict:
    """The single monotone affine energy map T(E) = a + b*E, b > 0.

    Fitted on population B alone, which is already exposed on both sides, by
    differential evolution at the frozen seed inside the frozen box. Two
    parameters, one fit, no restarts. Deterministic.
    """
    result = differential_evolution(
        lambda p: _alignment_objective(wur_mu, lcsb_mu, population_b, p[0], p[1]),
        bounds=[ALIGNMENT_A_BOUNDS, ALIGNMENT_B_BOUNDS],
        seed=SEED, tol=ALIGNMENT_TOL, maxiter=ALIGNMENT_MAXITER, polish=True,
    )
    a, b = float(result.x[0]), float(result.x[1])
    return {
        "form": "T(E) = a + b*E, applied to the LCSB nominal energy to give "
                "the WUR nominal energy at which WUR is read",
        "a": a,
        "b": b,
        "objective": float(result.fun),
        "objective_definition": "sum over the six ladder energies of the "
                                "absolute per-energy median signed delta",
        "interpolation": "PCHIP on each compound's own six-point WUR ladder, "
                         "knots at the ladder rungs, clamped at the ends, "
                         "never extrapolated",
        "optimizer": "scipy.optimize.differential_evolution",
        "seed": SEED,
        "bounds": {"a": list(ALIGNMENT_A_BOUNDS), "b": list(ALIGNMENT_B_BOUNDS)},
        "converged": bool(result.success),
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_wur_bridge.py -v`
Expected: PASS, 32 tests.

- [ ] **Step 5: Commit**

```bash
git add src/muru/wur_bridge.py tests/test_wur_bridge.py
git commit -m "wur: freeze the energy-alignment branch

One monotone affine map T(E) = a + b*E is the only fitted object, two
parameters, differential evolution at seed 20260911 inside an a-priori box.
PCHIP is a fixed readout rule for an already-measured ladder, not a fit, and
it clamps at the ends rather than extrapolating. Branch entry is decided on
the raw pre-alignment statistics.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 10: Decide the outcome and assemble the artifact

**Files:**
- Modify: `src/muru/wur_bridge.py`
- Modify: `tests/test_wur_bridge.py`

**Interfaces:**
- Consumes: everything from Tasks 8 and 9.
- Produces: `decide(wur_mu, lcsb_mu, population_b) -> dict` returning `{"outcome", "population_b", "pre_alignment", "alignment", "post_alignment"}` with `outcome` in `{"POOL", "POOL_AFTER_ENERGY_ALIGNMENT", "NO_POOL"}`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_wur_bridge.py`:

```python
from muru.wur_bridge import decide


def test_matching_corpora_give_pool():
    keys = _keys(40)
    frame = _mu_frame(keys, seed=11)
    result = decide(frame, frame, keys)
    assert result["outcome"] == "POOL"
    assert result["alignment"] is None
    assert result["post_alignment"] is None


def test_uncorrelated_corpora_give_no_pool_and_fit_no_map():
    keys = _keys(60)
    result = decide(_mu_frame(keys, seed=21), _mu_frame(keys, seed=22), keys)
    assert result["outcome"] == "NO_POOL"
    assert result["alignment"] is None


def test_a_large_consistent_offset_gives_no_pool_without_fitting():
    keys = _keys(40)
    lcsb = _mu_frame(keys, seed=31)
    wur = _mu_frame(keys, seed=31, offsets={e: 0.40 for e in LADDER})
    result = decide(wur, lcsb, keys)
    assert result["outcome"] == "NO_POOL"
    assert result["alignment"] is None


def test_the_artifact_always_preserves_the_raw_pre_alignment_statistics():
    keys = _keys(40)
    lcsb = _mu_frame(keys, seed=41)
    wur = _mu_frame(keys, seed=41, offsets={e: 0.09 for e in LADDER})
    result = decide(wur, lcsb, keys)
    pre = {s["ce_numeric"]: s for s in result["pre_alignment"]["per_energy"]}
    assert pre[15.0]["median_signed_delta"] == pytest.approx(0.09)
    assert result["pre_alignment"]["rule_passes"] is False


def test_population_b_size_and_per_energy_n_are_reported():
    keys = _keys(40)
    frame = _mu_frame(keys, seed=51)
    result = decide(frame, frame, keys)
    assert result["population_b"]["n_compounds"] == 40
    assert [s["n"] for s in result["pre_alignment"]["per_energy"]] == [40] * 6


def test_the_rule_is_applied_at_most_once_after_alignment():
    keys = _keys(40)
    lcsb = _mu_frame(keys, seed=61)
    wur = _mu_frame(keys, seed=61, offsets={e: 0.09 for e in LADDER})
    result = decide(wur, lcsb, keys)
    if result["alignment"] is not None:
        assert result["post_alignment"] is not None
        assert result["outcome"] in {"POOL_AFTER_ENERGY_ALIGNMENT", "NO_POOL"}
        assert "per_energy" in result["post_alignment"]
        assert "rule_passes" in result["post_alignment"]


def test_decide_is_json_serializable():
    import json
    keys = _keys(20)
    frame = _mu_frame(keys, seed=71)
    json.dumps(decide(frame, frame, keys))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `pytest tests/test_wur_bridge.py -v`
Expected: FAIL with `ImportError: cannot import name 'decide'`

- [ ] **Step 3: Implement the decision**

Append to `src/muru/wur_bridge.py`:

```python
def decide(wur_mu: pd.DataFrame, lcsb_mu: pd.DataFrame,
           population_b: list[str]) -> dict:
    """The gate, applied once per branch.

    The raw pre-alignment statistics are always preserved, whether or not
    the alignment branch activates, so the artifact records what was
    actually measured and not only what survived a transform. When the
    branch does activate, the fitted map and the single permitted
    re-evaluation are both kept.
    """
    pre = per_energy_statistics(wur_mu, lcsb_mu, population_b)
    pre_passes = rule_passes(pre)
    record = {
        "outcome": None,
        "population_b": {
            "n_compounds": len(population_b),
            "connectivity_keys": list(population_b),
        },
        "pre_alignment": {"per_energy": pre, "rule_passes": pre_passes},
        "alignment": None,
        "post_alignment": None,
    }

    if pre_passes:
        record["outcome"] = "POOL"
        return record

    if not alignment_branch_applies(pre):
        record["outcome"] = "NO_POOL"
        return record

    fit = fit_energy_map(wur_mu, lcsb_mu, population_b)
    mapped, n_clamped = apply_energy_map(wur_mu, fit["a"], fit["b"])
    fit["n_clamped_cells"] = int(n_clamped)
    post = per_energy_statistics(mapped, lcsb_mu, population_b)
    post_passes = rule_passes(post)

    record["alignment"] = fit
    record["post_alignment"] = {"per_energy": post, "rule_passes": post_passes}
    record["outcome"] = "POOL_AFTER_ENERGY_ALIGNMENT" if post_passes else "NO_POOL"
    return record
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `pytest tests/test_wur_bridge.py -v`
Expected: PASS, 39 tests.

- [ ] **Step 5: Run the full test suite**

Run: `pytest tests/ -q`
Expected: no new failures against the pre-existing baseline. Record any pre-existing failures separately so they are not attributed to this work.

- [ ] **Step 6: Commit**

```bash
git add src/muru/wur_bridge.py tests/test_wur_bridge.py
git commit -m "wur: decide the bridge-gate outcome

POOL, POOL_AFTER_ENERGY_ALIGNMENT or NO_POOL, applied once per branch. The
raw pre-alignment statistics are preserved in every case, and when the
alignment branch activates the fitted map and the one permitted
re-evaluation are both kept.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

### Task 11: Wire the CLI and run the gate exactly once

**Files:**
- Create: `scripts/build_wur_bridge_gate.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: everything above.
- Produces: `artifacts/wur_bridge_gate.json`.

- [ ] **Step 1: Write the CLI**

Create `scripts/build_wur_bridge_gate.py`:

```python
"""CLI: Stage 1, the cross-instrument bridge gate.

Writes artifacts/wur_bridge_gate.json. No logic lives here -- the gate is
muru.wur_bridge and the mu builder is muru.io.wur_spectra, both of which
have their own tests. This script wires them to real files, asserts the
lineage claims that cannot be tested on synthetic input, and runs once.
"""
import json
import sys
from pathlib import Path

import pandas as pd

from muru.io import wur_raw
from muru.io.wur_census import load_annotated_trajectories
from muru.io.wur_identity import accepted_rows
from muru.io.wur_partition import (
    apply_d6, partition, sealed_scaffold_groups,
)
from muru.io.wur_provenance import canonical_key_hash, environment_provenance
from muru.io.wur_spectra import build_mu_table
from muru.synth.generators import sealed_keys
from muru.wur_bridge import build_population_b, decide
from muru.wur_bridge_constants import BASE_CELL, LADDER_ENERGIES, PRECURSOR_MATCH_PPM

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts"


def lcsb_mu_table() -> pd.DataFrame:
    """The LCSB development corpus at the base preprocessing cell.

    The corpus is asserted to be base-cell and single-valued per
    (compound, energy) rather than assumed: its lineage is checked against
    trajectories.parquet, which carries the cell columns the aggregated
    corpus drops.
    """
    dev = pd.read_parquet(ART / "p2_dev_corpus.parquet")
    dev = dev.rename(columns={"inchikey_first_block": "connectivity_key"})

    counts = dev.groupby(["connectivity_key", "ce_numeric"]).size()
    assert counts.max() == 1, \
        f"LCSB corpus has {int((counts > 1).sum())} duplicated (compound, energy) cells"

    traj = pd.read_parquet(ART / "trajectories.parquet")
    base = traj[traj["is_base_cell"]]
    assert (base["cell_relative_cutoff"] == BASE_CELL["relative_cutoff"]).all()
    assert (base["cell_include_precursor"] == BASE_CELL["include_precursor"]).all()
    assert (base["cell_intensity_transform"] == BASE_CELL["intensity_transform"]).all()

    lineage = base[base["ion_mode_raw"].str.upper() == "POSITIVE"].groupby(
        ["inchikey_first_block", "ce_numeric"])["mu"].mean()
    check = dev.set_index(["connectivity_key", "ce_numeric"])["mu"]
    shared = check.index.intersection(lineage.index)
    assert len(shared) == len(check), \
        "an LCSB corpus row has no base-cell ancestor in trajectories.parquet"
    assert (check.loc[shared] - lineage.loc[shared]).abs().max() < 1e-9, \
        "LCSB corpus mu does not reproduce the base-cell value"

    return dev[["connectivity_key", "ce_numeric", "mu"]]


if __name__ == "__main__":
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "external" / "wur"

    pre_d6 = partition(load_annotated_trajectories(data_dir))
    partitioned = apply_d6(pre_d6, sealed_scaffold_groups(pre_d6["POS"]))
    pos = partitioned["POS"]
    wur_dev_keys = set(pos.loc[pos["side"] == "WUR-DEV", "connectivity_key"])

    wur_sealed = set(json.loads(
        (ART / "wur_sealed_partition.json").read_text())["connectivity_keys"])
    lcsb = lcsb_mu_table()
    population_b = build_population_b(
        wur_dev_keys, set(lcsb["connectivity_key"]), wur_sealed, sealed_keys())

    assert not (set(population_b) & wur_sealed), "a WUR sealed key reached population B"
    assert not (set(population_b) & sealed_keys()), "an LCSB sealed key reached population B"
    print(f"Population B realized: {len(population_b)} compounds")
    if len(population_b) != 124:
        print(f"NOTE: realized population B is {len(population_b)}, not the "
              f"expected 124. Reporting the realized population.", file=sys.stderr)

    accepted = accepted_rows(wur_raw.read_all_libraries(data_dir, "POS"), "+")
    accepted_b = accepted[accepted["connectivity_key"].isin(set(population_b))]
    wur_mu, census = build_mu_table(accepted_b, data_dir)

    if census:
        print(f"HALT: {len(census)} population-B spectra carry a peak defect",
              file=sys.stderr)
        for entry in census[:20]:
            print(f"  {entry}", file=sys.stderr)
        sys.exit(1)

    for key, grp in wur_mu.groupby("connectivity_key"):
        assert set(grp["ce_numeric"]) == set(LADDER_ENERGIES), \
            f"{key}: incomplete WUR ladder after mu construction"

    result = decide(wur_mu, lcsb, population_b)
    result["stage"] = "Stage 1: cross-instrument bridge gate"
    result["preprocessing_cell"] = dict(BASE_CELL,
                                        precursor_match_ppm=PRECURSOR_MATCH_PPM)
    result["duplicate_aggregator"] = "median"
    result["wur_mu_provenance"] = {
        "n_population_b_spectra": int(accepted_b.shape[0]),
        "n_mu_cells": int(len(wur_mu)),
        "n_cells_with_duplicates": int((wur_mu["n_spectra"] > 1).sum()),
        "max_spectra_per_cell": int(wur_mu["n_spectra"].max()),
        "peak_defect_census": census,
    }
    result["population_b"]["connectivity_keys_sha256"] = canonical_key_hash(population_b)
    result["environment"] = environment_provenance(ROOT)

    (ART / "wur_bridge_gate.json").write_text(json.dumps(result, indent=2) + "\n")

    print(f"Wrote wur_bridge_gate.json")
    print(f"  OUTCOME: {result['outcome']}")
    for stat in result["pre_alignment"]["per_energy"]:
        print(f"  E{stat['ce_numeric']:>5.1f}  n={stat['n']:>3}  "
              f"median|delta|={stat['median_abs_delta']}  "
              f"signed={stat['median_signed_delta']}  "
              f"rho={stat['spearman_rho']}  passes={stat['passes']}")
```

- [ ] **Step 2: Track the artifact**

In `.gitignore`, immediately after the line `!artifacts/wur_dev_neg_keys.json`, add:

```
!artifacts/wur_bridge_gate.json
```

- [ ] **Step 3: Confirm the preregistration commit already exists**

```bash
git log --oneline --all -- MURU_WUR_REAL_DATA_PREREGISTRATION.md
```

Expected: the Task 5 freeze commit. If this is empty, STOP. No `mu` may be computed before that commit exists.

- [ ] **Step 4: Run the full test suite before the single real run**

Run: `pytest tests/ -q`
Expected: no new failures. Then specifically:

Run: `pytest tests/ -k "wur or split or leak" -v`
Expected: PASS, including the existing disjointness and leakage canaries.

- [ ] **Step 5: Run the gate, once**

Run: `PYTHONPATH=src python scripts/build_wur_bridge_gate.py`

This is the single permitted real execution. Do not re-run it to try a different setting. If it halts on the peak-defect census, that is a reportable Stage 1 finding and the fix belongs in a separate engineering commit, not in a quiet re-run.

- [ ] **Step 6: Commit the result**

```bash
git add scripts/build_wur_bridge_gate.py artifacts/wur_bridge_gate.json .gitignore
git commit -m "wur: execute Stage 1, the cross-instrument bridge gate

One run against the frozen rule. Population B built operationally as
POS WUR-DEV keys intersected with LCSB development keys, minus both seals.
Raw pre-alignment statistics preserved regardless of branch.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

- [ ] **Step 7: Report**

Report plainly: the outcome, population B's realized size, the per-energy table, the commit SHAs for the Stage 0 close-out, the preregistration freeze and the gate run, and the test results. `NO_POOL` is a valid scientific outcome and is reported as such, not treated as a defect to fix.

---

## Appendix A: preregistration text

Write this to `MURU_WUR_REAL_DATA_PREREGISTRATION.md` in Task 5, Step 5.

```markdown
# MURU WUR real-data preregistration

**Identifier:** `wur-real-data-1.0`
**Status:** FROZEN
**Supersedes:** `wfsr-external-1.0`
**Design:** `docs/superpowers/specs/2026-09-11-wur-real-data-program-design.md`
**Frozen:** before any Stage 1 `mu` was computed. See section 9.

## 1. What this document does

MURU has never run on real spectra. v1 closed with all three endpoints
failing, v2 diagnosed those failures, and the final synthetic holdout
returned strong generalization evidence, but every one of those results is a
synthetic world. This document governs the first real-data program.

It fixes, before any real value is seen: the partition rules, the Stage 1
bridge rule and every remaining degree of freedom in it, the Stage 2
adequacy fractions, the inherited thresholds, and the sealed-part floor.

A change to any numeric threshold here voids the study that used it, and
must be reported as a voided study rather than an amendment to a running
one.

## 2. What is superseded, and the drift record

`wfsr-external-1.0` froze a GNPS2 census of 909 qualifying trajectories in
551 scaffold groups, naming GNPS2 as the primary route and the WUR download
form as fallback. This program uses the Zenodo deposit instead. Both facts
are drift, recorded here, and neither is evidence about MURU.

| Quantity | `wfsr-external-1.0` | WFSR subset of this release |
|---|---|---|
| Qualifying trajectories | 909 | 947 |
| Scaffold groups | 551 | 568 |
| Route | GNPS2 primary | Zenodo deposit |

The old analysis-population floor of 400 trajectories and 200 scaffold
groups was written for an unsplit 909-trajectory population and does not
apply to a split one. It is replaced in section 6.

## 3. The realized population

The design session projected 971 positive and 222 negative qualifying
trajectories. The executed Stage 0 census differs, and the realized figures
are the ones that govern.

| Quantity | POS | NEG |
|---|---|---|
| Qualifying trajectories | 1,010 | 241 |
| Scaffold groups | 610 | 178 |
| From WFSR food safety | 947 | 220 |
| Also in LCSB development | 165 | 10 |
| Also in the LCSB seal | 41 | 1 |

Design-session figures, retained for the record and not used: 971 POS in 581
groups, 222 NEG in 160 groups.

Source: Zenodo record 20552933, WUR Mass Spectral Library v1.0, DOI
`10.5281/zenodo.20552933`, CC-BY 4.0, 203,752,342 bytes, sha256
`96fe2b1a6c5bcb441ee980b602e58f1b296af09b4eb9b99d56b92d44c03333d2`.
Retrieved once, by the project human, on 2026-09-11. Those bytes are the
frozen release. Re-downloading for a cleaner copy is prohibited; a changed
release is a drift record plus an amendment, never a silent substitution.
The `.db` files are authoritative over the `.msp` files, because only the
`.db` records the activation type.

### 3.1 Population-definition audit

The qualifying rule calls a connectivity key complete when the union of its
accepted rows covers the ladder. Before any `mu` existed, three questions
were asked about whether that union does load-bearing work:

| Question | POS | NEG |
|---|---|---|
| Qualifying keys carrying more than one inferred adduct | 0 | 0 |
| Ladders complete only when adducts are mixed | 0 | 0 |
| Ladders complete only when source deposits are unioned | 0 | 0 |

All zero. The union is inert and the modal-adduct selection is never
exercised. Recorded in `artifacts/wur_population_audit.json`.

## 4. Partition rules

Every rule is identity-based and runs before any `mu` exists. The unit is
the Bemis-Murcko scaffold group, and a scaffold group is never split across
sides.

| Rule | Statement |
|---|---|
| D1 | The unit is the scaffold group of the lexicographically first deposited SMILES per connectivity key |
| D2 | A group containing any compound in the LCSB development corpus goes to WUR-DEV. Those compounds are already exposed |
| D3 | A group containing any compound in the LCSB sealed confirmation set goes to WUR-SEALED. D3 beats D2 where they conflict |
| D4 | Remaining free groups split 50/50 at seed `20260911` |
| D5 | Negative mode is not split. All negative-mode trajectories go to WUR-DEV, and no negative-mode external claim is made |
| D6 | A row with `side == "WUR-DEV"` whose scaffold group is a positive-mode WUR-SEALED group is EXCLUDED. D6 overrides D5 |

D6 exists because D5 routes negative-mode trajectories to WUR-DEV without
consulting the scaffold-group logic D2 to D4 use, so a negative-mode
compound could sit in development while its scaffold group is sealed on the
positive side. D6 is scoped to development exposure only: it never relabels
a WUR-SEALED row, so the sealed key list and the sealed-part floor are
untouched. It is applied as a filter over the D1 to D5 result and does not
re-run the partition. It is a provable no-op on the positive side, because
D1 to D4 never split a scaffold group.

### 4.1 Realized partition, before and after D6

| Side | POS before | POS after | NEG before | NEG after |
|---|---|---|---|---|
| WUR-DEV | 606 | 606 | 241 | 209 |
| WUR-SEALED | 404 | 404 | 0 | 0 |
| EXCLUDED | 0 | 0 | 0 | 32 |
| Total | 1,010 | 1,010 | 241 | 241 |

D6 moves 32 negative-mode trajectories in 21 scaffold groups. Of those, 19
carry a connectivity key that is itself in the sealed list; the remaining 13
are scaffold-group neighbours of a sealed compound. The narrower key-level
count is recorded here so both readings are on the record; the group-level
rule is the one frozen.

Scaffold groups, POS: 335 WUR-DEV, 275 WUR-SEALED.

Artifacts: `artifacts/wur_retrieval_manifest.json`,
`artifacts/wur_identity_census.json`,
`artifacts/wur_population_audit.json`, `artifacts/wur_split_manifest.json`,
`artifacts/wur_dev_neg_keys.json`, and `artifacts/wur_sealed_partition.json`
holding connectivity keys only, tracked in git the way
`confirmation_set_sealed.json` is, so its hash is checkable.

## 5. Stage 1: the cross-instrument bridge gate

**Question.** Does the same compound produce the same fragmentation
trajectory on the IQ-X as on the Q Exactive at matching NCE labels? If not,
pooling the two corpora is invalid and every later result must be reported
per corpus.

### 5.1 Population B

Constructed operationally, never as arithmetic on expected counts:

    population B = (POS WUR-DEV connectivity keys)
                 INTERSECT (LCSB development connectivity keys)
                 MINUS (WUR sealed keys)
                 MINUS (LCSB sealed keys)

The realized size is asserted and reported. It is expected to be 124. If it
is not, the realized population is reported and used; the expected figure is
never forced. Disjointness from both seals is asserted, not assumed.

### 5.2 Endpoint

`features.mu` on both sides, at the base preprocessing cell of
`configs/preprocessing.yaml`: `relative_cutoff = 0.0`,
`include_precursor = true`, `intensity_transform = "raw"`,
`precursor_match_ppm = 10.0`.

On the WUR side, `mu` is computed only for spectra that the Stage 0 identity
gates already accepted. The accepted-row table is the single definition of
an accepted spectrum, shared by the Stage 0 trajectory builder and the
Stage 1 `mu` builder, so a rejected UVPD, off-ladder, wrong-polarity or
wrong-adduct spectrum cannot re-enter at the `mu` step. Each spectrum uses
its own declared `PrecursorMass`, the WUR analogue of MassBank's
`MS$FOCUSED_ION: PRECURSOR_M/Z`. Peaks are sorted by m/z before use.

**Duplicate resolution.** Where more than one accepted spectrum exists at
the same `(connectivity_key, energy)`, the value is the **median** of the
per-spectrum `mu`. Chosen before any real `mu` existed. The contributing
spectrum ids, source libraries and `n_spectra` are preserved for every cell.

**Defects.** A blob length mismatch, a nonfinite value, a negative
intensity, a non-positive total intensity, or an unusable declared precursor
is an explicit census entry naming the spectrum and the reason. Nothing is
silently dropped. A population-B defect halts the run.

On the LCSB side, the corpus is asserted to be the base cell, by checking
its `mu` against the base-cell rows of `trajectories.parquet`, and asserted
to carry at most one `mu` per `(connectivity_key, energy)` after the
corpus's own intended aggregation. Compounds with five rather than six
energies are reported through the per-energy `n`.

### 5.3 The rule

Per energy, over population B, with `delta_i = mu_WUR,i - mu_LCSB,i` over
compounds carrying a value on both sides at that energy:

- median `|delta|` <= **0.05**, about 1.7 times the 0.0295 inter-mixture
  repeatability SD measured in `REPEATABILITY.md`; and
- Spearman rank correlation of `mu_WUR` against `mu_LCSB` >= **0.80**.

`scipy.stats.spearmanr` with its default average-rank tie handling;
`numpy.median` for both medians. An energy with fewer than 3 pairs has no
defined correlation and cannot pass.

Both conditions must hold on at least **5 of the 6** energies.

| Outcome | Condition | Consequence |
|---|---|---|
| `POOL` | The rule passes | WUR-DEV and LCSB development are analysed as one population |
| `POOL_AFTER_ENERGY_ALIGNMENT` | The rule fails only through a consistent offset, and the re-applied rule then passes | One monotone energy map, fitted on population B alone, is carried into Stage 2 |
| `NO_POOL` | Anything else | WUR is its own population. LCSB stays separate. Stage 2 runs twice and reports both |

`NO_POOL` is a valid scientific outcome, not a failure to be repaired.

### 5.4 The alignment branch, fully specified

The branch is entered only when **all four** conditions hold, each read off
the raw pre-alignment statistics before any map is fitted:

1. the rule in 5.3 failed;
2. the median signed delta has the same sign at every one of the six
   energies;
3. its magnitude is <= **0.15** at every energy;
4. the Spearman correlation is >= 0.80 at every energy.

Otherwise the outcome is `NO_POOL` and no map is fitted.

**The map.** One monotone affine transform of the nominal energy axis,

    T(E) = a + b*E,    b > 0,

applied to the LCSB nominal energy to give the WUR nominal energy at which
WUR is read. It is the only fitted object, and it has two parameters.

**Readout.** WUR `mu` at a non-rung energy is read from that compound's own
six-point ladder by PCHIP, shape-preserving piecewise cubic Hermite
interpolation, knots at the six ladder rungs exactly. There is no knot
selection, and nothing here is fitted: PCHIP is a deterministic readout rule
for a curve that has already been measured, which is why it is not in
tension with the affine map being the fit. Every WUR qualifying trajectory
has all six rungs by construction, and this is asserted.

**End behaviour.** `T(E)` is clamped to [15, 90] before interpolation. No
extrapolation ever occurs. The number of clamped (compound, energy) cells is
counted and reported.

**Objective.** Minimize

    J(a, b) = SUM over the six ladder energies of
              | median over i of ( mu_WUR,i(T(E)) - mu_LCSB,i(E) ) |

the sum of absolute per-energy median signed deltas. This targets the
consistent offset the branch exists for, rather than scatter, which no
energy map can fix.

**Constraints and optimizer.** `a` in [-30, 30], `b` in [0.5, 2.0], both
chosen a priori as generous relative to any plausible NCE-label mismatch
between two Orbitraps. `scipy.optimize.differential_evolution`, seed
`20260911`, `tol = 1e-8`, `maxiter = 1000`, `polish = True`. Deterministic
at that seed. One fit, no restarts.

**Re-application.** The rule in 5.3 is applied to the aligned deltas exactly
once. Pass gives `POOL_AFTER_ENERGY_ALIGNMENT`; fail gives `NO_POOL`. There
is no second fit, no third pass, and no threshold change.

The raw pre-alignment statistics are preserved in the artifact whether or
not the branch activates, together with the fitted map and the single
post-alignment evaluation when it does.

**Artifact:** `artifacts/wur_bridge_gate.json`.

## 6. Inherited thresholds and floors

| Quantity | Value | Source |
|---|---|---|
| Ladder | NCE 15, 30, 45, 60, 75, 90 | The release and the LCSB corpus share it |
| Energy snap tolerance | 0.01 | Stage 0 |
| Adduct inference tolerance | 10 ppm | Stage 0 |
| Precursor match tolerance | 10 ppm | `configs/preprocessing.yaml` |
| Seed | `20260911` | Stage 0, reused |
| `ENERGY_SCALE` | 30.0 | `discovery.estimate` |
| `E_REF` | 45.0 | `rc5_adequacy` |
| Practical-win margin | 0.90 | `rc5_adequacy` |
| Minimum observed energies per compound | 5 | `rc5_adequacy` |
| Elbow tolerance | 0.01 | Frozen search settings |
| Complexity cap | 20 | Frozen search settings |
| Search seeds | 30 | Frozen search settings |
| Frozen selector | B2 family vote, R1 representative, `t1 = 0.595`, `t2 = 0.2` | `claude/muru-final-holdout-experiment-d75e7d`, not refitted |
| **Sealed-part floor** | **250 trajectories and 150 scaffold groups** | Set in the design session, blind to every `mu` |

The sealed part realizes 404 trajectories in 275 scaffold groups and clears
both floors.

## 7. Stage 2 adequacy, as fractions

`rc5_adequacy.run_case_adequacy` and the `adequacy.py` contract hard-code
exactly 30 test compounds, 24 evaluable and 20 practical wins. Against a
real population of unknown size those become fractions of the realized test
population:

- evaluable >= **0.80** of test compounds;
- practical wins >= **2/3** of evaluable compounds.

The 0.90 practical-win margin, the minimum of 5 observed energies, the
`log_g` bounds and `E_REF = 45.0` are unchanged. At N = 30 the fractions
reproduce the existing contract exactly (24/30 and 20/24), and the existing
contract tests must keep passing at N = 30.

## 8. Standing constraints

- The synthetic method is not re-tuned against real data. No threshold,
  grammar, engine setting, null or selector is chosen by watching real-data
  performance.
- The LCSB sealed confirmation set is not opened. D3 exists to protect it.
- The WUR sealed partition is not opened for any `mu` or descriptor value
  before a candidate is frozen on development.
- The post-reveal prohibition on the synthetic holdout stands. This program
  adds a real-data study; it does not reopen synthetic accuracy work.
- If the implementation fails on real data, the permitted response is to
  record the failure, fix it in a separate engineering track, and re-run.
  Patching the code against observed real-data behaviour mid-run is
  prohibited.

## 9. Disclosures

**Format probe.** While establishing that mzVault peak blobs are
little-endian float64, the peak list of one spectrum was decoded:
`WUR mass spectral library_POS_v1.db`, `SpectrumId = 1`. It resolves to
Azaperol, connectivity key `LVXYAFNPMXCRJI`, scaffold group
`c1ccc(CCCCN2CCN(c3ccccn3)CC2)cc1`, assigned **WUR-DEV**. It is not in the
sealed partition and its scaffold group is not a sealed group, so no sealed
compound was accessed, no quarantine is required, and the sealed-part floor
and key hash are unaffected. The probe read a format, not a gate statistic,
and it preceded this freeze.

**Reproducibility contract.** Both Stage 0 manifests stamp a creation time,
so whole-file byte-identity across runs is impossible by construction. The
contract is instead `connectivity_keys_sha256`, defined as the SHA-256 over
the UTF-8 bytes of the sorted connectivity keys joined by a single newline,
with no trailing newline. Re-running the Stage 0 CLI after adding
environment provenance reproduced the 404-key sealed list unchanged.

**Environment provenance.** `wur_split_manifest.json`,
`wur_sealed_partition.json`, `wur_dev_neg_keys.json` and
`wur_bridge_gate.json` each record the Python, rdkit, pandas, numpy, scipy
and pyarrow versions, the git commit that produced them, and the sha256 of
`wur_retrieval_manifest.json`. rdkit sets the scaffold groups and the
identity gate; pandas and numpy set the grouping and the medians; scipy
supplies Spearman and PCHIP; pyarrow is the parquet engine reading the LCSB
corpus.

## 10. Permission

The old WUR download form required consent before publication. The Zenodo
deposit is CC-BY 4.0, which removes that gate. The licence is the permission
basis. Confirmation with WUR is a publication-time courtesy check, not an
analysis gate.

## 11. Non-goals

UVPD spectra, stepped-energy spectra, the FCH 15 to 55 ladder,
negative-mode external claims, raw vendor files, any claim about collision
energy as a causal quantity, and any second look at the sealed part.
```

---

## Self-review

**Spec coverage.** Section 5 of the design spec is covered by Tasks 6 to 11 (population B, endpoint, rule, both branches, the artifact). Section 8 is covered by Task 5. The two Stage 0 review items are Tasks 3 and 4. The user's additional audit requirement is Task 2. The accepted-lineage requirement is Task 1, consumed in Task 7.

**Placeholders.** None. Every code step carries the code. Every test step carries the test. The preregistration is given in full in Appendix A rather than described.

**Type consistency.** `accepted_rows` (Task 1) returns the column set that `build_mu_table` (Task 7) and `audit_population` (Task 2) consume. `build_mu_table` returns `connectivity_key, ce_numeric, mu` which is exactly what `per_energy_statistics` (Task 8), `apply_energy_map` (Task 9) and `decide` (Task 10) expect, and matches the renamed LCSB frame from the CLI (Task 11). `canonical_key_hash` and `environment_provenance` (Task 4) are used with the same signatures in Tasks 4 and 11. `sealed_scaffold_groups` and `apply_d6` (Task 3) are used identically in the Stage 0 CLI (Task 4) and the Stage 1 CLI (Task 11).
