"""Task C (completeness critic), patch 3: record the design-document and outline corrections."""
import pathlib

ROOT = pathlib.Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
P0 = ROOT / "MURU_CE_INTERFACE_ADJUDICATION_PHASE0_PROVENANCE.md"
P13 = ROOT / "MURU_CE_INTERFACE_ADJUDICATION_PHASE1_TO_3_DESIGN.md"
PRE = ROOT / "MURU_CE_INTERFACE_ADJUDICATION_PREREGISTRATION_OUTLINE_DRAFT.md"

EDITS = []


def sub(path, old, new, tag):
    EDITS.append((path, old, new, tag))


# ---------------------------------------------------------------- Phase 0 8.1: extend the confirmed list
sub(P0,
    "citations spot-checked at HEAD ed8311f (`misc_utils.py:2557`, `chem_utils.py:118-119`, `:277-283`, "
    "`:740-755`,\n`misc_utils.py:57-61`, `dag_data.py:505`, `:309-310`, `:892`, "
    "`create_msg_simulation_dataset.py:67-80`,\n`:445-450`, `glacier/dataset.py:150`, "
    "`01_assign_subformulae.py:59-66`, `predict_gen.py:146,199-203,246-252`).",
    "citations spot-checked at HEAD ed8311f (`misc_utils.py:2557`, `chem_utils.py:118-119`, `:277-283`, "
    "`:740-755`,\n`misc_utils.py:57-61`, `dag_data.py:505`, `:309-310`, `:892`, "
    "`create_msg_simulation_dataset.py:67-80`,\n`:445-450`, `glacier/dataset.py:150`, "
    "`01_assign_subformulae.py:59-66`, `predict_gen.py:146,199-203,246-252`).\n\n"
    "Corrections C-6 to C-16 land in the Phase 1 to 3 design document and the preregistration outline and are "
    "recorded in the design document's section 2.4b. The C01 numbers behind them were re-derived by "
    "`scripts/ce_interface_adjudication/c_taskc_recheck_c01.py` into the same JSON under key "
    "`C01_screen_recheck`.",
    "P0 8.1 pointer to C-6 to C-16")

# ---------------------------------------------------------------- Phase 1 to 3: record C-6 to C-13
sub(P13,
    "### 2.5 Does any public population support a clean adjudication?",
    """### 2.4b Corrections applied by the Task C completeness-critic pass

A later completeness pass re-derived the C01 screen numbers this document quotes that the screen artifacts do not
record as a named field (`scripts/ce_interface_adjudication/c_taskc_recheck_c01.py`, output under key
`C01_screen_recheck` in `artifacts/ce_interface_adjudication/counts/c_taskc_recheck.json`). No verdict changed.

| Id | What was wrong or missing | Correction |
| --- | --- | --- |
| C-6 | The document stated no evidence convention and tagged almost nothing VERIFIED or INFERRED, although Phase 0 defines and uses that convention throughout | Convention added at the head of the document, with an explicit statement that the verdicts and the recommendation are INFERRED judgements over verified counts |
| C-7 | 1.4 said "no coefficient optimized on any exposed data", weaker than X1 to X5 and than the outline, which both say "any data" | Now "any data, exposed or not" |
| C-8, C-14 | The C01 row and the outline's energy-cell section named the nine-value modal ladder as though it were the set of rungs C01 carries. C01 carries 15 distinct NCE values; the modal ladder covers 4,902 of the 5,051 records and the six off-ladder values are carried by at most 2 primary-tier compounds each (NCE 80 by 1). The screen's own verification note had repeated a truncated 12-value list, corrected there too | Full set stated in both documents, with the modal-ladder restriction named as a design choice rather than a fact about the library |
| C-9, C-10, C-16 | C02's 53-compound figure also requires NCE 20 and NCE 60, and the 37-compound EC arm is set P9 = P3 and NCE 20 and 60 and precursor range and first mass 40, not "NCE 20 to 80 complete" | Both definitions restated as verified; the 20 to 80 ladder is named as the library's modal ladder |
| C-11 | 3.4's category (4) row carried the all-source q95 of 90 in a row labelled by the MassBank ladder, and called NCE 120 and above "extrapolation on any reading" although 120, 150 and 180 are present in the training table | q95 corrected to 120 for the MassBank or MoNA arm with the all-source figure named alongside; "extrapolation" replaced by the measured sparsity, 1,205 of 18,365 rows (6.6%) |
| C-12 | "one clean compound has records from two instruments" did not say at which tier | 1 of the 112 compound-level-clean compounds, 0 in the primary, conservative and strict tiers; platform and resolution record counts added |
| C-13 | 2.5's "Tagged releases only: 33, 46, 31" gave three bare numbers in an order the reader had to infer, with no group counts | Tier order named and group counts added (conservative 33 in 33, primary 46 in 45, strict 31 in 31) |
| C-15 | The outline stated no evidence convention and did not say that its counts are carried over rather than newly measured | Convention added at its head |

Numbers this pass re-derived and CONFIRMED: the Butina cluster counts 41 (primary), 29 (conservative) and
26 (strict), which the screen artifacts record only for the pre-tautomer primary tier; the tier cascade
112 / 59 / 45 / 42 before the tautomer step and 111 / 58 / 44 / 41 after, with tagged-only 86 / 46 / 33 / 31 and
tagged conservative groups 33; the primary-tier [M+H]+ range 100.04 to 784.53 with 18 at or above 500 and the
conservative-tier 16; NCE 60 on 58 of 58 and NCE 20 on 2 of 58 primary-tier compounds; median 6 rungs inside
15 to 90; and the full peak-sparsity census (475 records, median 8, 29 at 1 peak or fewer, 92 at 3 or fewer,
NCE 15 median 2 with 21 of 59 records at 1 peak or fewer).

### 2.5 Does any public population support a clean adjudication?""",
    "P13 2.4b corrections record")

# ---------------------------------------------------------------- Outline: note the pass in section 13
sub(PRE,
    "Nothing above is frozen. No population is fixed, no criterion is declared, no split is drawn, no prediction "
    "has been generated, and no convention has been selected.",
    "Nothing above is frozen. No population is fixed, no criterion is declared, no split is drawn, no prediction "
    "has been generated, and no convention has been selected. Two corrections from the Task C "
    "completeness-critic pass are already folded in, C-14 (C01 carries 15 distinct NCE values, not the nine of "
    "the modal ladder) and C-16 (the high-mass stratum's 37 / 21 requires NCE 20 and 60 as well as the scan mode "
    "and the precursor ceiling); both are recorded in the design document's section 2.4b.",
    "PRE section 13 note")


def main():
    texts = {}
    for path, old, new, tag in EDITS:
        if path not in texts:
            texts[path] = path.read_text(encoding="utf-8")
    for path, old, new, tag in EDITS:
        t = texts[path]
        n = t.count(old)
        assert n == 1, f"{tag}: expected 1 occurrence in {path.name}, found {n}\n---\n{old[:300]}"
        texts[path] = t.replace(old, new)
        print(f"OK  {path.name}: {tag}")
    for path, t in texts.items():
        assert chr(0x2014) not in t and chr(0x2013) not in t, f"em/en dash introduced in {path.name}"
        path.write_text(t, encoding="utf-8")
        print("WROTE", path)


if __name__ == "__main__":
    main()
