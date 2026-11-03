# Simulated Reviewer A: Analytical Chemistry and Mass Spectrometry

**Status:** Internal adversarial review generated for Phase 4. This is not a human peer review or an expert signoff.

## Overall assessment

The revision is substantially more cautious than the Phase 3 draft and correctly distinguishes the scalar μ endpoint from complete MS/MS prediction. It now states that the empirical energy bridge is not a physical calibration, preserves the exposed-sample history, and corrects the comparator’s endpoint description. Those are important improvements.

The paper is potentially interpretable as a computational comparison of μ predictions under a fixed numerical interface. Two method details still need correction before this can be described as a chemically coherent energy-dependent endpoint comparison: (1) the precursor-mass denominator is supplied differently in WUR development and MSnLib evaluation, and (2) the Methods says the 10-ppm precursor matching tolerance is part of μ preprocessing although the target calculation includes the full peak list and does not invoke that tolerance. The public-comparator energy label also needs to distinguish FIORA’s native input from the mapped ICEBERG/GLACIER inputs.

## Major concerns

### A1. The precursor denominator is not specified consistently across development and external data

**Location:** Methods §2.3, especially “theoretical protonated precursor mass `m_prec`” and “The theoretical [M+H]+ mass was used.”

**Evidence:** In the WUR processing route, `src/muru/wur_v2/spectra.py` passes `r.precursor_mass` to `spectrum_quantities`; that value is read from the MassBank `PRECURSOR_M/Z` field in the WUR raw-record parser (`src/muru/io/wur_spectra.py`). In the MSnLib route, `scripts/wur_v2_confirmation_v2/10_one_look.py` builds `mh` from the population structure records and passes `mh[r.key]` to `external_multims2.spectrum_mu`. Thus the external denominator is structure-derived [M+H]+, whereas the development denominator is the source record’s declared precursor m/z. Those may be close, but they are not methodologically identical by definition.

**Why it matters:** The same symbolic equation can describe both, but the text currently suggests one common theoretical denominator. Any denominator difference can change μ at a small scale and is relevant to transfer across collections. The paper should not imply denominator identity without checking it.

**Required correction:** Explicitly state the source of `m_prec` for each collection. If the frozen population records allow it, compare structure-derived [M+H]+ with WUR declared precursor m/z and report the observed discrepancy range or an appropriate summary. Otherwise state that the denominator provenance differs and that the transfer comparison includes this endpoint implementation difference. Do not overwrite the frozen measured outcomes.

### A2. The stated 10-ppm tolerance does not affect μ under the frozen base cell

**Location:** Methods §2.3: “After the frozen base preprocessing (zero relative-intensity cutoff, precursor included, raw intensities, and 10-ppm precursor-match tolerance)…”

**Evidence:** `src/muru/wur_bridge_constants.py` sets `relative_cutoff=0.0`, `include_precursor=True`, and `intensity_transform='raw'`. In `Spectrum.preprocess`, the tolerance is consulted only if precursor removal is requested. `src/muru/features.py::mu` then calculates the normalized intensity-weighted first moment over the peaks it receives. The 10-ppm match is used for auxiliary quantities such as precursor survival and mass ratio, but not to filter the peak list when calculating μ.

**Why it matters:** The current prose makes precursor matching sound like a target-defining operation. That would invite a reader to assume that the observed precursor was explicitly identified or adjusted before calculating μ.

**Required correction:** Describe the μ preprocessing as no intensity cutoff, precursor not removed, and raw intensities. State that the 10-ppm criterion is used by auxiliary precursor-matching quantities, not by the μ arithmetic itself under this base cell.

### A3. Comparator energy input is incorrectly generalized as one “mapped” convention

**Location:** Results §3.7 opening phrase “On the comparator benchmark's primary mapped-energy convention…”; Figure 5 legend “Mapped primary.”

**Evidence:** `scripts/comparator_benchmark/analysis.py` defines `PRIMARY` as FIORA-OS with condition `native_nce`, and ICEBERG/GLACIER with `ev_primary`. Only ICEBERG and GLACIER have separate `raw_nce_sensitivity` entries. Therefore, the primary comparator set does not use one identical mapped-energy input convention for all three systems.

**Why it matters:** The current label implies FIORA was evaluated after the same energy mapping as ICEBERG and GLACIER. This can distort a reader’s interpretation of cross-model ranking and physical comparability.

**Required correction:** Call this the “preregistered primary comparator conditions” and identify each condition: FIORA native NCE input; ICEBERG and GLACIER mapped-energy inputs; raw-NCE diagnostics for ICEBERG and GLACIER. In Figure 5, separate the FIORA native-input bar from the mapped ICEBERG/GLACIER bars or label each bar explicitly. Retain that all outputs are reduced to μ before P1 scoring.

### A4. The external result supports only a fixed-interface scalar transfer comparison, not cross-instrument energy transfer

**Location:** Abstract, Methods §2.6, Results §3.3 and §3.7, Discussion energy paragraphs.

**Evidence:** The recovered Phase 2 `ENERGY_INTERFACE_ADJUDICATION.md` identifies WUR source values as percent-style normalized HCD/SCE settings using the primary library paper and acquisition metadata; Thermo documentation distinguishes normalized settings from absolute collision energy in volts. The committed map `T(E)=a+bE` is empirical, and Design A remains `INTERFACE_UNRESOLVED`. Comparator results reverse for ICEBERG/GLACIER under the raw-NCE diagnostic.

**Assessment:** The revised source mostly respects this boundary. However, “the selected development model transfers to a separately sampled MSnLib population” in the Abstract could still be read as transferable physical energy response, and “external transfer” in discussion shorthand is broad.

**Required correction:** Prefer “external evaluation under the frozen nominal-energy map” wherever “transfer” could imply physical calibration. State that the assessment covers two HCD NCE settings on the MSnLib instrument under one fixed computational mapping. Keep the current limitation against instrument-generalized calibration.

### A5. Bibliography order is inconsistent with the newly assigned citation identifiers

**Location:** References section.

**Evidence:** The Phase 4 source inserts reference 7 before reference 1. In-text references 1–8 are assigned correctly after citation shifting, but the bibliography lists 7 first and then 1, 2, etc.

**Why it matters:** Numbered citations conventionally follow first-appearance order. The current ordering makes citation lookup and reference auditing unreliable and may produce inconsistent numbered styles in the generated documents.

**Required correction:** Sort the bibliography numerically (1–27), then verify all in-text IDs resolve and first-appearance ordering remains valid.

## Minor concerns

1. **Title terminology:** “Fragmentation extent” is a convenient shorthand, but μ is the precursor-normalized intensity-weighted mean observed mass, not a direct measure of bond cleavage or fraction of a molecule fragmented. The Methods gives the key limitation; consider “fragmentation-extent proxy” in the abstract and first introduction use.
2. **Directional interpretation:** Larger μ means observed intensity remains at higher m/z relative to the precursor; lower μ is consistent with greater mass reduction among observed ions. The current manuscript defines μ but does not state this simple direction explicitly. Add one short sentence to prevent readers from interpreting higher μ as more fragmentation.
3. **HCD/CID language:** The Introduction correctly identifies HCD as an activation mode and does not claim that MURU resolves mechanisms. Keep the scope to positive-mode HCD. Any future discussion of CID mechanisms should remain field context, not an inferred mechanism for these data.
4. **Figure 5 caption:** It should identify the CE Design A ordinate as differences in mean cosine similarity and the comparator panel as ratios of P1 on derived μ. The current figure caption lumps both under an energy-interface sensitivity heading, so specify the two distinct metrics in the caption.
5. **“Independent” wording:** The Phase 4 title now uses “External Evaluation,” which is appropriate. The manuscript still uses “independent external comparison” in Discussion. Qualify this as a separately sampled, exposure-controlled evaluation; the replacement set is now exposed and may contain chemically similar compounds.

## Concerns that cannot be resolved from current evidence

- No matched-instrument calibration establishes the physical relation between WUR normalized HCD settings and the MSnLib HCD NCE settings for the selected molecules.
- The available records do not constitute a signed expert adjudication of the energy interface.
- No independent laboratory has remeasured the endpoint or replicated the candidate/reference result.
- The five compounds outside model-profile support are excluded from the primary estimate; their unsupported predictions cannot establish model behavior beyond the frozen profile domain.
- The comparator benchmark’s common μ score does not evaluate fragment identities, individual peak intensities, or full-spectrum similarity, so it cannot support claims about full-spectrum chemical prediction quality.

## Reviewer disposition

The comparator endpoint correction and conservative energy-language changes are scientifically justified. The remaining denominator provenance and tolerance wording should be corrected in Methods and Supporting Information. The energy-source ambiguity itself remains a limitation, not a reason to discard the narrowly scoped frozen-input result. These comments are simulated and do not represent independent human review.
