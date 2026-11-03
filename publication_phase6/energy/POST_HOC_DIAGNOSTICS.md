# Post hoc diagnostics

## Question

Does the converted mzML metadata provide evidence about the semantics of the selected frozen energy labels without retuning the model or changing the original comparison?

## Design and status

The Phase 6 member/scan audit is a metadata diagnostic. It compares each allowlisted mzML member SHA-256 with the frozen allowlist, verifies ZIP CRC, locates frozen spectrum IDs, checks MS2, checks selected precursor m/z, and reads the PSI-MS collision-energy value/unit. It does not recompute μ, select a new energy adapter, tune predictions, or revise model selection.

## Interpretation

The all-scan validator passed: the converted mzML records selected for the frozen analysis encode the expected numerical rung in eV. A separate audit found 161 public `.meth` files, all Vanquish LC separation methods without a selected-run link, and a nested NIH archive listing containing no method-like files. Neither establishes native Xcalibur method settings or physical equivalence to the development coordinate. The A0/A1/A2 anchor results and the separately frozen Design A verdict remain unchanged.

No outcome-guided alternative energy mapping was tested. No new headline or subgroup performance estimate was generated. The external sample is exposed and is not a fresh validation population.
