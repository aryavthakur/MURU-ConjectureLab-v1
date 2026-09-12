import os, numpy as np, pytest
from muru.wur_stage2 import cv as CV, candidates as CA, folds as FO
from muru.wur_stage2 import arms_v1 as AV
from muru.wur_stage2 import profile2 as P2
M = os.environ.get("MUT")
def apply():
    if M == "rel_denom":
        def compare(c, ref):
            pc, pr = c.p1_vector(), ref.p1_vector(); d = pc - pr; rel = (pr - pc) / pc
            return {"ref": ref.arm_id, "n_folds": int(len(d)), "wins": int((pc < pr).sum()), "mean_rel_improvement": float(rel.mean()),
                    "mean_diff": float(d.mean()), "se_diff": float(d.std(ddof=1)/np.sqrt(len(d))), "mean_P1": float(pc.mean()), "ref_mean_P1": float(pr.mean()),
                    "sd_P1": float(pc.std(ddof=1)), "ref_sd_P1": float(pr.std(ddof=1))}
        CV.compare = compare
    elif M == "wins_nonstrict":
        orig = CV.compare
        def compare(c, ref):
            o = orig(c, ref); o["wins"] = int((c.p1_vector() <= ref.p1_vector()).sum()); return o
        CV.compare = compare
    elif M == "min_wins_13": CA.MIN_WINS_VS_S2A = 13
    elif M == "min_wins_b1_13": CA.MIN_WINS_VS_B1 = 13
    elif M == "min_wins_b0_14": CA.MIN_WINS_VS_B0 = 14
    elif M == "rel_006": CA.MIN_REL_IMPROVEMENT = 0.06
    elif M == "s5_2x": CA.MAX_S5_RATIO = 2.0
    elif M == "s4_strict":
        src = open(CA.__file__).read().replace("s4_c <= s4_ref", "s4_c < s4_ref"); exec(compile(src, CA.__file__, "exec"), CA.__dict__)
    elif M == "tie_2se":
        src = open(CA.__file__).read().replace("diff.mean() <= se", "diff.mean() <= 2 * se"); exec(compile(src, CA.__file__, "exec"), CA.__dict__)
    elif M == "tie_params_numeric_swap":
        src = open(CA.__file__).read().replace('(r["n_features"], str(r["n_params"]), r["P1"])', '(r["n_features"], -float(r["n_params"]) if str(r["n_params"]).isdigit() else 0, r["P1"])'); exec(compile(src, CA.__file__, "exec"), CA.__dict__)
    elif M == "beats_first5":
        src = open(CA.__file__).read().replace("list(cond)[:6]", "list(cond)[:5]"); exec(compile(src, CA.__file__, "exec"), CA.__dict__)
    elif M == "cat_factor_3": CV.CATASTROPHIC_FACTOR = 3.0
    elif M == "s8_flip":
        src = open(CV.__file__).read().replace("keep = ok & (conf >= thr)", "keep = ok & (conf <= thr)"); exec(compile(src, CV.__file__, "exec"), CV.__dict__)
    elif M == "b0_unsorted":
        src = open(CV.__file__).read().replace("held = sorted(assign.index[assign == k])\n            train = sorted(assign.index[assign != k])\n            arm = B0NullProfile()", "held = list(assign.index[assign == k])[::-1]\n            train = sorted(assign.index[assign != k])\n            arm = B0NullProfile()"); exec(compile(src, CV.__file__, "exec"), CV.__dict__)
    elif M == "loeo_wrong_eref":
        src = open(CV.__file__).read().replace("e_ref=ENERGY_SCALE,", "e_ref=45.0,"); exec(compile(src, CV.__file__, "exec"), CV.__dict__)
    elif M == "predict_no_scale":
        src = open(CV.__file__).read().replace("u = (np.asarray(energies, float) / ENERGY_SCALE)[None, :] / g[:, None]", "u = (np.asarray(energies, float) / 45.0)[None, :] / g[:, None]"); exec(compile(src, CV.__file__, "exec"), CV.__dict__)
    elif M == "inner_unweighted":
        src = open(CV.__file__).read().replace("m = Ridge(alpha=a).fit(X[tr], log_g[tr], sample_weight=w[tr])", "m = Ridge(alpha=a).fit(X[tr], log_g[tr])"); exec(compile(src, CV.__file__, "exec"), CV.__dict__)
    elif M == "inner_on_all":
        src = open(FO.__file__).read().replace("seed=INNER_SEED_BASE + outer_fold)", "seed=INNER_SEED_BASE)"); exec(compile(src, FO.__file__, "exec"), FO.__dict__)
    elif M == "logit_inverse_wrong":
        src = open(P2.__file__).read().replace("a = 1.01 / (1 + np.exp(-self.models_[\"logit_a\"][0].predict(X))) - 0.01", "a = 1.0 / (1 + np.exp(-self.models_[\"logit_a\"][0].predict(X)))"); exec(compile(src, P2.__file__, "exec"), P2.__dict__)
    elif M == "a_clip_none":
        src = open(P2.__file__).read().replace("a = np.clip(a, 0.0, 0.9)", "a = a"); exec(compile(src, P2.__file__, "exec"), P2.__dict__)
    elif M == "boot_no_pair_guard":
        src = open(CV.__file__).read().replace("for k in keys if r in c.per_compound[k] and r in ref.per_compound[k]]", "for k in keys]"); exec(compile(src, CV.__file__, "exec"), CV.__dict__)
    elif M == "p1_sd_ddof0":
        src = open(CV.__file__).read().replace('"P1_sd": float(result.p1_vector().std(ddof=1))', '"P1_sd": float(result.p1_vector().std(ddof=0))'); exec(compile(src, CV.__file__, "exec"), CV.__dict__)
apply()
