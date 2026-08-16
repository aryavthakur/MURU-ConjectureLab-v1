"""The five preregistered closed-form oracle candidates (MURU_V2_IDENTIFIABILITY
_STUDY_DESIGN.md section 3.3, MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json E3
`candidate_models`). No search, no grammar, no complexity penalty -- each
candidate is fit directly against the estimated per-compound `g_hat` by
nonlinear least squares.

    M_mass  : g = a * mass^b
    M_affine: g = a * mass^b * (1 + c*descriptor)
    M_sat   : g = a * mass^b * (1 + c*descriptor/(1+descriptor))
    M_exp   : g = a * mass^b * exp(c*descriptor)
    M_inter : g = a * mass^b * (1 + c*descriptor*descriptor2)

Selection statistics: BIC (fit on the training split) and validation R2
(fit on training, scored on validation), reported as two independent,
never-combined oracle-selection criteria, per the frozen decision criterion.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import stats
from scipy.optimize import curve_fit

MODEL_IDS = ("M_mass", "M_affine", "M_sat", "M_exp", "M_inter")

#: MURU_V2_REMEDIATION_EXPERIMENT_PLAN.json "nearest_rival_declared_in_advance"
NEAREST_RIVAL = {
    "M_affine": "M_mass",
    "M_sat": "M_affine",
    "M_exp": "M_affine",
    "M_inter": "M_affine",
}

#: Truth family -> the oracle candidate that IS that family's own functional form.
FAMILY_TO_MODEL = {
    "mass_power": "M_mass",
    "mass_affine_descriptor": "M_affine",
    "mass_saturating_descriptor": "M_sat",
    "mass_exponential_descriptor": "M_exp",
    "mass_interaction": "M_inter",
}
MODEL_TO_FAMILY = {v: k for k, v in FAMILY_TO_MODEL.items()}

N_PARAMS = {"M_mass": 2, "M_affine": 3, "M_sat": 3, "M_exp": 3, "M_inter": 3}


def _f_mass(X, a, b):
    mass = X[0]
    return a * mass ** b


def _f_affine(X, a, b, c):
    mass, descriptor = X[0], X[1]
    return a * mass ** b * (1 + c * descriptor)


def _f_sat(X, a, b, c):
    mass, descriptor = X[0], X[1]
    return a * mass ** b * (1 + c * descriptor / (1 + descriptor))


def _f_exp(X, a, b, c):
    mass, descriptor = X[0], X[1]
    return a * mass ** b * np.exp(c * descriptor)


def _f_inter(X, a, b, c):
    mass, descriptor, descriptor2 = X[0], X[1], X[2]
    return a * mass ** b * (1 + c * descriptor * descriptor2)


_MODEL_FUNCS = {
    "M_mass": _f_mass,
    "M_affine": _f_affine,
    "M_sat": _f_sat,
    "M_exp": _f_exp,
    "M_inter": _f_inter,
}

_MODEL_COVARIATES = {
    "M_mass": ("mass",),
    "M_affine": ("mass", "descriptor"),
    "M_sat": ("mass", "descriptor"),
    "M_exp": ("mass", "descriptor"),
    "M_inter": ("mass", "descriptor", "descriptor2"),
}


@dataclass
class ModelFit:
    model_id: str
    converged: bool
    params: dict = field(default_factory=dict)
    param_se: dict = field(default_factory=dict)
    rss_train: float = float("nan")
    n_train: int = 0
    k_params: int = 0
    bic: float = float("nan")
    r2_train: float = float("nan")
    r2_val: float = float("nan")
    r2_test: float = float("nan")
    rss_val: float = float("nan")
    rss_test: float = float("nan")
    n_val: int = 0
    n_test: int = 0
    pred_val: np.ndarray | None = None
    resid_val: np.ndarray | None = None


def _design(frame, covariates):
    return np.vstack([np.asarray(frame[name], dtype=float) for name in covariates])


def _r2(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    if ss_tot <= 0:
        return float("nan")
    return 1.0 - ss_res / ss_tot


def _mass_loglog_init(mass: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Closed-form OLS in log-log space, used only as a curve_fit initial guess."""
    X = np.vstack([np.ones_like(mass), np.log(mass)]).T
    coef, *_ = np.linalg.lstsq(X, np.log(np.clip(y, 1e-12, None)), rcond=None)
    log_a, b0 = coef
    return float(np.exp(log_a)), float(b0)


def fit_one_model(model_id: str, train: dict, val: dict, test: dict) -> ModelFit:
    """`train`/`val`/`test` are dicts of numpy arrays: mass, descriptor,
    descriptor2, g (the target -- the ESTIMATED g_hat, per the frozen
    Phi/g estimation stage, not the planted truth)."""
    covariates = _MODEL_COVARIATES[model_id]
    func = _MODEL_FUNCS[model_id]
    k = N_PARAMS[model_id]

    X_train = _design(train, covariates)
    y_train = train["g"]

    a0, b0 = _mass_loglog_init(train["mass"], y_train)
    if model_id == "M_mass":
        p0 = [a0, b0]
    else:
        p0 = [a0, b0, 0.3]

    fit = ModelFit(model_id=model_id, converged=False, k_params=k, n_train=len(y_train))
    try:
        popt, pcov = curve_fit(func, X_train, y_train, p0=p0, maxfev=20000)
    except Exception:
        return fit

    if not np.all(np.isfinite(popt)):
        return fit

    param_names = ("a", "b") if model_id == "M_mass" else ("a", "b", "c")
    fit.params = {name: float(v) for name, v in zip(param_names, popt)}
    if np.all(np.isfinite(pcov)):
        se = np.sqrt(np.clip(np.diag(pcov), 0, None))
        fit.param_se = {name: float(v) for name, v in zip(param_names, se)}
    else:
        fit.param_se = {name: float("nan") for name in param_names}

    pred_train = func(X_train, *popt)
    resid_train = y_train - pred_train
    fit.rss_train = float(np.sum(resid_train ** 2))
    fit.r2_train = _r2(y_train, pred_train)
    n = fit.n_train
    fit.bic = n * np.log(max(fit.rss_train / n, 1e-300)) + k * np.log(n)

    X_val = _design(val, covariates)
    y_val = val["g"]
    pred_val = func(X_val, *popt)
    fit.pred_val = pred_val
    fit.resid_val = y_val - pred_val
    fit.rss_val = float(np.sum(fit.resid_val ** 2))
    fit.n_val = len(y_val)
    fit.r2_val = _r2(y_val, pred_val)

    X_test = _design(test, covariates)
    y_test = test["g"]
    pred_test = func(X_test, *popt)
    fit.rss_test = float(np.sum((y_test - pred_test) ** 2))
    fit.n_test = len(y_test)
    fit.r2_test = _r2(y_test, pred_test)

    fit.converged = True
    return fit


def fit_all_models(train: dict, val: dict, test: dict) -> dict[str, ModelFit]:
    return {model_id: fit_one_model(model_id, train, val, test) for model_id in MODEL_IDS}


def select_by_bic(fits: dict[str, ModelFit]) -> str | None:
    candidates = {m: f.bic for m, f in fits.items() if f.converged and np.isfinite(f.bic)}
    if not candidates:
        return None
    return min(candidates, key=candidates.get)


def select_by_val_r2(fits: dict[str, ModelFit]) -> str | None:
    candidates = {m: f.r2_val for m, f in fits.items() if f.converged and np.isfinite(f.r2_val)}
    if not candidates:
        return None
    return max(candidates, key=candidates.get)


def nested_lrt_p(restricted: ModelFit, full: ModelFit) -> float:
    """Standard nested likelihood-ratio test on TRAINING RSS, restricted in
    full (restricted = full with c fixed at 0, valid for every one of the
    four descriptor families against M_mass: each reduces to M_mass exactly
    at c=0). df = difference in free-parameter count (always 1 here)."""
    if not (restricted.converged and full.converged):
        return float("nan")
    if restricted.rss_train <= 0 or full.rss_train <= 0:
        return float("nan")
    df = full.k_params - restricted.k_params
    if df <= 0:
        return float("nan")
    lr_stat = restricted.n_train * np.log(max(restricted.rss_train / full.rss_train, 1.0))
    lr_stat = max(lr_stat, 0.0)
    return float(stats.chi2.sf(lr_stat, df=df))


def vuong_p(model_a: ModelFit, model_b: ModelFit) -> float:
    """Vuong (1989) non-nested test on the VALIDATION split, for the three
    same-parameter-count non-nested rival pairs (M_sat/M_exp/M_inter vs
    M_affine). Two-sided normal p-value on the standardised mean
    pointwise log-likelihood difference under a Gaussian-error assumption
    with each model's own MLE sigma^2 = RSS_val / n_val."""
    if not (model_a.converged and model_b.converged):
        return float("nan")
    n = model_a.n_val
    if n != model_b.n_val or n < 2:
        return float("nan")
    sigma2_a = max(model_a.rss_val / n, 1e-300)
    sigma2_b = max(model_b.rss_val / n, 1e-300)
    ll_a = -0.5 * np.log(2 * np.pi * sigma2_a) - (model_a.resid_val ** 2) / (2 * sigma2_a)
    ll_b = -0.5 * np.log(2 * np.pi * sigma2_b) - (model_b.resid_val ** 2) / (2 * sigma2_b)
    diff = ll_a - ll_b
    sd = float(np.std(diff, ddof=1))
    if sd <= 0 or not np.isfinite(sd):
        return float("nan")
    v_stat = np.sqrt(n) * float(np.mean(diff)) / sd
    return float(2 * (1 - stats.norm.cdf(abs(v_stat))))


def true_vs_mass_lrt_p(true_model_id: str, fits: dict[str, ModelFit]) -> float:
    if true_model_id == "M_mass":
        return float("nan")
    return nested_lrt_p(fits["M_mass"], fits[true_model_id])


def true_vs_rival_lrt_p(true_model_id: str, fits: dict[str, ModelFit]) -> float:
    rival_id = NEAREST_RIVAL.get(true_model_id)
    if rival_id is None:
        return float("nan")
    if rival_id == "M_mass":
        # M_affine's rival is M_mass: nested, reuse the classical chi2 LRT.
        return nested_lrt_p(fits["M_mass"], fits[true_model_id])
    # M_sat/M_exp/M_inter vs M_affine: same parameter count, non-nested ->
    # Vuong's test rather than a chi2 LRT (which requires nesting).
    return vuong_p(fits[true_model_id], fits[rival_id])
