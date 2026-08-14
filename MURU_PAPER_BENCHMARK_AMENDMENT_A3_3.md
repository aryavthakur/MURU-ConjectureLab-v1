# MURU paper benchmark — Amendment A3.3: Secondary Endpoint Scientific Contracts (Parameter Recovery & Predictive Equivalence)

## A3.3.0 Amendment Record

| Field | Value |
|---|---|
| Amendment | A3.3 — Secondary-Endpoint Scientific Contracts (Parameter Recovery & Predictive Equivalence) |
| Original content freeze | `d94d2c9` ("Prepare prospective paper benchmark content freeze") |
| Adequacy amendment A1 | `2ac86c5` ("Amendment A1: bind the M0/M1/M2/M3 adequacy decision rule") |
| F16 repair A2 | `03cc4d3` ("Amendment A2: repair the F16 generator to honour its declared M1+M2+M3 truth") |
| Generator version A2.1 | `80a7803` ("Amendment A2.1: bump GENERATOR_VERSION") |
| G2/G3 contract freeze A3.1 | `c8938e8` ("Amendment A3.1: G2/G3 structural endpoints and calibration contract") |
| Null calibration correction A3.2 | `1194fcbc9d9edcb14583eedfdcb0e395028dd93a` ("Amendment A3.2: null calibration base target and scaffold split") |
| Triggering audit | `7f3ca804277db7491bbf5dc3cf5984c8361ffab4` (`audit/MURU_ENDPOINT_CONTRACT_TRACEABILITY_AUDIT.md`) |
| Branch | `science/muru-paper-benchmark-a3-3` |
| Contract version | `paper-benchmark-secondary-endpoints-1.0.0` |
| Effective content freeze | the commit introducing this document, tagged `benchmark-content-freeze-a3-3` |

### Reason for Amendment
A comprehensive endpoint contract traceability audit (`audit/MURU_ENDPOINT_CONTRACT_TRACEABILITY_AUDIT.md`, commit `7f3ca804277db7491bbf5dc3cf5984c8361ffab4`) revealed a prospective governance gap: while content freeze V1 (`d94d2c9`) named two **SECONDARY** symbolic endpoints—**Parameter Recovery** (held-out denominator 156) and **Predictive Equivalence** (held-out denominator 144)—and assigned them case applicability and Wilson 95% intervals, it did not bind their deterministic mathematical evaluation contracts, metrics, tolerances, or failure semantics. Amendment A3.1 prospectively bound primary gate G2 (structural family and support matching), but explicitly left parameter recovery and predictive equivalence as separate secondary measures. This amendment completes those secondary evaluation contracts prospectively before any Development rerun, before structural-null calibration is executed, and before the sealed Held-out partition is opened.

### Absolute Contamination Status
No calibration output, partial calibration record, or threshold table was inspected. No Development scientific outcome was executed, scored, enumerated, parsed, summarised, or inspected. Held-out and Confirmation partitions remain strictly sealed and unopened. All tolerances and evaluation criteria in this amendment are derived from prospective physical principles, Master Plan specifications, and frozen case generator definitions.

### Scope of Scientific Change
1. Binds the complete, deterministic, algebraically invariant evaluation contract for **Parameter Recovery** across its 156 held-out cases.
2. Binds the complete, deterministic, out-of-sample functional evaluation contract for **Predictive Equivalence** across its 144 held-out cases.
3. Preserves all frozen denominators (156 and 144), roles (SECONDARY), gates (G1, G2, G3), calibration protocols (A3.1/A3.2), and primary claim decision rules without alteration.

---

## A3.3.1 Parameter Recovery Scientific Contract

### Scientific Role & Denominator
- **Role:** SECONDARY descriptive endpoint (never part of G1, G2, or G3).
- **Applicable Families:** F01–F05, F07–F12, F17, F18 (13 families $\times$ 12 held-out cases = **156 cases**).
- **Denominator Discipline:** The denominator is strictly fixed at **156**. Unresolved, non-finite, missing, or unparseable candidate expressions count as non-successes and never reduce the denominator.

### Theoretical Foundation: Coordinate-Free Dimensionless Parameter Extraction
In the M0 collapse model ($\mu(E) \approx \Phi(E/g)$), the overall multiplicative scale of $g$ is fundamentally confounded with the horizontal scale of the profile $\Phi$ and the chosen mass reference normalisation (e.g. $\sqrt{\text{mass}/250}$ vs $\sqrt{\text{mass}}$). Therefore, raw dimensional scale factors are non-identifiable.

However, physical scaling exponents and relative descriptor couplings are dimensionless, scale-invariant, and coordinate-free. Parameter recovery evaluates the recovery of these exact dimensionless physical parameters at the neutral reference anchor point:
$$\mathbf{x}_0 = (\text{mass} = 250.0, \text{descriptor} = 0.0, \text{descriptor2} = 0.0, \text{distractor} = 0.0, \text{correlated\_distractor} = 0.0)$$

### Identifiable Parameter Definitions

1. **Mass Scaling Exponent ($p_{\text{mass}}$):**
   Applicable to all 156 cases. Defined as the dimensionless logarithmic elasticity of $\hat{g}$ with respect to mass at $\mathbf{x}_0$:
   $$p_{\text{mass}}(\hat{g}) = \left. \frac{\partial \ln \hat{g}}{\partial \ln \text{mass}} \right|_{\mathbf{x}_0} = \left. \frac{\text{mass}}{\hat{g}} \frac{\partial \hat{g}}{\partial \text{mass}} \right|_{\mathbf{x}_0}$$
   - **Planted Truth ($p_{\text{truth}}$):** `truth.exponents["mass"]` ($0.50$ for F01–F05, F08–F12, F17, F18; drawn from $[0.45, 0.75]$ for F07).
   - **Absolute Tolerance:** $\Delta p = |p_{\text{mass}}(\hat{g}) - p_{\text{truth}}| \le 0.15$.
   - **Scientific Rationale:** Inherited from Master Plan §18.3. A tolerance of $\pm 0.15$ on a nominal exponent of $0.50$ provides a $\pm 30\%$ resolution band, sufficient to distinguish distinct physical scaling laws ($p = 0.5$ square root vs $p = 1.0$ linear vs $p = 0.33$ cube root vs $p = 0.0$ constant) while accommodating finite-sample estimation variance.

2. **Normalized Descriptor Coupling Coefficient ($c_{\text{desc}}$):**
   Applicable to the 84 held-out cases in descriptor-dependent families (F08, F09, F10, F11, F12, F17, F18). Defined as the relative sensitivity of $\hat{g}$ to the active descriptor at $\mathbf{x}_0$:
   - For linear/affine (`mass_affine_descriptor`, F08, F11, F12, F17) and saturating (`mass_saturating_descriptor`, F09):
     $$c_{\text{desc}}(\hat{g}) = \left. \frac{1}{\hat{g}} \frac{\partial \hat{g}}{\partial \text{descriptor}} \right|_{\mathbf{x}_0}$$
   - For interaction (`mass_interaction`, F10):
     $$c_{\text{desc}}(\hat{g}) = \left. \frac{1}{\hat{g}} \frac{\partial^2 \hat{g}}{\partial \text{descriptor} \partial \text{descriptor2}} \right|_{\mathbf{x}_0}$$
   - For exponential (`mass_exponential_descriptor`, F18, where generative law is $\exp(c \cdot d / 3)$):
     $$c_{\text{desc}}(\hat{g}) = \left. \frac{3}{\hat{g}} \frac{\partial \hat{g}}{\partial \text{descriptor}} \right|_{\mathbf{x}_0}$$
   - **Planted Truth ($c_{\text{truth}}$):** `truth.coefficients["coefficient"]` (drawn from $[0.25, 0.55]$).
   - **Absolute Tolerance:** $\Delta c = |c_{\text{desc}}(\hat{g}) - c_{\text{truth}}| \le 0.10$.
   - **Scientific Rationale:** On the generative range $c \in [0.25, 0.55]$, $\pm 0.10$ provides an error margin of $18–40\%$, requiring the discovered expression to capture the correct magnitude of the chemical modulation without penalizing equivalent algebraic reorganizations.

For mass-only families (F01–F05, F07; 72 cases), only $p_{\text{mass}}$ is evaluated.

### Algebraic Invariance
Because the differential operators normalize by $\hat{g}(\mathbf{x}_0)$, the extracted parameters $p_{\text{mass}}$ and $c_{\text{desc}}$ are strictly invariant to:
1. Any overall positive multiplicative scaling factor $A > 0$.
2. Arbitrary factoring or expansion (e.g. $A \sqrt{m}(1 + c d)$ vs $A \sqrt{m} + A c \sqrt{m} d$).
3. Mass normalisation shifts (e.g. $\sqrt{m/250}$ vs $\sqrt{m}$).

### Case-Level Success Predicate & Failure Semantics
A case achieves **Parameter Recovery Success** if and only if:
1. A candidate expression $\hat{g}$ is present and successfully parsed under the protected grammar.
2. $\hat{g}(\mathbf{x}_0)$ evaluates to a strictly positive finite real number ($\hat{g}(\mathbf{x}_0) > 0$).
3. The symbolic derivatives for all applicable parameters at $\mathbf{x}_0$ exist, are finite, and satisfy:
   $$|p_{\text{mass}}(\hat{g}) - p_{\text{truth}}| \le 0.15$$
   and (for descriptor-applicable families):
   $$|c_{\text{desc}}(\hat{g}) - c_{\text{truth}}| \le 0.10$$

Any missing expression, syntax failure, non-finite derivative, non-positive base evaluation, missing parameter dependency (derivative equals zero when non-zero is required), or parameter exceeding tolerance produces **Parameter Recovery Failure**.

---

## A3.3.2 Predictive Equivalence Scientific Contract

### Scientific Role & Denominator
- **Role:** SECONDARY descriptive endpoint (never part of G1, G2, or G3).
- **Applicable Families:** F01–F05, F08–F12, F17, F18 (12 families $\times$ 12 held-out cases = **144 cases**; F07 is excluded as mass-only safety control).
- **Denominator Discipline:** The denominator is strictly fixed at **144**. Unresolved, non-finite, missing, or out-of-tolerance candidate expressions count as non-successes and never reduce the denominator.

### Conceptual Distinction from G2 and Exact Algebra
1. **G2 (Primary Symbolic Gate):** Evaluates structural skeleton and active variable support (`support_status == MATCH` and `family_status == MATCH`).
2. **Exact Algebra Recovery (Secondary Symbolic Endpoint):** Evaluates exact symbolic/algebraic identity up to positive scale.
3. **Predictive Equivalence (Secondary Symbolic Endpoint):** Evaluates out-of-sample functional accuracy across the complete multidimensional descriptor domain, independent of whether the algebraic formulation matches the generative family.

### Evaluation Domain & Synthetic Space-Filling Design
To assess out-of-sample functional equivalence rather than in-sample fit, evaluation is performed on a prospectively frozen 5-dimensional evaluation grid $\mathcal{D}$:
- $\text{mass} \in [100.0, 800.0]$ Da (log-uniformly spaced)
- $\text{descriptor} \in [-2.5, +2.5]$ (uniformly spaced)
- $\text{descriptor2} \in [-2.5, +2.5]$ (uniformly spaced)
- $\text{distractor} \in [-2.5, +2.5]$ (uniformly spaced)
- $\text{correlated\_distractor} \in [-2.5, +2.5]$ (uniformly spaced)

**Point Construction Algorithm:**
- A deterministic space-filling design of $N = 2,048$ points generated via a deterministic scrambled Sobol low-discrepancy sequence (or Latin hypercube with canonical derived seed `PB|PRED_EQUIV|EVAL_GRID_N2048`).
- The evaluation lattice $\mathbf{X}_{\text{eval}} \in \mathbb{R}^{2048 \times 5}$ is frozen once for the entire benchmark.

### Comparison Metric & Positive Scale Alignment
For each case, the true law $g_{\text{true}}(\mathbf{x})$ and the discovered candidate $\hat{g}(\mathbf{x})$ are evaluated over $\mathbf{X}_{\text{eval}}$, producing evaluation vectors $\mathbf{y}_{\text{true}}, \hat{\mathbf{y}} \in \mathbb{R}^N$.

1. **Validity Check:**
   - Elements with non-finite values ($\text{NaN}$, $\pm\infty$) or non-positive values ($\hat{g}(\mathbf{x}) \le 0$) are marked invalid.
   - Let $\mathcal{V} \subseteq \{1, \dots, N\}$ be the valid index set.
   - If $\frac{|\mathcal{V}|}{N} < 0.995$ (i.e. more than 10 invalid points out of 2048), the candidate fails validity $\to$ **Predictive Equivalence Failure**.

2. **Optimal Positive Multiplicative Scale Alignment:**
   Because the collapse model identifies $g$ only up to a global positive multiplicative factor, $\hat{\mathbf{y}}$ is rescaled by the optimal least-squares positive scalar multiplier $c^*$:
   $$c^* = \frac{\sum_{i \in \mathcal{V}} y_{\text{true}, i} \cdot \hat{y}_i}{\sum_{i \in \mathcal{V}} \hat{y}_i^2}$$
   - If $c^* \le 0$, the candidate is negatively correlated or degenerate $\to$ **Predictive Equivalence Failure**.
   - Additive / affine intercept shifts ($a + b \hat{g}$ with $a \ne 0$) and non-linear parameter refitting are strictly **FORBIDDEN**.

3. **Scale-Adjusted Relative RMSE:**
   $$\text{rel\_RMSE} = \frac{\sqrt{\frac{1}{|\mathcal{V}|} \sum_{i \in \mathcal{V}} (y_{\text{true}, i} - c^* \hat{y}_i)^2}}{\sqrt{\frac{1}{|\mathcal{V}|} \sum_{i \in \mathcal{V}} y_{\text{true}, i}^2}}$$

4. **Pearson Correlation:**
   $$r = \frac{\sum_{i \in \mathcal{V}} (y_{\text{true}, i} - \bar{y}_{\text{true}})(\hat{y}_i - \bar{\hat{y}})}{\sqrt{\sum_{i \in \mathcal{V}} (y_{\text{true}, i} - \bar{y}_{\text{true}})^2 \sum_{i \in \mathcal{V}} (\hat{y}_i - \bar{\hat{y}})^2}}$$

### Exact Success Thresholds
A case achieves **Predictive Equivalence Success** if and only if all of the following hold:
1. Valid domain fraction $\ge 0.995$ ($|\mathcal{V}| \ge 2038$).
2. Optimal scale factor $c^* > 0$.
3. $\text{rel\_RMSE} \le 0.05$ (at most 5% relative root-mean-square error).
4. Pearson correlation $r \ge 0.990$.

**Scientific Rationale for Thresholds:**
- $\text{rel\_RMSE} \le 0.05$: Accommodates legitimate out-of-family mathematical approximations (e.g. Taylor series expansions, rational Padé approximants, or exponential approximations) that accurately reproduce the true scaling response within 5% error across the full physical domain.
- $r \ge 0.990$: Enforces strict directional monotonicity and co-variation across all active dimensions, preventing flat or distorted curves from passing via scale scaling alone.

---

## A3.3.3 Design Option Comparison

| Option | Definition | Advantages | Failure Modes / Disadvantages | Verdict |
|---|---|---|---|:---:|
| **Parameter: All Raw Constants** | Match raw constants (`scale`, `coeff`, `exponent`) | Appears comprehensive | Confounds $g$ with $\Phi$ horizontal scale; non-invariant to algebraic factoring; ill-posed | **REJECTED** |
| **Parameter: Exponent Only** | Match mass exponent $p \pm 0.15$ | Robust, dimensionless | Ignores descriptor sensitivity parameter in F08–F10, F18 | **REJECTED (Too Narrow)** |
| **Parameter: Dimensionless Elasticity (A3.3)** | Evaluate $p_{\text{mass}}$ and $c_{\text{desc}}$ via normalized derivatives at $\mathbf{x}_0$ | Strictly coordinate-free, algebraically invariant, covers all planted parameters | Requires symbolic differentiation of candidate expression | **ACCEPTED** |
| **Predictive: In-Sample Test Points** | Evaluate on 30 test compounds per case | Uses observed data | Small sample ($N=30$); sparse in 5D; does not test out-of-distribution stability | **REJECTED** |
| **Predictive: Dense Grid** | $10^5$ regular grid points | High density | Computationally heavy ($100\text{k}$ pts); curses of dimensionality | **REJECTED** |
| **Predictive: Sobol Low-Discrepancy (A3.3)** | $N=2048$ space-filling design on physical bounds; $\text{rel\_RMSE} \le 0.05$, $r \ge 0.990$ | Deterministic, space-filling, computationally fast, scale-invariant | Requires positive scale alignment | **ACCEPTED** |

---

## A3.3.4 Adversarial Review Findings

### Review 1: Algebraic Invariance (Parameter Recovery)
- *Test Case:* Consider $g_{\text{true}} = 1.4 \sqrt{\text{mass}/250}(1 + 0.35 \cdot \text{desc})$. Suppose discovery yields an expanded representation $\hat{g} = 0.0885 \sqrt{\text{mass}} + 0.0310 \sqrt{\text{mass}} \cdot \text{desc}$.
- *Evaluation under A3.3:*
  - $\hat{g}(\mathbf{x}_0) = 0.0885 \sqrt{250} = 1.400$.
  - $p_{\text{mass}} = \frac{250}{1.4} [ \frac{0.0885}{2 \sqrt{250}} ] = 0.500$ ($\Delta p = 0.000 \le 0.15$).
  - $c_{\text{desc}} = \frac{1}{1.400} [ 0.0310 \sqrt{250} ] = \frac{0.490}{1.400} = 0.350$ ($\Delta c = 0.000 \le 0.10$).
- *Verdict:* Perfectly invariant to expansion, factoring, and normalisation shifts.

### Review 2: Metric Gaming & Trivial Models (Predictive Equivalence)
- *Test Case A (Constant Model):* $\hat{g} = 1.0$.
  - $r = 0.0$ (fails $r \ge 0.990$); $\text{rel\_RMSE} \approx 0.32 > 0.05$. **FAILS.**
- *Test Case B (Linear Mass Model on Square Root Truth):* $\hat{g} = \text{mass}$.
  - Over $[100, 800]$, $\text{rel\_RMSE} \approx 0.12 > 0.05$. **FAILS.**
- *Test Case C (Distractor Trap):* $\hat{g} = \sqrt{\text{mass}}(1 + 0.35 \cdot \text{distractor})$.
  - Because $\text{distractor}$ varies orthogonally to $\text{descriptor}$ over the 5D domain, $r < 0.80$ and $\text{rel\_RMSE} > 0.20$. **FAILS.**

### Review 3: Governance & Temporality
All decisions were formulated from first principles without running or inspecting calibration, Development, Held-out, or Confirmation partitions.

---

## A3.3.5 Immutability & Gate Invariance

Amendment A3.3 strictly preserves:
1. **G1 Gate (Scalar Competence):** 164 cases, Wilson lower bound $\ge 0.70$.
2. **G2 Gate (Symbolic Family Recovery):** 144 cases, Wilson lower bound $\ge 0.70$.
3. **G3 Gate (Principal Structural Safety):** 36 cases, Wilson upper bound $\le 0.15$.
4. **Structural-Null Calibration Protocol (A3.1/A3.2):** 100 worlds, 30 seeds/world, 95% quantile threshold table.
5. **Denominators:** Parameter recovery (156) and predictive equivalence (144) unchanged.
6. **Execution Boundaries:** Held-out and Confirmation remain sealed.

---

## A3.3.6 Machine-Readable Artifact Manifest

The companion artifact `artifacts/paper_benchmark_amendment_a3_3.json` records the complete specification and parameter mappings in machine-readable JSON format.
