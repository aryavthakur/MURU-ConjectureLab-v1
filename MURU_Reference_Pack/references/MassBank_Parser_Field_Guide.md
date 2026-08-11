# MassBank Parser Field Guide for MURU

Canonical specification: MassBank Record Format 2.6.0, MassBank Consortium.

Official specification location:
`https://github.com/MassBank/MassBank-web/blob/master/Documentation/MassBankRecordFormat.md`

Official data repository:
`https://github.com/MassBank/MassBank-data`

## Fields MURU should preserve

### Identity and provenance

`ACCESSION`
Unique MassBank record identifier.

`DATE`
Record creation or modification date.

`AUTHORS`
Record contributors.

`LICENSE`
Reuse terms.

`PUBLICATION`
Associated publication when supplied.

`PROJECT`
Associated project when supplied.

`COMMENT`
May contain confidence, merge history, or other provenance information.

### Compound identity

`CH$NAME`
Compound name or names.

`CH$FORMULA`
Molecular formula.

`CH$EXACT_MASS`
Exact mass.

`CH$SMILES`
SMILES representation.

`CH$IUPAC`
InChI representation.

`CH$LINK`
External identifiers, including InChIKey when present.

For grouping spectra by molecule, prefer a stable structural identifier such as InChIKey when available. Do not group solely by display name.

### Instrument and acquisition conditions

`AC$INSTRUMENT`
Commercial instrument information.

`AC$INSTRUMENT_TYPE`
Instrument type.

`AC$MASS_SPECTROMETRY: MS_TYPE`
MS level, for example MS2.

`AC$MASS_SPECTROMETRY: ION_MODE`
Positive or negative ion mode.

Other `AC$MASS_SPECTROMETRY` subtags
May encode collision energy, fragmentation mode, ionization information, resolution, and related conditions.

MURU must preserve the original collision energy text before attempting numerical normalization.

### Precursor information

`MS$FOCUSED_ION`
May contain precursor ion, precursor m/z, and precursor adduct information.

### Spectral peaks

`PK$SPLASH`
Stable spectral hash.

`PK$NUM_PEAK`
Peak count.

`PK$PEAK`
Peak list containing m/z, intensity, and relative intensity.

## MURU parsing rule

Never throw away the raw metadata representation after parsing.

For every normalized field, retain:

* original raw value
* parsed value
* unit or collision energy type when known
* parser status
* warning or exclusion reason when ambiguous

This is especially important for collision energy because records may use different units or conventions.

## Suggested canonical collision energy object

Conceptually:

```text
raw_value
numeric_value
energy_type
unit
parse_status
source_field
```

Possible `energy_type` values should be determined from actual encountered data and the official specification. Do not invent a universal conversion between absolute eV and normalized collision energy.

## Scientific grouping key

A candidate repeated measurement group should normally require compatibility on at least:

* molecular identity
* ion mode
* precursor adduct
* instrument or instrument class as required by the experiment
* fragmentation method
* collision energy convention

The exact grouping key should be justified from the selected dataset rather than generalized prematurely to all MassBank data.
