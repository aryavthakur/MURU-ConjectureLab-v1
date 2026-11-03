# Manuscript integrity checks

Reusable checker: `run_integrity_checks.py`. It reads the canonical Markdown source and generated Word documents, and fails on violations rather than relying on filenames alone.

Checks cover: abstract word count; required sections; unique/contiguous reference IDs; citation resolution; figure file presence and in-text use; Supporting Information presence; placeholder scan; prohibited accuracy-percentage wording; source-derived population/metric anchors; the failed 5% criterion; adverse tail and novelty findings; energy-interface caveat; unreproduced development interval; comparator endpoint scope; and the primary values/reference list in all three manuscript DOCX files. The source SHA-256 is written to `CANONICAL_SOURCE_SHA256.txt`.

The final run is recorded in `FINAL_TEST_RESULTS.md`. Visual rendering is recorded separately in `RENDER_VALIDATION.md`; this script does not replace page inspection.
