# Energy-interface adjudication

The MSnLib confirmation uses fixed HCD NCE 20 and 60 and the frozen WUR-to-LCSB affine map `T(E)=a+bE`, with `a=-5.95552603907965` and `b=0.8618030610784555`. For external scoring the map is inverted as `(NCE-a)/b`. No parameter was fit to the MSnLib validation outcomes. The computation is reproducible, but this does not make the mapping a physical calibration.

Thermo instrument documentation defines NCE as a dimensionless setting that is approximately equivalent to eV for a reference ion of mass 500 and charge 1, with actual energy depending on precursor mass and charge. Source metadata and comparator checkpoint provenance do not establish a single, consistently applied eV/NCE convention for all public model inputs. Some comparator preprocessing pathways use raw numeric NCE; other conversion pathways exist in source code. The evidence supports an unresolved mapping, not a definitive conversion.

The separate CE Design A study had 33 compounds. K1 raw NCE was top-ranked (composite 0.557070), but Bonferroni-adjusted intervals for K1−K2 and K1−K3 crossed zero. Frozen verdict: `INTERFACE_UNRESOLVED`. The comparator benchmark's raw-NCE diagnostic reverses ICEBERG and GLACIER directions relative to its primary convention. Therefore:

- The primary MURU scalar confirmation is valid as a test under its fixed computational map.
- No universal physical interpretation of that map is established.
- Public full-spectrum comparator rankings are conditional on the energy input convention.
- No state-of-the-art or convention-independent superiority claim is supported.
- A physically calibrated prospective study would require a new protocol and outcomes; it is outside this retrospective package.
