"""Frozen spectrum-similarity layer for MURU CE interface adjudication, Design A.

This module is the ONLY place where the Design A similarity endpoints are defined.
Every convention is an explicit, named, documented parameter whose default is taken
from FROZEN_CONFIG. The module refuses to run with a changed convention unless the
caller passes allow_override=True, and it publishes a sha256 of its own frozen
configuration so the freeze manifest can pin it.

Endpoints
---------
cosine_similarity_untransformed(pred, obs, ...)  PRIMARY
    Cosine similarity computed on LINEAR relative intensities. The ms-pred
    checkpoints (ICEBERG 2.1 msg_simulation, GLACIER MassSpecGym) emit intensities
    on a sqrt scale, because their intensity heads are trained against targets that
    ms-pred max-normalizes and then square-roots
    (ms-pred@ed8311f src/ms_pred/common/misc_utils.py:2207-2210 and :2220-2223).
    This endpoint inverts that transform EXACTLY ONCE, by squaring the prediction
    side, and applies no transform at all to the observed side, which the study
    supplies in linear relative units. Nothing else is transformed.

jensen_shannon_similarity(pred, obs, ...)  SECONDARY (robustness)
    Jensen-Shannon similarity. Both binned vectors are treated as probability
    distributions after sum (L1) normalization. With m = (p + q) / 2,
        JSD = 0.5 * KL(p || m) + 0.5 * KL(q || m), in NATS (natural logarithm),
        JSS = 1 - JSD / ln(2),
    which lies in [0, 1] because JSD in nats is bounded above by ln 2.
    This is exactly MassSpecGym's js_sim
    (massspecgym@main massspecgym/simulation_utils/spec_utils.py:247-294) and is
    also algebraically identical to ms-pred's entropy_sim
    (ms-pred@ed8311f analysis/spec_pred_eval.py:37-51), since
    1 - (2 H(m) - H(p) - H(q)) / ln 4 == 1 - JSD / ln 2.

Provenance of every convention, with file:line citations and VERIFIED / INFERRED
marks, is in
artifacts/ce_interface_adjudication/design_a/notes/similarity_semantics.md

Style note: ordinary hyphens only, no em dashes or en dashes.
"""

from __future__ import annotations

import hashlib
import json
from types import MappingProxyType
from typing import Mapping, Sequence, Tuple

import numpy as np

__all__ = [
    "FROZEN_CONFIG",
    "FROZEN_CONFIG_SHA256",
    "frozen_config_sha256",
    "frozen_config_json",
    "bin_index",
    "bin_width_da",
    "prepare_spectrum",
    "cosine_similarity_untransformed",
    "jensen_shannon_similarity",
    "ConfigOverrideError",
]


# ---------------------------------------------------------------------------
# Frozen configuration
# ---------------------------------------------------------------------------

_NUM_BINS = 15000
_MASS_UPPER_LIMIT = 1500.0

# Bin grid follows ms-pred exactly: scale = (num_bins - 1) / mass_upper_limit,
# bin index = floor(mz * scale) + 1, bins kept when 0 <= index < num_bins.
# ms-pred@ed8311f src/ms_pred/common/misc_utils.py:2337 and :2346-2349
# (dense) and :180-184 (sparse).
_BIN_WIDTH_DA = _MASS_UPPER_LIMIT / (_NUM_BINS - 1)  # 0.10000666711114074 Da

_FROZEN_CONFIG_DICT = {
    # Identity
    "config_version": "muru.ce_interface_adjudication.design_a.spectrum_similarity.v1",
    "reference_ms_pred_commit": "ed8311f22958cb37f055b663b5f56c5c77a2ee33",
    "reference_massspecgym_ref": "pluskal-lab/MassSpecGym@main",

    # Binning
    "num_bins": _NUM_BINS,
    "mass_upper_limit_da": _MASS_UPPER_LIMIT,
    "bin_index_rule": "floor(mz * (num_bins - 1) / mass_upper_limit) + 1",
    "bin_validity_rule": "keep bins with 0 <= index < num_bins, drop all others",
    "bin_width_da": _BIN_WIDTH_DA,

    # Tolerance
    "tolerance_value": _BIN_WIDTH_DA,
    "tolerance_unit": "Da",
    "tolerance_application": (
        "fixed grid bin coincidence: two peaks match if and only if they fall in "
        "the same bin of the fixed grid. There is no symmetric +/- window and no "
        "ppm tolerance anywhere in the endpoint. The effective match width is one "
        "bin, so the worst case separation of two matched peaks is one bin width "
        "and two peaks separated by less than one bin width may still fail to "
        "match when a bin boundary falls between them."
    ),

    # Pooling
    "pool_fn": "add",
    "pool_summation_order": (
        "peaks are lexicographically sorted by (bin index, intensity, mz) before "
        "the within-bin reduction, so the result is bit identical under any "
        "permutation of the input peak order"
    ),

    # Intensity handling
    "pred_inverse_transform": "square",
    "obs_inverse_transform": "identity",
    "inverse_transform_rationale": (
        "ms-pred stores and predicts sqrt scale relative intensities. The study "
        "endpoint is preregistered as untransformed, so the prediction side is "
        "squared exactly once to recover linear relative intensity. The observed "
        "side is supplied in linear relative units and is never routed through "
        "ms-pred process_spec_file, so no transform is applied to it."
    ),
    "normalization_method": "max",
    "normalization_order": (
        "drop_nonfinite -> drop_nonpositive_intensity -> mass_cutoff -> "
        "inverse_transform -> max_normalize -> bin -> pool(add) -> "
        "precursor_treatment -> (metric specific L1 normalization for "
        "jensen_shannon_similarity only)"
    ),
    "normalization_is_inert": (
        "both endpoints are invariant to a positive global rescale of either side, "
        "so max normalization cannot change either value beyond float rounding. It "
        "is frozen anyway so that the intermediate binned vectors are reproducible."
    ),

    # Precursor and mass cutoff
    "precursor_treatment": "keep",
    "precursor_treatment_options": "keep | remove_above_parent_minus_1",
    "precursor_removal_offset_da": 1.0,
    "precursor_removal_index_rule": (
        "int((parent_mass - precursor_removal_offset_da) * num_bins / "
        "mass_upper_limit); bins with index >= this value are dropped. Note this "
        "reproduces ms-pred's own index rule, which uses num_bins / "
        "mass_upper_limit (= 10.0) and not the binning scale (num_bins - 1) / "
        "mass_upper_limit (= 9.999333...)."
    ),
    "mass_cutoff_offset_da": 1.0,
    "mass_cutoff_rule": (
        "when parent_mass is given, keep peaks with mz <= parent_mass + "
        "mass_cutoff_offset_da; when parent_mass is None, apply no mass cutoff"
    ),
    "low_mz_cutoff": "none",

    # Degenerate cases
    "nonfinite_handling": "drop_peak",
    "nonpositive_intensity_handling": "drop_peak",
    "empty_spectrum_value": 0.0,
    "zero_norm_value": 0.0,
    "disjoint_support_value": 0.0,
    "identical_prepared_spectra_value": 1.0,
    "output_clip_lo": 0.0,
    "output_clip_hi": 1.0,
    "length_mismatch_behaviour": "raise ValueError",

    # Jensen-Shannon specifics
    "js_log_base": "e (natural log), divided by ln(2) so the range is [0, 1]",
    "js_probability_normalization": "sum (L1) over the binned vector",
    "js_zero_handling": (
        "a bin absent from one side contributes nothing to that side's KL term; "
        "0 * ln(0 / m) is defined as 0. The KL ratio is formed as p / m, never as "
        "ln(p) - ln(m), so a bin present on exactly one side contributes exactly "
        "p * ln(2)."
    ),

    # Numerics
    "dtype": "float64",
}

FROZEN_CONFIG: Mapping[str, object] = MappingProxyType(dict(_FROZEN_CONFIG_DICT))


def frozen_config_json() -> str:
    """Canonical JSON serialization of FROZEN_CONFIG, used for the sha256."""
    return json.dumps(dict(FROZEN_CONFIG), sort_keys=True, separators=(",", ":"))


def frozen_config_sha256() -> str:
    """sha256 of the canonical JSON serialization of FROZEN_CONFIG."""
    return hashlib.sha256(frozen_config_json().encode("utf-8")).hexdigest()


FROZEN_CONFIG_SHA256: str = frozen_config_sha256()


class ConfigOverrideError(RuntimeError):
    """Raised when a caller changes a frozen convention without allow_override."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_LN2 = float(np.log(2.0))

_DTYPES = {"float64": np.float64, "float32": np.float32}

SpectrumLike = Tuple[Sequence[float], Sequence[float]]


def _check_frozen(provided: Mapping[str, object], allow_override: bool) -> None:
    """Refuse to run with a modified convention unless explicitly overridden."""
    changed = []
    for key, value in provided.items():
        frozen_value = FROZEN_CONFIG[key]
        if isinstance(frozen_value, float) or isinstance(value, float):
            same = float(value) == float(frozen_value)
        else:
            same = value == frozen_value
        if not same:
            changed.append(f"{key}: frozen={frozen_value!r} given={value!r}")
    if changed and not allow_override:
        raise ConfigOverrideError(
            "Design A spectrum similarity refuses to run with a modified frozen "
            "configuration. Pass allow_override=True to run anyway, and record "
            "the deviation. Changed conventions:\n  " + "\n  ".join(changed)
        )


def bin_width_da(
    num_bins: int = _NUM_BINS,
    mass_upper_limit: float = _MASS_UPPER_LIMIT,
) -> float:
    """Width in Da of one bin of the fixed grid."""
    return float(mass_upper_limit) / (int(num_bins) - 1)


def bin_index(
    mz,
    num_bins: int = _NUM_BINS,
    mass_upper_limit: float = _MASS_UPPER_LIMIT,
):
    """ms-pred bin index for an m/z value or array.

    bin index = floor(mz * (num_bins - 1) / mass_upper_limit) + 1
    ms-pred@ed8311f src/ms_pred/common/misc_utils.py:2337, :2346
    """
    mz_arr = np.asarray(mz, dtype=np.float64)
    scale = (int(num_bins) - 1) / float(mass_upper_limit)
    out = np.floor(mz_arr * scale).astype(np.int64) + 1
    if np.ndim(mz) == 0:
        return int(out)
    return out


def _apply_inverse_transform(values: np.ndarray, transform: str) -> np.ndarray:
    """Invert the ms-pred intensity transform. Applied at most once, per side."""
    if transform == "identity":
        return values
    if transform == "square":
        # Exactly inverts np.sqrt for every non negative finite float.
        return np.square(values)
    raise ValueError(f"Unknown inverse transform: {transform!r}")


def _normalize(values: np.ndarray, method: str) -> np.ndarray:
    if method == "none":
        return values
    if method == "max":
        peak = values.max() if values.size else 0.0
        if not np.isfinite(peak) or peak <= 0.0:
            return values[:0]
        return values / peak
    if method == "sum":
        total = values.sum() if values.size else 0.0
        if not np.isfinite(total) or total <= 0.0:
            return values[:0]
        return values / total
    raise ValueError(f"Unknown normalization method: {method!r}")


def _pool(bin_idx: np.ndarray, values: np.ndarray, mz: np.ndarray, pool_fn: str):
    """Deterministic, permutation invariant within bin reduction."""
    if bin_idx.size == 0:
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=values.dtype)

    # Canonical order: bin index, then intensity, then mz. np.lexsort takes the
    # primary key last. This makes the within bin summation order a function of
    # the peak SET, not of the caller's peak ORDER.
    order = np.lexsort((mz, values, bin_idx))
    sorted_idx = bin_idx[order]
    sorted_vals = values[order]

    starts = np.r_[0, np.flatnonzero(np.diff(sorted_idx)) + 1]
    if pool_fn == "add":
        pooled = np.add.reduceat(sorted_vals, starts)
    elif pool_fn == "max":
        pooled = np.maximum.reduceat(sorted_vals, starts)
    else:
        raise ValueError(f"Unknown pool function: {pool_fn!r}")
    return sorted_idx[starts].astype(np.int64, copy=False), pooled


def prepare_spectrum(
    spectrum: SpectrumLike,
    *,
    inverse_transform: str,
    parent_mass: float | None = None,
    num_bins: int = _NUM_BINS,
    mass_upper_limit: float = _MASS_UPPER_LIMIT,
    pool_fn: str = "add",
    normalization_method: str = "max",
    precursor_treatment: str = "keep",
    mass_cutoff_offset_da: float = 1.0,
    precursor_removal_offset_da: float = 1.0,
    nonfinite_handling: str = "drop_peak",
    nonpositive_intensity_handling: str = "drop_peak",
    dtype: str = "float64",
):
    """Turn a raw (mz, intensity) pair into the frozen sparse binned vector.

    Returns
    -------
    (indices, values) : both 1D numpy arrays, indices strictly increasing int64,
        values the chosen float dtype and strictly positive. Either can be empty,
        which is the documented signal for a degenerate spectrum.
    """
    float_dtype = _DTYPES.get(dtype)
    if float_dtype is None:
        raise ValueError(f"Unknown dtype: {dtype!r}")

    mz_in, inten_in = spectrum
    mz = np.asarray(mz_in, dtype=np.float64).ravel()
    inten = np.asarray(inten_in, dtype=np.float64).ravel()
    if mz.shape[0] != inten.shape[0]:
        raise ValueError(
            "mz and intensity arrays must have the same length, got "
            f"{mz.shape[0]} and {inten.shape[0]}"
        )

    # 1. Non finite peaks. Frozen rule: drop the peak, never raise, never NaN out.
    if nonfinite_handling == "drop_peak":
        keep = np.isfinite(mz) & np.isfinite(inten)
    elif nonfinite_handling == "raise":
        if not (np.all(np.isfinite(mz)) and np.all(np.isfinite(inten))):
            raise ValueError("non finite value in spectrum")
        keep = np.ones(mz.shape[0], dtype=bool)
    else:
        raise ValueError(f"Unknown nonfinite_handling: {nonfinite_handling!r}")
    mz, inten = mz[keep], inten[keep]

    # 2. Non positive intensities. Frozen rule: drop (this covers zeros and
    #    negatives, including negative baseline artefacts).
    if nonpositive_intensity_handling == "drop_peak":
        keep = inten > 0.0
    elif nonpositive_intensity_handling == "raise":
        if np.any(inten <= 0.0):
            raise ValueError("non positive intensity in spectrum")
        keep = np.ones(mz.shape[0], dtype=bool)
    else:
        raise ValueError(
            f"Unknown nonpositive_intensity_handling: {nonpositive_intensity_handling!r}"
        )
    mz, inten = mz[keep], inten[keep]

    # 3. Mass cutoff relative to the parent mass.
    if parent_mass is not None and np.isfinite(float(parent_mass)):
        keep = mz <= (float(parent_mass) + float(mass_cutoff_offset_da))
        mz, inten = mz[keep], inten[keep]

    # 4. Intensity inverse transform, applied exactly once for this side.
    inten = _apply_inverse_transform(inten, inverse_transform)

    # 5. Per spectrum normalization.
    inten = _normalize(inten, normalization_method)
    if inten.size != mz.size:  # normalization signalled a degenerate spectrum
        return np.zeros(0, dtype=np.int64), np.zeros(0, dtype=float_dtype)

    inten = inten.astype(float_dtype, copy=False)

    # 6. Bin onto the fixed grid.
    idx = bin_index(mz, num_bins=num_bins, mass_upper_limit=mass_upper_limit)
    valid = (idx >= 0) & (idx < int(num_bins))
    idx, inten, mz = idx[valid], inten[valid], mz[valid]

    # 7. Pool within bins.
    idx, vals = _pool(idx, inten, mz, pool_fn)

    # 8. Precursor treatment, applied on bin indices exactly as ms-pred does.
    if precursor_treatment == "keep":
        pass
    elif precursor_treatment == "remove_above_parent_minus_1":
        if parent_mass is None or not np.isfinite(float(parent_mass)):
            raise ValueError(
                "precursor_treatment='remove_above_parent_minus_1' requires parent_mass"
            )
        cut = int(
            (float(parent_mass) - float(precursor_removal_offset_da))
            * int(num_bins)
            / float(mass_upper_limit)
        )
        keep = idx < cut
        idx, vals = idx[keep], vals[keep]
    else:
        raise ValueError(f"Unknown precursor_treatment: {precursor_treatment!r}")

    # 9. Anything that pooled to a non positive or non finite value is dropped.
    keep = np.isfinite(vals) & (vals > 0.0)
    return idx[keep], vals[keep].astype(float_dtype, copy=False)


def _identical(a_idx, a_val, b_idx, b_val) -> bool:
    return (
        a_idx.shape == b_idx.shape
        and a_val.shape == b_val.shape
        and np.array_equal(a_idx, b_idx)
        and np.array_equal(a_val, b_val)
    )


def _clip(value: float) -> float:
    lo = float(FROZEN_CONFIG["output_clip_lo"])
    hi = float(FROZEN_CONFIG["output_clip_hi"])
    if not np.isfinite(value):
        return float(FROZEN_CONFIG["zero_norm_value"])
    return float(min(max(value, lo), hi))


# ---------------------------------------------------------------------------
# PRIMARY endpoint
# ---------------------------------------------------------------------------

def cosine_similarity_untransformed(
    pred: SpectrumLike,
    obs: SpectrumLike,
    *,
    parent_mass: float | None = None,
    num_bins: int = _NUM_BINS,
    mass_upper_limit: float = _MASS_UPPER_LIMIT,
    pool_fn: str = "add",
    pred_inverse_transform: str = "square",
    obs_inverse_transform: str = "identity",
    normalization_method: str = "max",
    precursor_treatment: str = "keep",
    mass_cutoff_offset_da: float = 1.0,
    precursor_removal_offset_da: float = 1.0,
    nonfinite_handling: str = "drop_peak",
    nonpositive_intensity_handling: str = "drop_peak",
    dtype: str = "float64",
    allow_override: bool = False,
) -> float:
    """PRIMARY endpoint. Cosine similarity on LINEAR relative intensities.

    Parameters
    ----------
    pred : (mz array, intensity array)
        The checkpoint prediction, on ms-pred's sqrt intensity scale. It is
        squared exactly once (pred_inverse_transform='square') to recover linear
        relative intensity.
    obs : (mz array, intensity array)
        The observed spectrum, in LINEAR relative intensity. No transform is
        applied to it (obs_inverse_transform='identity'). The endpoint is
        invariant to the absolute scale of this side.
    parent_mass : float or None
        Precursor mass used for the mass cutoff and, if enabled, precursor
        removal. When None there is no mass cutoff.

    Deviation from ms-pred's own convention
    ---------------------------------------
    ms-pred's binned cosine (analysis/spec_pred_eval.py:24-34, :216) compares BOTH
    sides in ms-pred's sqrt space, because both sides are routed through
    common.process_spec_file which max normalizes and then square roots
    (src/ms_pred/common/misc_utils.py:2207-2210). This study deliberately does
    not do that, because it preregisters an UNTRANSFORMED endpoint. The deviation
    is not an invention: ms-pred itself ships --no-sqrt-inten, which squares the
    stored sqrt intensities back to linear before scoring
    (src/ms_pred/retrieval/retrieval_benchmark.py:87-91 and :211-217), and
    MassSpecGym's headline simulation metric cos_sim is likewise computed on
    untransformed intensities (massspecgym/models/simulation/base.py:165-174).

    Returns
    -------
    float in [0, 1]. Degenerate cases return 0.0 and never NaN, see FROZEN_CONFIG.
    """
    _check_frozen(
        {
            "num_bins": num_bins,
            "mass_upper_limit_da": mass_upper_limit,
            "pool_fn": pool_fn,
            "pred_inverse_transform": pred_inverse_transform,
            "obs_inverse_transform": obs_inverse_transform,
            "normalization_method": normalization_method,
            "precursor_treatment": precursor_treatment,
            "mass_cutoff_offset_da": mass_cutoff_offset_da,
            "precursor_removal_offset_da": precursor_removal_offset_da,
            "nonfinite_handling": nonfinite_handling,
            "nonpositive_intensity_handling": nonpositive_intensity_handling,
            "dtype": dtype,
        },
        allow_override,
    )

    common_kwargs = dict(
        parent_mass=parent_mass,
        num_bins=num_bins,
        mass_upper_limit=mass_upper_limit,
        pool_fn=pool_fn,
        normalization_method=normalization_method,
        precursor_treatment=precursor_treatment,
        mass_cutoff_offset_da=mass_cutoff_offset_da,
        precursor_removal_offset_da=precursor_removal_offset_da,
        nonfinite_handling=nonfinite_handling,
        nonpositive_intensity_handling=nonpositive_intensity_handling,
        dtype=dtype,
    )
    p_idx, p_val = prepare_spectrum(
        pred, inverse_transform=pred_inverse_transform, **common_kwargs
    )
    o_idx, o_val = prepare_spectrum(
        obs, inverse_transform=obs_inverse_transform, **common_kwargs
    )

    # Degenerate: empty prediction, empty observation, or zero norm on either side.
    if p_idx.size == 0 or o_idx.size == 0:
        return float(FROZEN_CONFIG["empty_spectrum_value"])

    # Exact case: bit identical prepared spectra score exactly 1.0.
    if _identical(p_idx, p_val, o_idx, o_val):
        return float(FROZEN_CONFIG["identical_prepared_spectra_value"])

    shared_p = np.isin(p_idx, o_idx)
    if not np.any(shared_p):
        # Exact case: disjoint supports have zero dot product.
        return float(FROZEN_CONFIG["disjoint_support_value"])
    shared_o = np.isin(o_idx, p_idx)

    # Both index arrays are strictly increasing, so the masked subsets align.
    dot = float(np.dot(p_val[shared_p], o_val[shared_o]))
    norm_p = float(np.sqrt(np.dot(p_val, p_val)))
    norm_o = float(np.sqrt(np.dot(o_val, o_val)))
    if norm_p <= 0.0 or norm_o <= 0.0:
        return float(FROZEN_CONFIG["zero_norm_value"])

    return _clip(dot / (norm_p * norm_o))


# ---------------------------------------------------------------------------
# SECONDARY endpoint
# ---------------------------------------------------------------------------

def jensen_shannon_similarity(
    pred: SpectrumLike,
    obs: SpectrumLike,
    *,
    parent_mass: float | None = None,
    num_bins: int = _NUM_BINS,
    mass_upper_limit: float = _MASS_UPPER_LIMIT,
    pool_fn: str = "add",
    pred_inverse_transform: str = "square",
    obs_inverse_transform: str = "identity",
    normalization_method: str = "max",
    precursor_treatment: str = "keep",
    mass_cutoff_offset_da: float = 1.0,
    precursor_removal_offset_da: float = 1.0,
    nonfinite_handling: str = "drop_peak",
    nonpositive_intensity_handling: str = "drop_peak",
    dtype: str = "float64",
    allow_override: bool = False,
) -> float:
    """SECONDARY robustness endpoint. Jensen-Shannon similarity in [0, 1].

    Definition
    ----------
    The two prepared binned vectors are sum (L1) normalized to probability
    distributions p and q over bin indices. With m = (p + q) / 2,

        KL(p || m) = sum_i p_i * ln(p_i / m_i)      (bins with p_i = 0 contribute 0)
        JSD        = 0.5 * KL(p || m) + 0.5 * KL(q || m)        [nats]
        JSS        = 1 - JSD / ln(2)

    The logarithm is the NATURAL logarithm and the divisor is ln(2), because JSD
    in nats is bounded above by ln 2. The range is therefore exactly [0, 1]:
    1.0 for identical distributions, 0.0 for disjoint supports.

    Zero handling: a bin present on only one side contributes p_i * ln(p_i / m_i)
    with m_i = p_i / 2, that is exactly p_i * ln 2, to that side's KL term and
    nothing to the other side's. The ratio p_i / m_i is formed directly rather
    than as ln(p_i) - ln(m_i), so this term is exact in floating point. A bin
    absent from a side contributes 0, the standard 0 * ln 0 = 0 convention.

    This matches MassSpecGym's js_sim exactly
    (massspecgym/simulation_utils/spec_utils.py:247-294, LN_2 at :28), and is
    algebraically identical to ms-pred's entropy_sim
    (ms-pred@ed8311f analysis/spec_pred_eval.py:37-51), which writes the same
    quantity as 1 - (2 H(m) - H(p) - H(q)) / ln 4.

    Returns
    -------
    float in [0, 1]. Degenerate cases return 0.0 and never NaN.
    """
    _check_frozen(
        {
            "num_bins": num_bins,
            "mass_upper_limit_da": mass_upper_limit,
            "pool_fn": pool_fn,
            "pred_inverse_transform": pred_inverse_transform,
            "obs_inverse_transform": obs_inverse_transform,
            "normalization_method": normalization_method,
            "precursor_treatment": precursor_treatment,
            "mass_cutoff_offset_da": mass_cutoff_offset_da,
            "precursor_removal_offset_da": precursor_removal_offset_da,
            "nonfinite_handling": nonfinite_handling,
            "nonpositive_intensity_handling": nonpositive_intensity_handling,
            "dtype": dtype,
        },
        allow_override,
    )

    common_kwargs = dict(
        parent_mass=parent_mass,
        num_bins=num_bins,
        mass_upper_limit=mass_upper_limit,
        pool_fn=pool_fn,
        normalization_method=normalization_method,
        precursor_treatment=precursor_treatment,
        mass_cutoff_offset_da=mass_cutoff_offset_da,
        precursor_removal_offset_da=precursor_removal_offset_da,
        nonfinite_handling=nonfinite_handling,
        nonpositive_intensity_handling=nonpositive_intensity_handling,
        dtype=dtype,
    )
    p_idx, p_val = prepare_spectrum(
        pred, inverse_transform=pred_inverse_transform, **common_kwargs
    )
    o_idx, o_val = prepare_spectrum(
        obs, inverse_transform=obs_inverse_transform, **common_kwargs
    )

    if p_idx.size == 0 or o_idx.size == 0:
        return float(FROZEN_CONFIG["empty_spectrum_value"])

    p_sum = float(p_val.sum())
    o_sum = float(o_val.sum())
    if not np.isfinite(p_sum) or not np.isfinite(o_sum) or p_sum <= 0.0 or o_sum <= 0.0:
        return float(FROZEN_CONFIG["zero_norm_value"])

    p = p_val / p_sum
    q = o_val / o_sum

    if _identical(p_idx, p, o_idx, q):
        return float(FROZEN_CONFIG["identical_prepared_spectra_value"])
    if not np.any(np.isin(p_idx, o_idx)):
        return float(FROZEN_CONFIG["disjoint_support_value"])

    union = np.union1d(p_idx, o_idx)
    p_full = np.zeros(union.shape[0], dtype=p.dtype)
    q_full = np.zeros(union.shape[0], dtype=q.dtype)
    p_full[np.searchsorted(union, p_idx)] = p
    q_full[np.searchsorted(union, o_idx)] = q
    m_full = 0.5 * (p_full + q_full)

    p_mask = p_full > 0.0
    q_mask = q_full > 0.0
    kl_p = float(np.sum(p_full[p_mask] * np.log(p_full[p_mask] / m_full[p_mask])))
    kl_q = float(np.sum(q_full[q_mask] * np.log(q_full[q_mask] / m_full[q_mask])))
    jsd = 0.5 * (kl_p + kl_q)

    return _clip(1.0 - jsd / _LN2)
