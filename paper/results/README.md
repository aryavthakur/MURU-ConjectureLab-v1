# MURU ConjectureLab v1: Prospective Result Ingestion Scaffold

This directory (`paper/results/`) houses the deterministic, frozen-schema result ingestion and reporting scaffold for MURU ConjectureLab v1.

**Governing Principle:** No benchmark case was executed, no prospective result artifact was inspected, and no fabricated or mock number was placed into publication outputs during the construction of this scaffold.

---

## 1. Core Architecture & Fail-Closed Guarantee

The ingestion pipeline consumes prospective experimental outputs and deterministically populates:
1. **Paper Result Tables** (Tables 3b through 9 in Markdown, LaTeX, and JSON).
2. **Prospective Figure Panels** (Figures 4D, 5D, 6D, 7A–D, 8B–C in SVG, PDF, and 300-DPI PNG).
3. **Claim Matrix Result Fields** (`MURU_CLAIM_MATRIX.md` claim statuses and allowed wording).
4. **Evidence Ledger Entries** (Class C prospective entries P001–P018 in `MURU_EVIDENCE_LEDGER.json`).
5. **Machine-Readable Master Result JSON** (`paper/results/paper_results.json`).

### Fail-Closed Behavior
If required input artifacts are absent when `ingest_results.py` or `render_prospective_figures.py` is invoked:
- The script exits immediately with error code `2`.
- Outputs an explicit error message: `RESULT_ARTIFACT_MISSING`.
- **Zero mock/fake curves or numbers** are rendered in publication outputs.

---

## 2. Expected Input Artifacts & Schemas

| Artifact | Expected Path | Partition / Scope | Frozen Denominator | Schema Identifier |
|---|---|---|---|---|
| **Null Calibration** | `artifacts/calibration_thresholds.json` | 100 null worlds (30 seeds/world) | 100 worlds ($\ge 95$ floor) | `muru-calibration-result-schema-1.0.0` |
| **Development Aggregate** | `artifacts/paper_benchmark_development_aggregate.json` | 80 Development cases | 80 cases | `muru-development-aggregate-schema-1.0.0` |
| **Held-Out Aggregate** | `artifacts/paper_benchmark_held_out_aggregate.json` | 240 Held-out cases | 240 cases | `muru-held-out-aggregate-schema-1.0.0` |
| **Challenge Aggregate** | `artifacts/paper_benchmark_challenge_aggregate.json` | 60 Challenge cases | 60 cases (staged/disabled) | `muru-challenge-aggregate-schema-1.0.0` |

### Frozen Endpoints and Exact Denominators

#### Primary Gates (Held-Out)
- **G1 Scalar Competence**: Denominator **164** (F01–F05, F07–F12, F17, F18 at 12 each = 156; + F19A: 4, F19B: 4). Criterion: Lower 95% Wilson score bound $\ge 0.70$.
- **G2 Family Recovery**: Denominator **144** (12 families at 12 each). Requires `support_status == MATCH` AND `family_status == MATCH`. Criterion: Lower 95% Wilson score bound $\ge 0.70$.
- **G3 Principal Structural Safety**: Denominator **36** (F07: 12, F19: 12 [4 F19A, 4 F19B, 4 F19C], F20: 12 [4 F20A, 4 F20B, 4 F20C]). Criterion: Upper 95% Wilson score bound $\le 0.15$. `UNEVALUABLE` is conservatively scored as a violation and retained in denominator 36.
- **Umbrella Benchmark Claim**: Positive iff calibration is valid ($\ge 95/100$ worlds) AND G1 passes AND G2 passes AND G3 passes.

#### Secondary Endpoints (Ungated, Descriptive Only)
- **Joint Parameter Recovery**: Denominator **156** cases. Evaluated at canonical anchor $\mathbf{x}_0 = (250, 0, 0, 0, 0)$.
- **Mass Exponent Recovery ($p_{\text{mass}}$)**: Denominator **156** cases. Tolerance $|p - p_{\text{truth}}| \le 0.15$.
- **Descriptor Coupling Recovery ($c_{\text{desc}}$)**: Denominator **84** cases (F08–F12, F17, F18). Tolerance $|c - c_{\text{truth}}| \le 0.10$.
- **Predictive Equivalence**: Denominator **144** cases. Evaluated over 2,160 reference points across 12 reference frames (`4fef2379...`). Criteria: $\text{valid\_fraction} \ge 0.995$, $c^* > 0$, $\text{rel\_RMSE} \le 0.05$, Pearson $r \ge 0.990$.
- **Exact Algebra Recovery**: Denominator **60** cases (F01, F08, F09, F10, F17). Symbolic equivalence under SymPy normalisation. Distinct functional-equivalence classes reported.
- **Support Recovery**: Denominator **144** cases. `support_status == MATCH`.

#### Model Adequacy & Diagnostics
- **M0 Specificity**: Denominator **164** cases (`M0_NOT_REJECTED`).
- **M1 Sensitivity**: Denominator **36** cases (F06: 12, F13: 12, F16: 12).
- **M2 Sensitivity**: Denominator **24** cases (F14: 12, F16: 12).
- **M3 Sensitivity**: Denominator **24** cases (F15: 12, F16: 12).
- **Boundary Hit Diagnostic**: Denominator **12** cases (F05).
- **Response Structure Diagnostic**: Denominator **4** cases (F19C).
- **Scalar Target Yield**: Denominator **164** cases.

---

## 3. Statistical Calculation Rules

### Wilson Score Confidence Intervals
All binomial confidence intervals are computed from exact integer numerator $k$ and exact frozen denominator $n$ using $z = 1.959963984540054$:
$$\hat{p} = \frac{k}{n}$$
$$\text{center} = \frac{\hat{p} + \frac{z^2}{2n}}{1 + \frac{z^2}{n}}, \quad \text{margin} = \frac{z}{1 + \frac{z^2}{n}} \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}$$
$$\text{Lower} = \max(0.0, \text{center} - \text{margin}), \quad \text{Upper} = \min(1.0, \text{center} + \text{margin})$$

Interval bounds are **never copied blindly** from external logs; they are recomputed deterministically.

---

## 4. Mechanical Wording Selection

No subjective language or LLM generation determines numerical outcomes. Wording templates from `paper/results/templates/` are selected mechanically:
- `PASS`: Emits pre-approved language confirming gate conditions were met.
- `FAIL`: Emits pre-approved language reporting gate failure and stating that the synthetic claim is not supported.
- `INCONCLUSIVE` / `NOT_EVALUABLE`: Emits explicit explanations of missing/incomplete inputs.

For claims C1 through C10, C4a, and C4b:
- Allowed wording is parameterized strictly by evaluated numerators, denominators, rates, and intervals.
- All binding **forbidden overclaims** (e.g. forbidding real-world transfer, mechanistic claims, or identifying single equations as laws) are strictly maintained.

---

## 5. Directory Layout

```
paper/results/
├── README.md                                  # This specification document
├── schema/                                    # JSON Schemas and Python validators
│   ├── __init__.py
│   ├── calibration_result.schema.json         # Null calibration schema (100 worlds, T(c) table)
│   ├── development_aggregate.schema.json      # Development 80-case aggregate schema
│   ├── held_out_aggregate.schema.json         # Held-out 240-case aggregate schema
│   ├── case_outcome.schema.json               # Individual case outcome record schema
│   ├── challenge_aggregate.schema.json        # Challenge 60-case aggregate schema (staged)
│   ├── paper_result_payload.schema.json       # Master machine-readable results payload schema
│   └── validators.py                          # Schema validators and denominator assertions
├── templates/                                 # Wording and layout templates
│   ├── verdict_wording_templates.json         # PASS / FAIL / INCONCLUSIVE / NOT_EVALUABLE templates
│   ├── claim_wording_templates.json           # Claims C1–C10, C4a, C4b allowed phrasing & forbidden overclaims
│   └── evidence_ledger_templates.json         # Class C ledger entries P001–P018
└── scripts/                                   # Ingestion and reporting engines
    ├── __init__.py
    ├── wilson.py                              # Exact Wilson 95% & Clopper-Pearson calculator
    ├── verdict_engine.py                      # Deterministic rule engine for gate evaluation
    ├── populate_tables.py                     # Generates Tables 3b–9 in MD, TeX, JSON
    ├── render_prospective_figures.py          # Renders Figures 4D, 5D, 6D, 7A–D, 8B–C (fails closed)
    ├── update_claim_matrix.py                 # Updates MURU_CLAIM_MATRIX.md
    ├── update_evidence_ledger.py              # Updates MURU_EVIDENCE_LEDGER.json
    ├── export_paper_results_json.py           # Produces paper_results.json
    ├── ingest_results.py                      # Master pipeline entry point
    └── test_scaffold.py                       # Automated test suite
```

---

## 6. Execution & Usage

### Running the Test Suite
```bash
python3 -m unittest paper/results/scripts/test_scaffold.py
```

### Ingesting Prospective Results (Once Available)
```bash
python3 -m paper.results.scripts.ingest_results \
  --calibration artifacts/calibration_thresholds.json \
  --development artifacts/paper_benchmark_development_aggregate.json \
  --held-out artifacts/paper_benchmark_held_out_aggregate.json
```

### Dry Run / Check Only
```bash
python3 -m paper.results.scripts.ingest_results \
  --calibration artifacts/calibration_thresholds.json \
  --development artifacts/paper_benchmark_development_aggregate.json \
  --held-out artifacts/paper_benchmark_held_out_aggregate.json \
  --dry-run
```

---

## 7. Contamination Attestation

- **Calibration scientific values inspected:** None.
- **Benchmark cases executed:** 0.
- **Prospective result values fabricated or inserted:** None.
- **Active branches modified:** None (worked strictly on `writing/muru-result-ingestion-scaffold`).
