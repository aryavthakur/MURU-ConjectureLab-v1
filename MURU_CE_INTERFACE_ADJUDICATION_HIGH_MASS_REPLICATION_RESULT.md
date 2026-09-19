# CE interface adjudication: C02 high-mass replication, RESULT

Written after result commit `75a5936`. Numbers are from `artifacts/ce_interface_adjudication/high_mass/result/analysis.json`; `60_analysis.py` ran exactly once.

## Verdict

**HIGH_MASS_SUPPORTS_K1.** Mean compound-level S_K1 - S_K2 (cosine) = **+0.0755**, 95% bootstrap interval
**[+0.0411, +0.1111]**, n = 32 compounds (= 32 scaffold groups), B = 10,000, seed 20260920. 25 of 32 compounds
favour K1.

Composite cosine: K1 0.3960, K2 0.3205, K3 0.3268. Mechanically complete: 2,184 score rows, 0 drops.

## Chain

Scope closure fd2cd3b -> metadata stage 9dc298b -> freeze 376ab65 (`refs/muru-freeze/muru-ce-interface-high-mass-replication`)
-> access record 4d3df86 (`refs/muru-access/...`, published before retrieval) -> retrieval (364/364, all blob shas
verified) -> predictions (`refs/muru-predictions/...`, 6 x 224 cells) -> scores and input manifest 7e0c1ba -> result 75a5936.

## Descriptive only (never decisional)

| Cut | K1 - K2 |
|---|---|
| ICEBERG 2.1 | +0.0878 [+0.0485, +0.1289] |
| GLACIER | +0.0632 [+0.0258, +0.1015] |
| JS robustness | +0.0671 [+0.0393, +0.0963] (same verdict if applied) |
| K1 - K3 | +0.0692 [+0.0354, +0.1052] |
| K2 - K3 | -0.0063 [-0.0144, +0.0013] |
| NCE 15 / 20 / 25 / 30 / 40 / 50 / 60 | +0.178 / +0.178 / +0.044 / +0.026 / -0.027 / +0.047 / +0.083 |
| Level 1 (12) / 2a (6) / 2b (14) | +0.068 / +0.081 / +0.080 |
| EAWAG EC+ED (19) / MLU-ED (10) | +0.089 / +0.032 |
| [M+H]+ < 500 (3) / 500-700 (9) / 700-900 (14) / 900-1000 (6) | +0.042 / +0.028 / +0.110 / +0.084 |

Both models order K1 > K3 > K2. Unlike Design A, GLACIER separates K1 from K2 here as well.

## Interpretation, within the preregistered constraints

In Design A most compounds sat below m/z 500, so K1 was the numerically HIGHER CE input, and K1 led
(descriptively). Here 29 of 32 compounds sit above 500, so K1 is the numerically LOWER input, and K1 again
leads, now with an interval clear of zero and agreement across both models, JS and every identity tier. The
K1 preference therefore does not follow a generic preference of the checkpoints for lower or higher CE
numbers. This is consistent with the checkpoints treating raw NCE as their collision-energy input.

Limits: one chemical class (cyanobacterial peptides and related metabolites), mostly Level 2 identities and
crude-extract spectra, and the advantage sits mainly at NCE 15 to 20 (NCE 40 is slightly negative). This is a
high-mass replication, not a universal interface proof, not a MURU-vs-comparator benchmark and not a
replacement for the cancelled Design B. Design A remains formally INTERFACE UNRESOLVED. PR #8 is not
recomputed under any convention. The C02 population is now EXPOSED and may not be reused as a blind population.

Not done: Design A's full-rerun byte-determinism check of the predictions was not repeated for this study.
