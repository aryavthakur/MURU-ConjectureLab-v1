"""Task C (completeness critic): apply the corrections found by the re-check.

Every replacement is an exact-string swap and asserts that the old text was present exactly once,
so a silent no-op is impossible. Nothing is committed.
"""
import pathlib

ROOT = pathlib.Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
P0 = ROOT / "MURU_CE_INTERFACE_ADJUDICATION_PHASE0_PROVENANCE.md"
P13 = ROOT / "MURU_CE_INTERFACE_ADJUDICATION_PHASE1_TO_3_DESIGN.md"
PRE = ROOT / "MURU_CE_INTERFACE_ADJUDICATION_PREREGISTRATION_OUTLINE_DRAFT.md"
NOTES = ROOT / "artifacts" / "ce_interface_adjudication" / "notes"

EDITS = []


def sub(path, old, new, tag):
    EDITS.append((path, old, new, tag))


# ---------------------------------------------------------------- Phase 0, C-1: G4 unresolved arm
sub(P0,
    "Unresolved arm (n = 23,689): integers 0 to 180, 30 distinct, q05 15, median 45, q95 90",
    "Unresolved arm, MassBank or MoNA only (n = 16,464 gen train): integers 0 to 180, 30 distinct, "
    "q05 15, median 45, q95 120. The all-source category (4) gen-train arm, which additionally holds "
    "7,219 probable-MSnLib and 6 block B rows, is n = 23,689 with q95 90; that is the figure "
    "`network_ce_value_quantiles.csv` reports at `category = CAT4`, and it is NOT this row's arm",
    "C-1 G4 unresolved arm was quoting the all-source CAT4 figures in a MassBank-or-MoNA row")

# ---------------------------------------------------------------- Phase 0, C-2: the mult-of-5 subreason
sub(P0,
    "Category (4) by named subreason: MassBank or MoNA integer multiple of 5 on the ladder "
    "{15,30,35,45,60,75,90,120,150,180} 18,340;",
    "Category (4) by named subreason: MassBank or MoNA integer, nonzero multiple of 5, 18,340 (the frozen "
    "subreason is `CE % 5 == 0`, not ladder membership: 15,791 of the 18,340 sit on the "
    "{15,30,35,45,60,75,90,120,150,180} ladder that matches the implied NCE of category (2), and the other "
    "2,549 are at 5, 10, 20, 25, 40, 50, 55, 65, 70, 80 and 85);",
    "C-2 the 18,340 subreason is 'multiple of 5', not the named ten-value ladder")

# ---------------------------------------------------------------- Phase 0, C-3: ladder ambiguity in 5.5
sub(P0,
    "49,891 T_sim rows are Orbitrap integer ladder rows, of which only the 30,631 in block B are classified raw NCE.",
    "49,891 T_sim rows are Orbitrap integer rows on the MSnLib ladder {15, 20, 30, 45, 60, 75} (a different "
    "and narrower set than the ten-value MassBank ladder named in 5.3; 8,393 of them are probable-MSnLib and "
    "10,867 are MassBank or MoNA), of which only the 30,631 in block B are classified raw NCE.",
    "C-3 5.5 used 'ladder' in a second sense without saying so")

# ---------------------------------------------------------------- Phase 0, C-4: U4
sub(P0,
    "| U4 | The unit of the 18,340 MassBank or MoNA integer Orbitrap rows on the "
    "{15,30,35,45,60,75,90,120,150,180} ladder |",
    "| U4 | The unit of the 18,340 MassBank or MoNA integer Orbitrap rows whose CE is a nonzero multiple of 5 "
    "(15,791 of them on the {15,30,35,45,60,75,90,120,150,180} ladder) |",
    "C-4 U4 repeated the same ladder mischaracterisation")

# ---------------------------------------------------------------- Phase 0, C-5: per-checkpoint by-source table
sub(P0,
    "### 5.4 Per-checkpoint counts by split",
    """### 5.3b The same breakdown for `inten_contr`, the one checkpoint whose table is not T_sim

5.3 is the breakdown for `gen` and for GLACIER, whose row tables are exactly T_sim. `inten_contr` drops 12,191
rows, so its by-source-and-instrument breakdown differs and is stated separately rather than left to be inferred
from 4.2A. Source of both tables: `artifacts/ce_interface_adjudication/counts/ce_convention_counts.csv`, which
carries all three checkpoints at this granularity.

| Source library | Instrument | (1) raw NCE | (2) NCE x mz/500 | (3) other | (4) unknown | native eV | Excluded | Total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MSnLib v1.0 (construction order) | Orbitrap | 30,631 | 0 | 0 | 6 | 0 | 0 | 30,637 |
| MSnLib v1.0 | QTOF | 0 | 0 | 0 | 0 | 3 | 0 | 3 |
| MSnLib v1.0 probable (heuristic) | Orbitrap | 0 | 0 | 0 | 8,393 | 0 | 0 | 8,393 |
| MassBank or MoNA | Orbitrap | 0 | 12,135 | 14 | 18,377 | 0 | 11,767 | 42,293 |
| MassBank or MoNA | QTOF | 0 | 0 | 0 | 0 | 37,279 | 424 | 37,703 |
| GNPS | any | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Total | | 30,631 | 12,135 | 14 | 26,776 | 37,282 | 12,191 | 119,029 |

Reconciliation against 5.3: every exclusion is a MassBank or MoNA row, 11,767 Orbitrap (11,759 category (2) plus
8 category (3)) and 424 QTOF. Category (1) and category (4) are untouched, so the CE-key filter raises the raw-NCE
share of this checkpoint's Orbitrap rows from 30,631 of 81,323 (37.7%) to 30,631 of 69,556 (44.0%).

### 5.4 Per-checkpoint counts by split""",
    "C-5 added the per-checkpoint by-source-and-instrument table for inten_contr (requirement b)")

# ---------------------------------------------------------------- Phase 1 to 3, C-6: evidence convention
sub(P13,
    "Standing constraint on everything below: the closed 1,327-compound comparator benchmark was not used to "
    "choose, tune, validate or justify any item in this document, and its outcome files were never opened. "
    "No effect size, threshold or coefficient anywhere in this document derives from it.",
    "Standing constraint on everything below: the closed 1,327-compound comparator benchmark was not used to "
    "choose, tune, validate or justify any item in this document, and its outcome files were never opened. "
    "No effect size, threshold or coefficient anywhere in this document derives from it.\n\n"
    "Evidence convention, the same one Phase 0 uses: VERIFIED means read in code or data and reproduced; "
    "INFERRED means derived by argument from verified facts; UNRESOLVED means not decidable from available "
    "material. Every count in section 2 is VERIFIED against the screen artifacts under "
    "`artifacts/ce_interface_adjudication/screen/` and re-derived by the verification lens recorded in "
    "`notes/v_screen.md`, except where a cell says otherwise. Every provenance count quoted in section 1 is "
    "VERIFIED against `artifacts/ce_interface_adjudication/counts/`. The verdicts themselves (SUITABLE, PARTIAL, "
    "UNSUITABLE) and the recommendation in section 3 are INFERRED: they are judgements over verified counts, "
    "not measurements.",
    "C-6 design document carried no evidence convention and almost no VERIFIED/INFERRED tagging")

# ---------------------------------------------------------------- Phase 1 to 3, C-7: 1.4 wording
sub(P13,
    "No continuous fitted scale factor. No coefficient optimized on any exposed data.",
    "No continuous fitted scale factor. No coefficient optimized on any data, exposed or not.",
    "C-7 1.4 said 'any exposed data' where X4 and the preregistration outline say 'any data'")

# ---------------------------------------------------------------- Phase 1 to 3, C-8: C01 rung set
sub(P13,
    "403 of 415 have >= 3 distinct NCE; modal ladder 15,30,45,60,75,90,120,150,180; median 6 rungs inside 15 to 90",
    "403 of 415 have >= 3 distinct NCE; 15 distinct NCE values exist across the 5,051 records "
    "(15, 20, 25, 30, 40, 45, 50, 60, 70, 75, 80, 90, 120, 150, 180), but the modal ladder is the nine-value "
    "15,30,45,60,75,90,120,150,180 and the six off-ladder values are carried by at most 2 primary-tier "
    "compounds each (NCE 80 by 1); median 6 rungs inside 15 to 90",
    "C-8 the C01 row named the modal ladder as though it were the full rung set")

# ---------------------------------------------------------------- Phase 1 to 3, C-9: C02 P5 definition
sub(P13,
    "107 after key exclusion; 84 rows / 81 keys after scaffold exclusion; 53 within the models' precursor range; "
    "37 in the EC scan-mode arm",
    "107 rows / 104 keys after key exclusion; 84 rows / 81 keys after scaffold exclusion; 53 that additionally "
    "carry both NCE 20 and NCE 60 AND sit inside the models' precursor range; 37 of those 53 in the EC "
    "scan-mode arm",
    "C-9 the 53 figure also requires NCE 20 and 60, which the cell omitted")

# ---------------------------------------------------------------- Phase 1 to 3, C-10: EC arm description
sub(P13,
    "C02 EC arm (first-mass-40 scan mode, NCE 20 to 80 complete), 37 compounds in 21 scaffold groups, restricted "
    "to precursor m/z at or below 995.556 to stay inside the checkpoints' training precursor support.",
    "C02 EC arm (first-mass-40 scan mode, both NCE 20 and NCE 60 present, precursor m/z at or below 995.556 to "
    "stay inside the checkpoints' training precursor support), 37 compounds in 21 scaffold groups. VERIFIED "
    "definition: screen set P9 = P3 and NCE 20 and 60 and precursor range and first mass 40. The full 20 to 80 "
    "ladder is the library's modal ladder, not a verified property of all 37.",
    "C-10 'NCE 20 to 80 complete' overstated the verified P9 definition")

# ---------------------------------------------------------------- Phase 1 to 3, C-11: 3.4 unresolved arm
sub(P13,
    "| Unresolved integer ladder (category 4) | 15, 30, 35, 45, 60, 75, 90, 120, 150, 180; q05 15, median 45, "
    "q95 90 | Extending to NCE 90 stays inside the in-training integer support; 120 and above is extrapolation "
    "on any reading |",
    "| Unresolved integer arm (category 4), MassBank or MoNA | Modal ladder 15, 30, 35, 45, 60, 75, 90, 120, "
    "150, 180; presented values 0 to 180, q05 15, median 45, q95 120 (gen train, MassBank or MoNA only; the "
    "all-source category (4) arm has q95 90) | NCE 15 to 90 sits inside the arm's central 90%. NCE 120, 150 and "
    "180 are present in training but sparse, 1,205 of the 18,365 MassBank or MoNA integer Orbitrap rows (6.6%), "
    "so they are thin support rather than extrapolation |",
    "C-11 3.4 quoted the all-source q95 in a MassBank row and called in-support values extrapolation")

# ---------------------------------------------------------------- Phase 1 to 3, C-12: instrument mixing
sub(P13,
    "| Instrument platform and resolution must be balanced or blocked | C01 mixes three Orbitrap platforms and "
    "two resolution settings; one clean compound has records from two instruments |",
    "| Instrument platform and resolution must be balanced or blocked | C01's [M+H]+ records span three Orbitrap "
    "platforms under four instrument strings (Exploris 240 under two spellings 2,576 records, Q Exactive Plus "
    "623, Q Exactive 96) and two resolution settings (17,500 on 1,704 records, 15,000 on 1,591). One "
    "compound-level-clean compound has records from two instruments; none in the primary, conservative or "
    "strict tiers, so the confound is between compounds, not within them |",
    "C-12 sharpened the instrument-mixing constraint with the tier-level fact")

# ---------------------------------------------------------------- Phase 1 to 3, C-13: 2.5 tier ordering
sub(P13,
    "| How large is that population? | 44 compounds in 44 scaffold groups (conservative tier), 58 in 57 (primary "
    "tier), 41 in 41 (strict tier). Tagged releases only: 33, 46, 31. A scaffold split therefore leaves roughly "
    "10 to 20 compounds per side |",
    "| How large is that population? | 44 compounds in 44 scaffold groups (conservative tier), 58 in 57 (primary "
    "tier), 41 in 41 (strict tier). Tagged releases only, same tier order: conservative 33 in 33, primary 46 in "
    "45, strict 31 in 31. A scaffold split therefore leaves roughly 10 to 20 compounds per side |",
    "C-13 2.5 gave three bare tagged numbers in an order the reader had to guess, and omitted their group counts")

# ---------------------------------------------------------------- Preregistration outline, C-14: rung set
sub(PRE,
    "Admissible rungs are those C01 actually carries with adequate peak support, from the ladder "
    "{15, 30, 45, 60, 75, 90, 120, 150, 180}.",
    "C01 carries 15 distinct NCE values (15, 20, 25, 30, 40, 45, 50, 60, 70, 75, 80, 90, 120, 150, 180). The "
    "nine-value modal ladder {15, 30, 45, 60, 75, 90, 120, 150, 180} covers 4,902 of the 5,051 records; the six "
    "off-ladder values are each carried by at most 2 primary-tier compounds (NCE 80 by 1) and so cannot support "
    "a cell of their own. Admissible rungs are therefore those modal-ladder rungs C01 actually carries with "
    "adequate peak support; restricting to the modal ladder is a design choice and must be declared as one.",
    "C-14 the outline presented the modal ladder as the set of rungs C01 carries")

# ---------------------------------------------------------------- Preregistration outline, C-15: evidence convention
sub(PRE,
    "Companion documents: `MURU_CE_INTERFACE_ADJUDICATION_PHASE0_PROVENANCE.md` (provenance and counts), "
    "`MURU_CE_INTERFACE_ADJUDICATION_PHASE1_TO_3_DESIGN.md` (candidate conventions, feasibility, recommendation).",
    "Companion documents: `MURU_CE_INTERFACE_ADJUDICATION_PHASE0_PROVENANCE.md` (provenance and counts), "
    "`MURU_CE_INTERFACE_ADJUDICATION_PHASE1_TO_3_DESIGN.md` (candidate conventions, feasibility, recommendation).\n\n"
    "Evidence convention: every count quoted here is VERIFIED in the companion documents' artifacts and is "
    "carried over unchanged; nothing in this outline is a new measurement. Every rule, threshold, split ratio and "
    "criterion is a DRAFT PROPOSAL, not a verified fact, and section 12 lists the ones that are still open.",
    "C-15 outline had no evidence convention and no statement that its counts are carried over, not new")

# ---------------------------------------------------------------- Preregistration outline, C-16: high-mass stratum
sub(PRE,
    "| High mass | C02: CyanoMetDB EAWAG-EC arm (first-mass-40 scan mode), restricted to precursor m/z at or "
    "below 995.556 | up to 37 | up to 21 |",
    "| High mass | C02: CyanoMetDB EAWAG-EC arm (first-mass-40 scan mode, both NCE 20 and 60 present), "
    "restricted to precursor m/z at or below 995.556 | up to 37 | up to 21 |",
    "C-16 high-mass stratum definition omitted the NCE 20 and 60 requirement that produced 37 / 21")


def main():
    texts = {}
    for path, old, new, tag in EDITS:
        if path not in texts:
            texts[path] = path.read_text(encoding="utf-8")
    for path, old, new, tag in EDITS:
        t = texts[path]
        n = t.count(old)
        assert n == 1, f"{tag}: expected 1 occurrence in {path.name}, found {n}\n---\n{old[:200]}"
        texts[path] = t.replace(old, new)
        print(f"OK  {path.name}: {tag}")
    for path, t in texts.items():
        assert chr(0x2014) not in t and chr(0x2013) not in t, f"em/en dash introduced in {path.name}"
        path.write_text(t, encoding="utf-8")
        print("WROTE", path)


if __name__ == "__main__":
    main()
