# MURU collision-energy interface adjudication, Design A: result

Study id: `muru-ce-interface-adjudication-design-a`, governed by `MURU_CE_INTERFACE_ADJUDICATION_DESIGN_A_PREREGISTRATION.md`.
Status: EXECUTED. One look, exit 0. Written after the numerical outputs were committed.

## Verdict

**INTERFACE UNRESOLVED.**

K1, the raw NCE convention, uniquely has the highest observed composite score, so criterion 1 of the frozen rule holds. Its Bonferroni-adjusted advantage over K2 and over K3 does not lie wholly above zero, so criterion 2 fails. Under the frozen rule that is an unresolved interface, and the verdict stands exactly as written. No post-hoc rule was introduced, no re-specification was made, and no additional analysis was run on this population.

## Record chain

All refs published on `origin`:

| Step | Ref | Commit |
|---|---|---|
| Preregistration freeze | `refs/muru-freeze/muru-ce-interface-adjudication-design-a` | `518190b` |
| Pre-access record, published before any record was retrieved | `refs/muru-access/muru-ce-interface-adjudication-design-a` | `ad7b302` |
| Retrieval of the 69 records, population EXPOSED from here | | `7b7ffce` |
| Frozen predictions, determinism check PASS | `refs/muru-predictions/muru-ce-interface-adjudication-design-a` | `69449d5` |
| Scored spectra, committed before the one look | | `903e448` |
| Result | `refs/muru-result/muru-ce-interface-adjudication-design-a` | `de3a1c2` |

Execution: 69 of 69 records retrieved, every one byte-verified against its recorded MassBank git blob sha. 396 predictions, 66 per set, no empty prediction. The full prediction run was repeated independently and all twelve output files were byte-identical, which is stronger than the preregistered single-mapping check. 414 score rows, 0 dropped, all six frozen drop reasons at count zero. 33 compounds analysed in 33 molecule-level resampling units.

## Primary result

Composite untransformed full-spectrum cosine, reduced replicates then NCE cells then the two models, B = 10,000, seed 20260916, shared bootstrap weights (`0f824793ac296c6d...`).

| Mapping | Composite cosine |
|---|---|
| K1, raw NCE | **0.557070** |
| K2, NCE x m/z / 500 | 0.514752 |
| K3, floor of K2 | 0.506737 |

| Contrast | Point | 95% interval (descriptive) | Bonferroni 98.3333% (primary) | Wholly above zero |
|---|---|---|---|---|
| D12 = K1 - K2 | +0.042318 | [-0.003235, +0.088835] | [-0.012660, +0.099083] | no |
| D13 = K1 - K3 | +0.050333 | [+0.001693, +0.099972] | [-0.007439, +0.109993] | no |
| D23 = K2 - K3 | +0.008015 | [-0.009910, +0.025627] | [-0.013378, +0.029884] | no |

## Descriptive observations, none of which can change the verdict

**The direction is consistent, the precision is not sufficient.** Every descriptive cut orders the mappings the same way, K1 above K2 above K3: both models separately, both endpoints, and the pooled estimate. What fails is width, not direction. D13's ordinary 95 percent interval excludes zero while its Bonferroni-adjusted interval does not, so the multiplicity correction over three contrasts is exactly where the primary criterion is lost.

**The two models disagree in strength, not in order.**

| Contrast | ICEBERG 2.1 point, adjusted interval | GLACIER point, adjusted interval |
|---|---|---|
| K1 - K2 | +0.0736, [+0.0067, +0.1459] | +0.0110, [-0.0631, +0.0823] |
| K1 - K3 | +0.0763, [+0.0058, +0.1532] | +0.0244, [-0.0518, +0.1016] |
| K2 - K3 | +0.0027, [-0.0191, +0.0251] | +0.0134, [-0.0225, +0.0537] |

Taken alone and descriptively, ICEBERG 2.1's adjusted intervals for K1 over K2 and K1 over K3 both lie above zero, while GLACIER's straddle zero on every contrast. The composite rule is what the study preregistered, deliberately, so that the convention could not be chosen by whichever model flattered it. That choice is what produces an unresolved verdict here, and it was made before any outcome existed.

**Model ordering agreement:** no disagreement. Both order K1 > K2 > K3.

**Jensen-Shannon robustness:** same ordering, S_K1 = 0.5579, S_K2 = 0.5102, S_K3 = 0.5049. Robustness only.

**Per energy cell:** K1's advantage is carried by NCE 60 in the pooled figures (K1 0.5245 against K2 0.4782 and K3 0.4502) while at NCE 30 the three are closer (0.5896, 0.5513, 0.5633). The two models differ in where their similarity is highest: ICEBERG scores slightly higher at NCE 60 than at NCE 30 under K1, GLACIER markedly lower.

**K2 against K3 behaved as disclosed.** The preregistration stated in advance that these two differ only by the fractional part of K2 and could not plausibly separate. D23 is the narrowest contrast and is centred near zero, which is what a structurally unidentifiable contrast looks like. This was predicted before any outcome and is not a finding.

## What this result does and does not license

| Licensed | Not licensed |
|---|---|
| The statement that no convention among K1, K2 and K3 is supported by this independent population under the frozen rule | Any claim that a convention is correct, including K1, however consistent its lead |
| The descriptive observation that every cut favoured raw NCE over the documented conversion, with ICEBERG separating and GLACIER not | Any claim about relative model accuracy, or any claim about MURU, which did not participate |
| A statement that the study's own disclosed limits, small population and no null stratum, are consistent with an unresolved outcome | Recomputing, reranking or reinterpreting the closed comparator benchmark (PR #8) under any convention. It stays CLOSED and EXPOSED |
| Using this result to inform the hypothesis that a prospective Design B would test | Treating any diagnostic row of PR #8 as a confirmatory result, or starting a new MURU-against-comparator benchmark on this basis |

## Preregistered limitations that materially affect interpretation

1. **An unresolved verdict may reflect leverage, not the absence of an effect.** The preregistration recorded this in advance: 33 compounds, all scaffold-group singletons, from a single laboratory. Direction was consistent across every cut; only precision was lacking.
2. **No null stratum exists.** Exactly one of 33 compounds lies in the 450 to 550 band where K1 and K2 coincide, so the negative control that would falsify the design's own identifying assumption could not be run.
3. **K2 against K3 is structurally unidentifiable here**, as disclosed at freeze.
4. **The energy cells are NCE 30 and 60**, not MURU's frozen 20 and 60. Nothing here is a replacement external MURU benchmark.
5. **Instrument, resolution and release are confounded** in this population, and none of the three can be adjusted for independently.
6. **The evaluation grid is ms-pred's**, while GLACIER's own training hyperparameters record a grid ten times finer. The grid is applied identically to both models and all three mappings, so it cannot favour a mapping, but it is not native to GLACIER.

## Next step, not taken here

The preregistration names Design B, a prospective dense-NCE acquisition with a deliberate 450 to 550 null stratum, as the study that could resolve what this one could not. It is not executed, and it requires its own preregistration before any acquisition. This population is now exposed and may never be reused as a blind or confirmatory population.
