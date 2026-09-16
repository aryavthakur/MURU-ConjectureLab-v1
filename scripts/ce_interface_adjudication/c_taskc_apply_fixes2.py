"""Task C (completeness critic), patch 2: record the corrections in Phase 0 and in the supporting notes.

Part 1 of notes/q_counts.md (the frozen classification rule, sha256 c5ab93af...) is NOT touched; only Part 2
prose and an appended Part 3 are affected, which is the same regime under which Part 2 was written.
"""
import pathlib

ROOT = pathlib.Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
P0 = ROOT / "MURU_CE_INTERFACE_ADJUDICATION_PHASE0_PROVENANCE.md"
NOTES = ROOT / "artifacts" / "ce_interface_adjudication" / "notes"
QC = NOTES / "q_counts.md"
VC = NOTES / "v_counts.md"
VS = NOTES / "v_screen.md"

EDITS = []


def sub(path, old, new, tag):
    EDITS.append((path, old, new, tag))


# ---------------------------------------------------------------- Phase 0: record the Task C pass
sub(P0,
    "Screen-level corrections are applied in the Phase 1 to 3 design document, section 2.",
    """Screen-level corrections are applied in the Phase 1 to 3 design document, section 2.

### 8.1 Corrections applied by the Task C completeness-critic pass

Re-check script: `scripts/ce_interface_adjudication/c_taskc_recheck_numbers.py`; output
`artifacts/ce_interface_adjudication/counts/c_taskc_recheck.json`. It recomputes, from the same metadata
parquets the frozen classifier used, exactly those document-level numbers that are NOT a named field of the
counts artifacts, so they can be confirmed or refuted without trusting the prose. Patch script:
`scripts/ce_interface_adjudication/c_taskc_apply_fixes.py`, each edit an exact-string swap asserted to match
once. No count in `counts/` changed and no classifier was re-run; these are description errors, not count errors.

| Id | What was wrong | Correction |
| --- | --- | --- |
| C-1 | 4.2B row G4 is keyed to (gen, MassBank or MoNA, Orbitrap) but its "Unresolved arm" cell quoted n = 23,689 with q95 90, which is the ALL-source category (4) gen-train row of `network_ce_value_quantiles.csv` | The MassBank or MoNA Orbitrap unresolved arm is n = 16,464 (16,452 integer rows plus the 12 CE 80.205 rows), 30 distinct presented values, 0 to 180, q05 15, median 45, q95 120. Both figures are now stated, each labelled |
| C-2 | 5.3 and U4 described the 18,340 rows as being "on the {15,30,35,45,60,75,90,120,150,180} ladder". The frozen subreason is `mbmona_integer_mult5`, defined at `03_classify_ce_conventions.py:268` as integer and `CE % 5 == 0` and CE non-zero, with no ladder test | 15,791 of the 18,340 are on that ladder; 2,549 are at 5, 10, 20, 25, 40, 50, 55, 65, 70, 80 and 85. Both places corrected. The count 18,340 is unchanged and correct |
| C-3 | 5.5's "49,891 T_sim rows are Orbitrap integer ladder rows" uses `ladder` for the MSnLib set {15,20,30,45,60,75}, two paragraphs after 5.3 named a different ten-value ladder | The set is now named explicitly, with its 8,393 probable-MSnLib and 10,867 MassBank or MoNA parts. 49,891 is unchanged and correct |
| C-5 | The document gave a by-source-and-instrument table only for T_sim (that is, for `gen` and GLACIER) and a per-checkpoint table only by split, so `inten_contr`'s by-source-and-instrument breakdown had to be assembled by the reader from 4.2A | Added as 5.3b, taken from `ce_convention_counts.csv`, which already carried all three checkpoints at that granularity |

Numbers that the pass re-derived and CONFIRMED, listed because a critic's silence is not evidence: the whole of
5.2, 5.3 and 5.4 against `ce_convention_counts.json` (every cell); 49,891 and the 30,631 to 49,891 bracket; the
Orbitrap 81,323 / QTOF 37,706 split; the 5.4 validation-against-training composition (70.5 / 10.8 / 18.7 against
29.4 / 34.0 / 36.6, both reproduced to the stated decimal); the 4.2B presented-value quantiles for G1, G2, G4's
converted arm and GLACIER's H_raw arm (8,831 distinct, 2.052 to 358.400, median 26.891); section 3's register
totals (457 lines, 367,533,450 bytes, largest 49,520,118, every task-tag count) and its Hugging Face range
accounting; section 6's embedding distances, near-alias minima and band shares; and the ms-pred file:line
citations spot-checked at HEAD ed8311f (`misc_utils.py:2557`, `chem_utils.py:118-119`, `:277-283`, `:740-755`,
`misc_utils.py:57-61`, `dag_data.py:505`, `:309-310`, `:892`, `create_msg_simulation_dataset.py:67-80`,
`:445-450`, `glacier/dataset.py:150`, `01_assign_subformulae.py:59-66`, `predict_gen.py:146,199-203,246-252`).""",
    "P0 8.1 corrections record")

# ---------------------------------------------------------------- q_counts.md Part 2 prose
sub(QC,
    "- (4) Integer values 0-180 whose unit is not recoverable per row; 18,340 of all 26,776 are MassBank/MoNA "
    "multiples of\n  5 on the 15/30/35/45/60/75/90/120/150/180 ladder that matches the implied NCE of category "
    "(2) rows (INFERRED mostly\n  NCE); 8,393 are probable MSnLib NCE.",
    "- (4) Integer values 0-180 whose unit is not recoverable per row; 18,340 of all 26,776 are MassBank/MoNA\n"
    "  non-zero multiples of 5 (the subreason's actual definition), of which 15,791 sit on the\n"
    "  15/30/35/45/60/75/90/120/150/180 ladder that matches the implied NCE of category (2) rows (INFERRED mostly\n"
    "  NCE) and 2,549 are at 5/10/20/25/40/50/55/65/70/80/85; 8,393 are probable MSnLib NCE.\n"
    "  [Corrected 2026-09-15 by the Task C completeness-critic pass; see Part 3. The count 18,340 is unchanged.]",
    "q_counts Part 2 ladder description")

# ---------------------------------------------------------------- v_counts.md B5
sub(VC,
    "- B5. All 18,365 MassBank/MoNA integer Orbitrap rows stay CAT4, including the 18,340 multiples of 5 that sit "
    "on the\n  same ladder as the implied NCE of the converted rows.",
    "- B5. All 18,365 MassBank/MoNA integer Orbitrap rows stay CAT4, including the 18,340 non-zero multiples of 5,\n"
    "  15,791 of which sit on the same ladder as the implied NCE of the converted rows (the other 2,549 are at\n"
    "  5/10/20/25/40/50/55/65/70/80/85). [Ladder clause corrected 2026-09-15 by the Task C completeness-critic\n"
    "  pass; the check and its counts are unchanged.]",
    "v_counts B5 ladder clause")

# ---------------------------------------------------------------- v_screen.md CE value set
sub(VS,
    "- CE string form: **5,051 / 5,051 are `N % (nominal)`**; 0 ramp, stepped, list or eV strings; the\n"
    "  distinct values are {15,20,25,30,40,45,50,60,70,120,150,180} % (criterion 5).",
    "- CE string form: **5,051 / 5,051 are `N % (nominal)`**; 0 ramp, stepped, list or eV strings; the\n"
    "  distinct values are **{15,20,25,30,40,45,50,60,70,75,80,90,120,150,180} %**, 15 of them (criterion 5).\n"
    "  [Corrected 2026-09-15 by the Task C completeness-critic pass: this line previously listed 12 values, which\n"
    "  was the truncated `ce_raw_examples` field of `v_part1.json` (a first-12 slice), not the full set. It\n"
    "  omitted 75, 80 and 90 and so contradicted this same section's \"median 6 rungs in 15-90\" and\n"
    "  \"NCE 60 present for 59/59\". Record counts over all 5,051: 15 682, 20 29, 25 30, 30 678, 40 29, 45 625,\n"
    "  50 24, 60 631, 70 20, 75 573, 80 17, 90 527, 120 465, 150 386, 180 335. No verdict or tier count changes.]",
    "v_screen C01 CE value set")


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

    # append Part 3 to q_counts.md
    q = texts[QC]
    assert "## Part 3." not in q
    q += """

## Part 3. Corrections from the Task C completeness-critic pass (2026-09-15)

Part 1 (the frozen classification rule) is unchanged and its recorded freeze hash still refers to the file as it
stood at 2026-09-15T03:18:59Z. This part records description errors found in Part 2 after the fact. No count in
`artifacts/ce_interface_adjudication/counts/` changed and the classifier was not re-run.

1. Section 2.6's category (4) bullet described the 18,340 `mbmona_integer_mult5` rows as lying on the
   15/30/35/45/60/75/90/120/150/180 ladder. The subreason as implemented and as frozen in Part 1 section 1.3 is
   integer and `CE % 5 == 0` and CE non-zero, with no ladder test. Recomputed: 15,791 on that ladder, 2,549 off
   it at 5/10/20/25/40/50/55/65/70/80/85. Corrected in place above. The synthesis document repeated the error in
   two places and is corrected there as C-2.
2. Recomputation script for both figures: `scripts/ce_interface_adjudication/c_taskc_recheck_numbers.py`, output
   `artifacts/ce_interface_adjudication/counts/c_taskc_recheck.json` (key `C1_mbmona_integer_mult5`).
3. The same pass re-derived the MassBank-or-MoNA-only gen-train category (4) arm, which section 2.6 does not
   report separately: n = 16,464, 30 distinct presented values, 0 to 180, q05 15, median 45, q95 120. Section
   2.6's own all-source figures are unaffected; the synthesis document had attributed the all-source figures to a
   MassBank-or-MoNA row and is corrected there as C-1.
"""
    texts[QC] = q
    print("OK  q_counts.md: appended Part 3")

    for path, t in texts.items():
        assert chr(0x2014) not in t and chr(0x2013) not in t, f"em/en dash introduced in {path.name}"
        path.write_text(t, encoding="utf-8")
        print("WROTE", path)


if __name__ == "__main__":
    main()
