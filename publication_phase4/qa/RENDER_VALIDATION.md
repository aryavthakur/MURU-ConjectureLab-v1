# Word and PDF render validation

The four DOCX artifacts were rendered with the bundled `render_docx.py` into `qa/rendered/` and inspected page-by-page using page PNGs. The manuscript master and standard-citation DOCX produced 14-page PDFs; the online-citation DOCX produced 18 pages; Supporting Information produced 5 pages. The master and standard-citation versions use the same canonical source and their rendered pages are visually identical. The citation-expanded version has the same scientific content and figures but takes more pages due to the full in-text references.

Checks: no clipped figure labels, missing glyphs, blank pages, truncated tables, broken equations, or absent captions were observed. Figure 5 and its caption were kept together; the blue title rule was removed; inline code backticks are not emitted as literal markup. Page numbers are consistent. At 12 pt the main text fits within the requested 20-page limit. The main manuscript is 14 pages after keeping the Figure 5 caption with its figure.

Render command pattern:

```sh
PYTHONPATH=/tmp/muru-phase4-python-deps python3.13 /Users/aryav/.codex/plugins/cache/openai-primary-runtime/documents/26.1026.10807/skills/documents/render_docx.py INPUT.docx --output_dir OUTPUT_DIR
```

The intermediate render PNGs/PDFs are retained for audit in `qa/rendered/`.

Visual inspection covered all 14 master pages, all 18 online-citation pages, all 5 Supporting Information pages, and the 14 standard-citation pages (the latter were pixel-identical to the master). Figure 5 and its caption now begin together on page 10; page 9 retains the preceding comparator text and Figure 3 without overlap. Inline citation references in the online version contain no raw Markdown backtick characters.
