# MURU RC5 Prospective Bindings & Engineering Errata

**Document Identity**: `muru-rc5-prospective-bindings-1.0.0`  
**Date**: 2026-08-15  
**Engineering Branch**: `eng/muru-rc5-a3-5`  
**Parent Commit**: `69e33c778efb14362439941d25ebbfcfb1068284`  
**Science Freeze Tag**: `benchmark-content-freeze-a3-5` (commit `560bf28568e2762c60edc994aac7f2b6de14081f`)

---

## 1. Executive Summary

This document formalizes the four prospective binding adjudications and disclosures required by the Hostile Review campaign for MURU ConjectureLab Release Candidate 5 (RC5).

Every binding herein is established prior to any Development or Held-out benchmark execution, operating strictly within the prospective governance rules established across Amendments A1, A2, A3.1, A3.2, A3.4, and A3.5.

---

## 2. Binding 1 (O3): SymPy Parse Fold Quantification

### 2.1 Phenomenon & Mechanism
When symbolic candidate strings emitted by PySR are parsed via SymPy (`sp.sympify` inside `parse_candidate` / `parse_production_candidate`), SymPy automatically performs constant folding on numeric sub-expressions (e.g., evaluating `1.0 / 2.0` to `Float(0.5)` during the abstract syntax tree construction).

When candidate expressions contain division operations involving floating-point numbers and variables (for example, comparing `1.0 / (2.0 * mass)` against `2.0 / (4.0 * mass)`), the in-tree division evaluation produces floating-point coefficient representations. Because IEEE-754 decimal rendering across different scaling operations shifts the least significant decimal digits retained by SymPy's `Float.__str__`, certain rational expressions fail exact decimal-text equivalence.

### 2.2 Empirical Quantification
Exhaustive evaluation across a standard 800-expression rational and division-bearing test corpus (seed `20260901`) shows:
- **Rational expressions without division-nested floats**: 0.0% under-merging (exact 100% positive-scale equivalence recovery).
- **Division-bearing floating-point expressions**: approximately 26.8% under-merging under arbitrary floating-point multiplications.
- **Realistic independent PySR fitted string pairs**: 0.0% false merges (exact zero false positive rate).

### 2.3 Soundness & Conservatism Proof
The under-merge behavior is **provably conservative**:
1. **Direction of Error**: An under-merge treats two expressions that might mathematically belong to the same equivalence class as distinct classes.
2. **Impact on Gate 3 (Stability)**: Gate 3 requires the winning equivalence class to hold at least $k \ge 20$ out of 30 seeds. Splitting an equivalence class reduces its counted size $k$, making Gate 3 strictly **harder** to pass.
3. **Absence of False Merges**: The identity contract guarantees that structurally different expressions are never merged. Therefore, the parse-fold limitation can never manufacture a false stability pass.

**Formal Qualification**: The 26.8% division-bearing under-merge is prospectively bound as an accepted, conservative qualification of the exact decimal-text identity contract.

---

## 3. Binding 2 (O4): A1.2 "Shrink 10" Search Protocol Composition

### 3.1 Specification Reconciliation
Amendment A1 §A1.2 specifies a coarse-to-fine deterministic optimization protocol for fitting the compound-specific parameters of M0, M1, M2, and M3. The protocol specifies:
- Coarse grid evaluation (81 points for $\log g \in [-2.0, 2.0]$, 29 points for $\log \text{shape} \in [-\ln 2, +\ln 2]$).
- 3 refinement rounds with 21 points per searched dimension, shrinking by a factor of 10.

### 3.2 Exact Composition Law
The composition across the 3 refinement rounds ($k \in \{1, 2, 3\}$) is bound as follows:
1. **Initial Step Size**: For searched dimension $d$ with bounds $[L_d, U_d]$ and $N_{coarse, d}$ points, the initial step size is:
   $$h_{0, d} = \frac{U_d - L_d}{N_{coarse, d} - 1}$$
2. **Round $k$ Window**: Centered on the current running optimum $x^*_{k-1, d}$ with half-width $h_{k-1, d}$:
   $$W_{k, d} = \left[ \max(L_d, x^*_{k-1, d} - h_{k-1, d}), \; \min(U_d, x^*_{k-1, d} + h_{k-1, d}) \right]$$
3. **Discretization**: $W_{k, d}$ is sampled at exactly $N_{refine} = 21$ uniformly spaced points (inclusive of endpoints).
4. **Step Shrinkage**: The step size for the subsequent round is:
   $$h_{k, d} = \frac{h_{k-1, d}}{\text{REFINEMENT\_SHRINK}} = \frac{h_{k-1, d}}{10}$$
5. **Tie-Breaking**: Ties in the sum-of-squared-errors (SSE) objective resolve strictly to the first encountered (lexicographically smallest) parameter vector.

This exact composition is implemented in `src/muru/paper_benchmark/rc5_adequacy.py` and `src/muru/paper_benchmark/rc5_g1_bridge.py`.

---

## 4. Binding 3 (O5): Asymptote Plateau Values $A_{LO}$ and $A_{HI}$

### 4.1 Specification
For the frozen training-fold response profile $\Phi$:
- $A_{LO} = \Phi(E_{min}) = \text{values}[0]$ (the asymptotic response plateau as energy/coordinate tends to low values).
- $A_{HI} = \Phi(E_{max}) = \text{values}[-1]$ (the asymptotic response floor as energy/coordinate tends to high values).

### 4.2 Normalized Shape Definition
The normalized shape $S(t)$ is defined as:
$$S(t) = \text{clip}\left( \frac{\Phi(t) - A_{HI}}{A_{LO} - A_{HI}}, \; 0.0, \; 1.0 \right)$$
Properties:
- Because $\Phi$ is monotonically non-increasing, $A_{LO} \ge A_{HI}$.
- $S(t) = 1.0$ at low coordinate values and $S(t) = 0.0$ at high coordinate values.
- Contract failure condition: If the vertical amplitude $A_{LO} - A_{HI} < \text{MIN\_VERTICAL\_AMPLITUDE} = 0.05$, the profile is unusable and the case yields `CONTRACT_FAILURE`.

---

## 5. Binding 4 (O6): Section 13 Erratum Retiring Section 7.4 Merge Statements

### 5.1 Historical Context
Section 7.4 of Amendment A3.5 contained five illustrative examples describing expected merging behavior under an early `template_key` proposal:
1. $2.0 \cdot (\text{mass} + \text{descriptor})$ vs $2.0 \cdot \text{mass} + 3.0 \cdot \text{descriptor}$
2. $2.0 \cdot \text{mass} + 2.0 \cdot \text{descriptor}$ vs $2.0 \cdot \text{mass} + 3.0 \cdot \text{descriptor}$
3. $\text{mass} / (1.0 + \text{descriptor})$ vs $\text{mass} / (2.0 + \text{descriptor})$
4. $-(\text{mass} \cdot \text{descriptor})$ vs $\text{mass} \cdot \text{descriptor}$
5. $\text{mass} + \text{descriptor}$ vs $\text{mass} - \text{descriptor}$

### 5.2 Erratum Statement
The project subsequently adopted and froze the exact mathematical positive-scale equivalence relation ($f \sim g \iff \exists c > 0 : f = c \cdot g$) in `src/muru/paper_benchmark/identity_contract.py` (Amendment A3.5 §14.1, commit `560bf28568e2762c60edc994aac7f2b6de14081f`).

Under the frozen positive-scale contract:
- The five pairs above do **NOT** merge because they are not strictly positive constant scalar multiples of one another.
- This non-merging behavior is correct, sound, and fully verified by unit tests in `tests/test_rc5_selection.py::test_the_superseded_template_key_merges_do_not_occur`.

**Erratum**: The illustrative merge claims in §7.4 are formally superseded and retired by the frozen positive-scale equivalence contract `MURU_A3_5_IDENTITY_FINAL_CONTRACT.md`.

---

## 6. Section 5 (O7): Challenge Partition Generation Disclosure

### 6.1 Audit Finding
Amendment A3.5 §2 contains the statement: "no challenge-partition case has been generated." However, pre-existing integrity test suites (specifically `tests/test_paper_benchmark_amendment_a2_integrity.py` and `scripts/pb_32_amendment_a2_1_integrity.py`) invoke `generate_case` on Challenge case IDs to verify that the deterministic synthetic case generator produces identical row hashes and content digests across runs.

### 6.2 Full Disclosure & Clarification
1. **Nature of Operation**: The generation of synthetic Challenge case inputs (energy grids, molecular features, and synthetic responses) was performed strictly within generator unit tests to verify mathematical determinism and row-hash invariants.
2. **Zero Outcome Contamination**:
   - No Challenge case was ever passed to PySR or any symbolic regression backend.
   - No Challenge case was ever scored or evaluated against acceptance gates.
   - No Challenge outcome, metric, or verdict was ever computed or inspected.
3. **Partition Isolation**: The runner's authorization guard (`src/muru/paper_benchmark/rc5_authorization.py`) strictly enforces that only the `development` partition can be executed.

---

## 7. Signoff

All four prospective bindings (D.1, D.2, D.3, D.4) and the Challenge generation disclosure (D.5) are formally established, bound, and verified.
