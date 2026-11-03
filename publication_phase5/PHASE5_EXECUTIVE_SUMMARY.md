# Phase 5 executive summary

Phase 5 consolidates the Phase 4 research record into a release candidate and corrects a consequential energy-description conflict. The live repository was at the verified Phase 4 commit; PR #10 and PR #11 remain open drafts. The frozen release branch and prior phase branches were left unchanged.

The primary external result is preserved exactly. Among 1,789 scored MSnLib compounds from 1,794 measured (five support exclusions; 1,687 scaffolds), MURU’s pooled P1 RMSE was 0.1296115107 versus 0.1335276112 for the Tier A reference. The ratio was 0.9706719801 (95% whole-scaffold bootstrap interval 0.9523611880–0.9892672062), a 2.9328% reduction. The interval is below one but above the practical target 0.95. Tail-risk improvement was not demonstrated; the least-similar quartile ratio was about 1.0083.

Phase 5 surfaced a direct disagreement that Phase 4 did not resolve: the frozen project protocol calls MSnLib’s selected numeric values NCE 20/60, while the peer-reviewed MSnLib article says its ID-X MS2 method used 20/60 eV. The nine evaluated source archives lack native method files to decide which description applies. The A0 adapter also assumes ID-X NCE equals IQ-X NCE, and the prespecified absolute-agreement anchor gate failed at A0, A1, and A2. Phase 5 narrows the claim to a numerical model comparison under the frozen adapter and does not claim calibrated physical energy transfer.

Phase 5 also discloses that development amendment A-3 restated permutation-control criterion c4 after development outcomes and review diagnostics were visible, but before external outcomes were accessed. The original literal criterion failed for EXP08B; it was admitted under the revised rule. Frozen candidate and outcomes remain unchanged.

The Phase 4 PDF page-count discrepancy is reconciled: master and standard-citation versions are 14 pages, online-citation version 19, supplement 6. The manuscript is 236 whitespace-delimited words in the abstract and has 29 references.

A separate external-review packet, source-based candidate shortlist, and unsent outreach drafts are prepared. No human expert review has yet occurred. The reviewer reproduction package reproduces statistics and figures from frozen outputs, not raw mzML processing or retraining. The external share package excludes per-compound predictions and model artifacts pending rights confirmation.
