# GitHub integration plan

Verified live state before Phase 5 edits: PR #10 (Phase 3 branch to frozen release) is open/draft; PR #11 (Phase 4 branch to Phase 3) is open/draft. Frozen release SHA `bfa153e828e08b3c7e674ef7fe9d6818d14a2b61`, Phase 3 head `645abb057f0f30db78d91bf82ee3445d6a31976f`, Phase 4 head `d11303161ec40eac410390d92c97e9c88010db19`. Phase 5 is additive on top of Phase 4.

Preferred review order: review/accept PR #10 into the frozen release, then PR #11 into the Phase 3 head after #10 advances, then Phase 5 into the Phase 4 head after #11 advances; alternatively maintain the stack and rebase target refs through a regular merge commit after approval. Never merge these automatically. Do not force-push prior branches or change frozen history. PR #12 should target Phase 4 and link #11 and #10 as prerequisites. Keep it draft until project-owner review and data-rights decisions are complete.

Only Phase 5 project-authored docs, scripts, aggregate tables and figures should be pushed. The Phase 4 reviewer archive contains record-level derivatives/model artifacts; it is retained locally and not newly included in the external reviewer ZIP pending rights clearance. The external package is a prepared, unsent reviewer bundle, not public release authorization.
