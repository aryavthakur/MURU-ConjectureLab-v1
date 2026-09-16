"""Task C (completeness critic), patch 4: flag the one C06 figure that cannot be traced to an artifact."""
import pathlib

ROOT = pathlib.Path("/Users/aryav/Documents/MURU-ConjectureLab-v1/.claude/worktrees/muru-ce-interface-adjudication")
P13 = ROOT / "MURU_CE_INTERFACE_ADJUDICATION_PHASE1_TO_3_DESIGN.md"

OLD = ("| 55 (of 689 deposited and identified) | 55, all singletons; 16 under the conservative full-registry "
       "exclusion | 1 |")
NEW = ("| 55, all singletons (UNTRACED denominator: 55 is tier M5 of `c06_screen_summary.json`, whose universe is "
       "1,007 rows / 987 keys, while 689 is the deposited-and-identified key count of the `v_screen` and addendum "
       "universe of 698 rows; the two are not the same base) | 55; and 16 under the conservative full-registry "
       "exclusion, which is UNTRACED: the artifacts hold tier T5 = 15 keys / 15 groups on the 987-key universe "
       "and `v_partials.json` holds 22 on a cascade without the raw-file criterion, neither of which is 16. "
       "Immaterial to any verdict or recommendation, since criterion 8 already fails on a single energy | 1 |")


def main():
    t = P13.read_text(encoding="utf-8")
    assert t.count(OLD) == 1, t.count(OLD)
    t = t.replace(OLD, NEW)

    anchor = ("| C-15 | The outline stated no evidence convention and did not say that its counts are carried over "
              "rather than newly measured | Convention added at its head |")
    assert t.count(anchor) == 1
    t = t.replace(anchor, anchor + "\n| C-17 | C06's compound counts could not be traced: \"55 (of 689)\" takes "
                                   "numerator and denominator from two different screen universes (1,007 rows / "
                                   "987 keys against 698 rows / 689 keys), and no artifact holds a 16-member C06 "
                                   "set. This is the same class of defect the verification lens already found in "
                                   "C06 criterion 1 (\"90 of 689\", correctly 94) | NOT FIXED, flagged in place. "
                                   "The numbers are left as the screen wrote them and marked UNTRACED rather than "
                                   "replaced by a guess. C06 is PARTIAL_OR_SUPPORTING_ONLY on criterion 8 (a "
                                   "single energy), which no compound count can change |")
    assert chr(0x2014) not in t and chr(0x2013) not in t
    P13.write_text(t, encoding="utf-8")
    print("WROTE", P13)


if __name__ == "__main__":
    main()
