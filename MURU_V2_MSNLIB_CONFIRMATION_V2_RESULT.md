# MURU-WUR-v2 MSnLib Confirmation Study 2: Result

**Study:** `muru-v2-msnlib-confirmation-2.0`. **Decision (frozen four-way rule): MODEST EXTERNAL CONFIRMATION.**

| Record | Value |
|---|---|
| Freeze commit | `5b5afd345ce00b5dab678650d408834a63c1d888` (`refs/muru-freeze/muru-v2-msnlib-confirmation-2.0` on origin) |
| Access record commit | `e9145d3ca85c122561206d5882ceed42e2a5701e` (`refs/muru-access/...`, pushed 2026-09-14T03:32:15Z, before any decode) |
| Measurement commit | `92cf2c4592dd51ccd9ad79aba1e61e169f5f02b1` (measured mu, committed before the analysis ran) |
| Decoded | 6,004 of 6,004 frozen scans in 1,428 files (1,428 decode intents); 0 empty or non-positive spectra |
| Code at the look | identical to the freeze commit (`git diff 5b5afd3 -- scripts src artifacts/wur_v2` empty) |
| Analysis | `scripts/wur_v2_confirmation_v2/11_external_analysis.py`, unchanged, run once; output `artifacts/wur_v2_confirmation_v2/result/external_analysis.json` |

Population 2 is permanently EXPOSED. There is no third MSnLib sample, no repair and no reanalysis.

## Population

1,794 frozen compounds, all measured at both rungs (0 incomplete). 5 were excluded as outside either model's profile
support, leaving **1,789 scored compounds in 1,687 scaffold groups** (largest group 7).

## Primary endpoint (P1, pooled two-rung RMSE of mu)

| | V2_TA_MORGAN_JOINT (candidate) | V2_REF_TA_RIDGE (comparator) |
|---|---|---|
| P1 | **0.12961** | **0.13353** |
| MRMSE | 0.11214 | 0.11752 |
| Median compound RMSE | 0.09956 | 0.10752 |
| Q90 / Q95 compound RMSE | 0.20705 / 0.23151 | 0.20659 / 0.23486 |
| CVaR95 | 0.26568 | 0.26486 |
| AF (compound RMSE > 0.20) | 0.11850 | 0.11794 |
| AF_max (any rung abs error > 0.30) | 0.06205 | 0.06093 |

Whole-scaffold-group bootstrap, B = 10,000, seed 20261011, 1,687 clusters:

| Contrast | Estimate | 95% interval |
|---|---|---|
| P1 ratio (candidate / comparator) | **0.9707** | **[0.9524, 0.9893]** |
| P1 difference | -0.00392 | [-0.00644, -0.00143] |
| MRMSE difference | -0.00538 | [-0.00771, -0.00303] |
| AF difference | +0.00056 | [-0.01453, +0.01554] |

Candidate compound-level wins: 54.3%.

**Applying the frozen rule.** The ratio is below 1.00. The AF difference upper limit (+0.0155) is within the +0.03
tolerance, so the tail override does not fire. The ratio's upper 95% limit (0.9893) is below 1.00. The ratio (0.9707)
is above the 0.95 practical criterion. Result: **MODEST EXTERNAL CONFIRMATION**. The whole interval sits above 0.95,
so even its favorable end does not reach the practical criterion.

**Sensitivity (all 1,794 complete compounds, unsupported ones included):** P1 0.12947 vs 0.13336. The conclusion is
unchanged.

## Per rung (predeclared)

| Rung | Candidate RMSE | Comparator RMSE | Ratio | Mean signed residual (cand / comp) | Median abs residual (cand / comp) |
|---|---|---|---|---|---|
| NCE 20 | 0.16438 | 0.16736 | 0.982 | -0.0077 / +0.0354 | 0.1175 / 0.1240 |
| NCE 60 | 0.08111 | 0.08747 | 0.927 | +0.0033 / +0.0207 | 0.0521 / 0.0610 |

Both rungs favor the candidate, so there is no reversal. The advantage is larger at NCE 60.

At both rungs the comparator's residuals are biased positive; the candidate's mean residual is close to zero. So part
of the pooled gain is a smaller systematic offset under the zero-parameter A0 map.

## Structural novelty (secondary; interpreted because the primary confirmation holds)

Bins are the frozen quartiles of maximum Morgan-count Tanimoto similarity to the 1,325 development compounds. Q1 has
the lowest similarity, so it is the most novel.

| Bin (max similarity) | n scored | Candidate P1 | Comparator P1 | Ratio |
|---|---|---|---|---|
| Q1 [0.000, 0.281), most novel | 449 | 0.12768 | 0.12663 | **1.008** |
| Q2 [0.281, 0.319) | 462 | 0.13308 | 0.13783 | 0.966 |
| Q3 [0.319, 0.364) | 456 | 0.12678 | 0.13216 | 0.959 |
| Q4 [0.364, 1.000], least novel | 422 | 0.13082 | 0.13730 | 0.953 |

The frozen analysis gives no interval for the bins. Read descriptively:
- In the three bins more similar to the development set, the advantage is roughly uniform (0.95 to 0.97).
- In the most novel quartile it is gone (1.008).

The candidate's structural component helped where the population resembles its training chemistry. There is no
evidence that it helps for the least similar quarter of this library. This whole population is structurally distant
from development: the Q4 lower edge is only 0.364.

## Claim

Stated within protocol V2 section 2, qualified as the protocol requires:

> On an independent, scaffold-separated MSnLib screening-library population measured on a Thermo Orbitrap ID-X at fixed
> HCD NCE 20 and 60, the frozen MURU-WUR-v2 structural scale model outperformed the frozen Tier A scale comparator under
> a fixed zero-parameter deployment energy map. **This is a MODEST external confirmation:**
> - P1 is about 3% lower (ratio 0.971, 95% interval 0.952 to 0.989), short of the predeclared 0.95 practical criterion.
> - The gain is in the typical compound, not the tail (AF, Q90, Q95 and CVaR95 at parity).
> - The gain is present at both rungs.
> - There is no advantage in the most structurally novel quartile.

Not claimed: a practically meaningful improvement; tail-risk improvement; transfer to structurally novel chemistry;
universal MS/MS prediction; other instruments, adducts or negative mode; dense energy trajectories; QTOF transfer;
natural products generally; absolute cross-instrument calibration. The absolute-agreement anchor gate failed by small
margins before this study (freeze section 9) and was not revisited.

**Development versus external.** In development the P1 ratio was 0.889 (0.1160 vs 0.1305). Externally it is 0.971, so
roughly three quarters of the development advantage did not transfer. The development tail advantage (AF 6.3% vs
10.3%) did not transfer at all (11.9% vs 11.8%).

## Disclosures carried from the freeze

- **Sample 1 burned.** Confirmation sample 1 (seed 20261010) was burned before its look by an accidental
  parser-preflight decode that surfaced one mu. It was never scored, and this population replaced it.
- **Pulse signature.** The NIST pulse's RSA signature could not be verified: a 2,048-bit designated certificate
  against a 4,096-bit signature. The pulse was accepted under Amendment A-1, committed before any seed, on the exact
  timestamp, a valid outputValue, the certificateId binding and an identical canonical-URI refetch.
- **Deferred review findings.** These are unchanged (freeze section 12):
  - in-process circumvention is not prevented;
  - rung-only header indices weakly track MSn tree size;
  - co-isolation of earlier-well compounds is not excluded;
  - the guarantee relies on the GitHub remote.

## Stop

This is the final MSnLib confirmation result. The mandate forbids another MSnLib replacement sample, and no tuning,
redraw or reanalysis will follow from this outcome.
