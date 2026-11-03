# Final energy-interface adjudication

**Status:** Evidence-bounded technical assessment for the Phase 5 internal review package. This is not a signed instrument-specialist opinion or a human expert adjudication.

## Adjudication

The frozen numerical analysis is reproducible as a computation under its chosen energy-coordinate convention. The evidence does **not** establish that the affine bridge is a physical conversion between NCE and eV, a cross-instrument calibration, or a universal relationship between WUR and MSnLib acquisition energies. The appropriate scientific description is therefore: *external comparison of the frozen predictions under the study's fixed numerical energy adapter and selected records*. Physical transfer of a calibrated fragmentation trajectory remains unestablished.

The Phase 4 manuscript also contains two material energy-description gaps: (1) it says that the WUR development records “label” values as NCE/SCE although the exported collision-energy field is unitless and the NCE interpretation is supplied by source publication/acquisition context; and (2) it identifies MSnLib evaluation rungs as HCD NCE 20 and 60 despite a direct conflict with the MSnLib primary paper, which reports the public library's MS2 settings as 20 eV and 60 eV. The Phase 4 manuscript does not show that the nine specific source archives used in this evaluation are all the same acquisitions described by the paper, nor does it produce their native method files to resolve the conflict. Until reconciled, those values should be called *recorded numeric collision-energy settings 20 and 60* (or fixed study rungs 20 and 60), with their physical convention explicitly unresolved.

## Evidence and the frozen conventions

### WUR development coordinate

The primary WUR library paper reports normalized HCD settings 15, 30, 45, 60, 75, and 90 and stepped collision energy settings 25, 38, and 59. Its DOI is [10.1021/acs.analchem.5c03020](https://doi.org/10.1021/acs.analchem.5c03020). Local acquisition metadata identifies Orbitrap IQ-X HCD and filter strings such as `@hcd15.00`. These are evidence for interpreting the source values as normalized/stepped instrument settings. However, the exported MassBank `AC$MASS_SPECTROMETRY: COLLISION_ENERGY` value is not independently unit-bearing.

This distinction is explicit in `src/muru/energy.py` (module docstring and `parse_collision_energy`, approximately lines 1–18 and 93–139): a bare value such as `15` has `unit=None`, `parse_status="NO_UNIT_IN_RECORD"`, and `energy_type="NCE_ASSUMED_FROM_PUBLICATION"`. Thus the manuscript's Methods §2.6 sentence “The WUR development records label HCD settings as NCE ... and stepped collision energy as SCE ...” overstates what the record itself says. The source-level interpretation can be stated as: “The WUR library publication and acquisition context identify the HCD ladder as normalized settings and the stepped ladder as SCE; the exported collision-energy field itself contains a numeric value without a unit.” The same limitation should be applied wherever WUR values are called directly “NCE” without attribution.

The WUR development protocol states the direction of the frozen affine bridge: the model's LCSB nominal coordinate (E) is mapped to the WUR coordinate (T(E)=a+bE), with (a=-5.95552603907965) and (b=0.8618030610784555); WUR observations are read at that mapped coordinate by PCHIP (`MURU_WUR_V2_DEVELOPMENT_PROTOCOL.md`, §2; `src/muru/wur_v2/population.py`, module docstring and `build`; `src/muru/wur_bridge.py::apply_energy_map`). For MSnLib deployment, the protocol applies the inverse, (E_LCSB=(NCE_WUR-a)/b) (`MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md`, §2 and `MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md`, §3; code `src/muru/wur_v2/external_msnlib.py::adapter_energy`). The Phase 4 phrase “The WUR-to-LCSB development bridge used ... (T(E)=a+bE)” obscures the direction; it should say that the *LCSB nominal coordinate is mapped to WUR nominal coordinates by T; the external adapter applies T's inverse to the recorded rung values*.

Neither direction has a committed collision-physics derivation or matched-instrument calibration. The coefficients are fixed empirical alignment parameters inherited from the earlier development protocol. They are not an eV↔NCE conversion. The scientific validity of calculating the candidate/reference contrast under a common, frozen numerical input remains distinct from a claim that the two instruments experienced physically equivalent energy deposition.

### MSnLib evaluation rungs: a primary-source conflict

The Phase 4 manuscript §2.1, §2.6, abstract, and results call the validation rungs “HCD NCE 20 and 60.” The frozen analysis code `src/muru/wur_v2/external_msnlib.py` defines `RUNGS=(20.0,60.0)` and selects MS2 records whose parsed `collision_energy` numeric values equal 20 and 60 (`fixed_rung_scans`). The frozen protocol and result call these NCE 20/60 (`MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md`, §§2, 5–6; `MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md`, §§3, 6; result, pp. 1–2).

But the peer-reviewed primary MSnLib paper, Brungs et al., *Nature Methods* 22, 2028–2031 (2025), DOI [10.1038/s41592-025-02813-0](https://doi.org/10.1038/s41592-025-02813-0), states that its flow-injection MSn analysis used a Thermo Orbitrap ID-X and that MS2 energies were set to **20 eV and 60 eV**, with assisted energy tested in 15 eV steps. This does not by itself prove that every one of the nine Zenodo mzML source archives included in the MURU evaluation is from exactly that acquisition method or has absolute-energy semantics. The frozen population is assembled from nine positive-mode ZIPs (`MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md`, §6; `src/muru/wur_v2/msnlib_design.py::ZIPS`), and the evaluation identifies rungs using header numeric values without instrument-method energy-type metadata. No native Thermo method files or archive-specific calibration evidence were located in the accessible frozen artifacts. Therefore the exact convention for the *selected evaluation spectra* is unresolved; the primary paper's eV description and the project protocol's NCE label cannot both be repeated as settled fact.

The Thermo Orbitrap ID-X Method Editor documentation distinguishes normalized collision energy, set as a percentage, from absolute accelerating voltage, set in volts ([official ID-X Method Editor Help, “Activation parameters”](https://docs.thermofisher.com/r/Orbitrap-ID-X-Method-Editor-Help/2912190859v1en-US2912274187)). This proves that both semantics are available on the instrument family, not which mode was configured for each historical archive. Do not infer the selected scan's unit from the numeric value or instrument model alone.

**Required manuscript correction:** Until acquisition-level metadata is recovered, use “numeric collision-energy rungs 20 and 60” or “recorded 20/60 rungs; energy type not verified for all source files.” State that protocol records call them NCE but the MSnLib paper describes its library acquisition as eV, and that the file-level method semantics for the sampled archives remain unresolved. If acquisition methods establish NCE, update with exact archive/method provenance and hashes; if they establish eV, update accordingly. Do not continue to say “not values in eV” as a resolved statement.

### Cross-instrument anchor gate

The external protocol explicitly says A0 uses the frozen inverse map with “no free parameter; assumes ID-X NCE equals IQ-X NCE” (`MURU_WUR_V2_MSNLIB_EXTERNAL_PROTOCOL.md`, §2). The later confirmation freeze records that the absolute-agreement anchor gate failed for A0/A1/A2 by small margins (A0 NCE20 median |Δμ|=0.0501 vs 0.05; A1 pooled RMSD=0.0811 vs 0.08; A2 NCE20 median=0.0506) and that the final study tests the comparative claim under A0 only (`MURU_V2_MSNLIB_CONFIRMATION_V2_FREEZE.md`, §9; `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md`, §7). These are not the separate Design A 33-compound inferential results.

The Phase 4 main manuscript and its `FINAL_ENERGY_INTERPRETATION.md` omit both the explicit ID-X=IQ-X NCE-semantics assumption and the failed absolute-agreement anchor gate. A later sentence saying the map is not a universal calibration is not a substitute: readers need to know the frozen mapping assumption was tested on anchors and its agreement gate failed. This is a **major** disclosure correction. State the failed gate and clarify that the result nevertheless remains a prespecified comparative test of candidate versus reference on the same frozen numerical input and measured endpoint; it does not validate absolute trajectory agreement or physical transfer.

## Comparator conventions and Design A

The Phase 4 current manuscript correctly specifies that the comparator benchmark uses model-specific inputs: FIORA-OS native NCE, ICEBERG and GLACIER `ev_primary`, with raw-NCE diagnostics only for ICEBERG and GLACIER (§§2.8, 3.7; `scripts/comparator_benchmark/analysis.py`). Preserve that distinction. `ev_primary` is a benchmark pipeline label; it must not be presented as independently verified physical eV unless the upstream model's training/inference semantics support that interpretation.

The 33-compound CE Design A adjudication compares three tested computational conventions. Its frozen adjusted intervals cross zero and verdict is `INTERFACE_UNRESOLVED` (`artifacts/ce_interface_adjudication/`; Phase 4 §3.7 and result). This establishes that the adjudication failed to select a convention under its prespecified rule. It does not establish that all conventions are physically equivalent or that the rank order is reliable. Keep this separate from the earlier failed MSnLib anchor agreement gate.

## What remains computationally valid

Subject to correct scan/population processing, the frozen candidate and reference predictions can be compared against the same measured endpoint at the selected numeric rung labels using the same map, support rule, and scoring code. The external pooled error ratio and its scaffold-bootstrap interval describe that conditional comparison. They do **not** establish:

- that the two values 20 and 60 represent NCE (%) for all selected files;
- physical energy equivalence across IQ-X and ID-X;
- a physically calibrated fragmentation trajectory;
- a universal NCE-to-eV or instrument conversion;
- cross-instrument generalization beyond this dataset and frozen computational adapter;
- a convention-independent ranking of external spectral models.

The word “external” may describe a separately sampled population, but “independent energy transfer” or “cross-instrument validation” would overstate the current evidence. The exposure-controlled population is now exposed, and the original sample-1 decode history remains disclosed.

## Source wording contradiction register

| Phase 4 statement/location | Contradictory or limiting evidence | Adjudication |
|---|---|---|
| Main manuscript §2.6: WUR records “label” settings NCE/SCE; supplement §S5: says primary publication reports them | `src/muru/energy.py` says generic `COLLISION_ENERGY` has no unit, and parser labels NCE as assumed from publication | Attribute NCE/SCE interpretation to source paper/acquisition context, not the bare field. |
| Main abstract, §§2.1/2.6/3.1 and §4: selected MSnLib values are fixed HCD NCE 20/60 and “not values in eV” | Frozen code picks numeric values only; MSnLib primary paper reports public library MS2 at 20/60 eV; exact nine archive method settings unavailable | Downgrade to recorded numeric 20/60 rungs with unresolved units unless archive-specific acquisition records are recovered. |
| Methods §2.6 phrase “WUR-to-LCSB development bridge” | Development code maps LCSB E forward to WUR T(E); external deployment uses inverse | Clarify direction and identify external adapter as inverse T. |
| Energy section/Discussion describes empirical map uncertainty generally | Protocol explicitly assumes ID-X NCE equals IQ-X NCE; frozen absolute-agreement anchor gate failed narrowly | Report assumption and gate result in main Methods/Limitations. |
| `FINAL_ENERGY_INTERPRETATION.md` states external MSnLib settings are NCE 20/60, not eV | Same MSnLib primary-paper conflict | Replace definitive unit statement with file-level unresolved convention. |

## Highest-value resolution steps (not performed in this adjudication)

1. Retrieve the nine exact source archives specified by the frozen `msnlib_design.ZIPS` manifest and verify hashes against `artifacts/wur_v2_confirmation_v2/freeze/validation_scan_allowlist.csv` and the manifest.
2. Inspect archive-specific Thermo raw methods, tune/method exports, acquisition logs, or vendor metadata to determine normalized versus absolute HCD mode for each archive. Preserve the source files and hashes; do not infer from `collision_energy=20/60` alone.
3. Trace the WUR acquisition publication, IQ-X method records, and generic MassBank exports separately; retain the unitless-field caveat.
4. Ask an analytical chemist or Thermo instrument specialist to adjudicate the method-version-specific semantics and whether any defensible physical relation exists for the precursor population. This memo is a technical evidence packet, not that expert's answer.

## References

- Padilla-González et al. “Creation of an Open-Access High-Resolution Tandem Mass Spectral Library of 1000 Food Toxicants.” *Analytical Chemistry* (2025). DOI: [10.1021/acs.analchem.5c03020](https://doi.org/10.1021/acs.analchem.5c03020).
- Brungs et al. “MSnLib: efficient generation of open multi-stage fragmentation mass spectral libraries.” *Nature Methods* 22, 2028–2031 (2025). DOI: [10.1038/s41592-025-02813-0](https://doi.org/10.1038/s41592-025-02813-0).
- Thermo Fisher Scientific. [Orbitrap ID-X Method Editor Help: Activation parameters](https://docs.thermofisher.com/r/Orbitrap-ID-X-Method-Editor-Help/2912190859v1en-US2912274187).
- Révész et al. “Collision energies: Optimization strategies for bottom-up proteomics.” *Mass Spectrometry Reviews* (2023). DOI: [10.1002/mas.21763](https://doi.org/10.1002/mas.21763). This is general collision-energy context; it does not adjudicate the specific historical methods.
