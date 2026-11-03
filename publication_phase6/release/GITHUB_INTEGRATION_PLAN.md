# GitHub integration plan

Verified open draft PR chain: #10 Phase 3 targets the frozen release; #11 Phase 4 targets Phase 3; #12 Phase 5 targets Phase 4. Phase 6 is additive on the Phase 5 head and should be reviewed as a stacked draft PR targeting `publication/phase5-release-candidate`. Preserve the sequence and do not merge or force-push historical phase branches.

After owner review, the eventual integration can proceed #10 → #11 → #12 → Phase 6, or through an explicitly reviewed consolidation branch preserving all commits. No phase is merged automatically. The frozen release remains unchanged. Phase 6 adds documentation, metadata audit summaries, scripts, and publication assets; it excludes raw data and unredacted method files.
