# Citation check results

The canonical source and the three Word manuscripts contain 34 references, numbered sequentially by first in-text appearance. The bibliography text was matched against every in-text citation in the online version. Repeated online citations use the same full reference text.

Automated checks in `validate_nhsjs.py` passed **23/23** on the final files. They verified: 240-word abstract; required sections; continuous and unique reference numbering; all 34 citations used; first-use order; 34-reference agreement between online citations and bibliography; full online citations in double parentheses; online leading spaces and superscript separators; standard superscript citations with no preceding gap; five figure captions and embedded figures; matching non-citation scientific text between standard and online versions after masking citations and author/acknowledgment details; the 9 Supporting Information table objects; exact-title Word/PDF identity; anonymous PDF Info and XMP anonymization; PDF existence; US Letter page size; standard page limit; and preserved primary measurements and limitation language.

Bibliographic formatting was normalized to the NHSJS examples, including initial-before-surname author format, sentence case for the cited article titles checked in this production pass, sequential numbering, URLs/DOIs retained, and book-title italics. The references remain the 34-source Phase 6 bibliography; this task did not re-audit source scholarship.

One limitation: project-record citations and their repository URLs are retained to preserve provenance, as requested. Those citations can reveal project ownership even though author metadata are removed from the anonymous file.
