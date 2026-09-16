#!/usr/bin/env python3
"""P2: static read of CE-related tensors from the frozen ms-pred checkpoints.

Reads PyTorch zip checkpoints WITHOUT torch (custom unpickler -> numpy) and
extracts only parameter tensors. No model is built and no inference is run.

Extracted per checkpoint:
  * collision_embedder_denominators (frozen nn.Parameter)
  * collision_embed_merged (NaN substitute)
  * adduct_embedder, instrument_embedder (frozen one-hot / multi-hot tables)
  * the first linear input projection(s) that consume the concatenated node
    features [atom feats | adduct | CE sinusoid (64) | instrument (4)], so the
    per-column weight norms of the CE block can be reported.

Usage: p2_read_checkpoint_ce_parameters.py OUT_JSON
"""
from __future__ import annotations

import collections
import hashlib
import io
import json
import pickle
import sys
import zipfile

import numpy as np

CKPTS = {
    "iceberg21_msg_simulation_gen": "/Users/aryav/muru-comparators/checkpoints/iceberg21_msg_simulation/gen/best.ckpt",
    "iceberg21_msg_simulation_inten_contr": "/Users/aryav/muru-comparators/checkpoints/iceberg21_msg_simulation/inten_contr/best.ckpt",
    "glacier_msg": "/Users/aryav/muru-comparators/checkpoints/glacier_msg/best.ckpt",
}

_DTYPES = {
    "FloatStorage": np.float32,
    "DoubleStorage": np.float64,
    "HalfStorage": np.float16,
    "LongStorage": np.int64,
    "IntStorage": np.int32,
    "ShortStorage": np.int16,
    "CharStorage": np.int8,
    "ByteStorage": np.uint8,
    "BoolStorage": np.bool_,
}


class _Stub:
    def __init__(self, *a, **k):
        self.args = a
        self.kwargs = k

    def __setstate__(self, state):
        self.state = state


class _StorageType:
    def __init__(self, name):
        self.name = name


def _rebuild_tensor_v2(storage, storage_offset, size, stride, requires_grad=False, backward_hooks=None, metadata=None):
    size = tuple(size)
    n = int(np.prod(size)) if len(size) else 1
    if n == 0:
        return np.zeros(size, dtype=storage.dtype)
    itemsize = storage.itemsize
    view = np.lib.stride_tricks.as_strided(
        storage[storage_offset:], shape=size, strides=tuple(s * itemsize for s in stride)
    )
    return np.array(view)


def _rebuild_parameter(data, requires_grad, backward_hooks, *rest):
    return data


class CkptUnpickler(pickle.Unpickler):
    def __init__(self, f, zf, prefix):
        super().__init__(f)
        self.zf = zf
        self.prefix = prefix
        self.cache = {}

    def find_class(self, module, name):
        if module == "torch._utils" and name == "_rebuild_tensor_v2":
            return _rebuild_tensor_v2
        if module == "torch._utils" and name in ("_rebuild_parameter", "_rebuild_parameter_with_state"):
            return _rebuild_parameter
        if module == "torch" and name.endswith("Storage"):
            return _StorageType(name)
        if module == "collections" and name == "OrderedDict":
            return collections.OrderedDict
        if module in ("builtins", "copyreg"):
            return super().find_class(module, name)
        return _Stub

    def persistent_load(self, pid):
        typename, storage_type, key, location, numel = pid
        assert typename == "storage"
        if key not in self.cache:
            raw = self.zf.read(f"{self.prefix}/data/{key}")
            self.cache[key] = np.frombuffer(raw, dtype=_DTYPES[storage_type.name])
        return self.cache[key]


def load_ckpt(path):
    zf = zipfile.ZipFile(path)
    pkl = [n for n in zf.namelist() if n.endswith("data.pkl")][0]
    prefix = pkl.rsplit("/", 1)[0]
    with zf.open(pkl) as f:
        return CkptUnpickler(io.BytesIO(f.read()), zf, prefix).load()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(out_path):
    out = {"note": "static tensor read only; no model construction, no inference", "checkpoints": {}}
    for tag, path in CKPTS.items():
        obj = load_ckpt(path)
        sd = obj["state_dict"]
        rec = {"path": path, "sha256": sha256(path), "n_state_dict_keys": len(sd)}
        ce_keys = [k for k in sd if "collision" in k or "instrument_embedder" in k or "adduct_embedder" in k]
        rec["ce_related_keys"] = {k: list(np.shape(sd[k])) for k in ce_keys}
        den = sd.get("collision_embedder_denominators")
        if den is not None:
            den = np.asarray(den, dtype=np.float64)
            rec["collision_embedder_denominators"] = den.tolist()
            p = 2 * np.arange(32) / 64.0
            rec["denominators_match_10000_pow_2i_over_64"] = bool(np.allclose(den, 10000.0 ** p, rtol=1e-5))
        merged = sd.get("collision_embed_merged")
        if merged is not None:
            rec["collision_embed_merged_all_zero"] = bool(np.all(np.asarray(merged) == 0))
        for k in ("adduct_embedder", "instrument_embedder"):
            if k in sd:
                rec[k] = np.asarray(sd[k]).astype(int).tolist()
        proj_keys = [k for k in sd if k.endswith("input_project.weight") or k.endswith("atom_encoder.weight")]
        rec["input_projection_keys"] = {k: list(np.shape(sd[k])) for k in proj_keys}
        n_add = np.shape(sd["adduct_embedder"])[1] if "adduct_embedder" in sd else 0
        n_ins = np.shape(sd["instrument_embedder"])[1] if "instrument_embedder" in sd else 0
        blocks = {}
        for k in proj_keys:
            W = np.asarray(sd[k], dtype=np.float64)
            ncol = W.shape[1]
            ce_start = ncol - n_ins - 64
            add_start = ce_start - n_add
            colnorm = np.linalg.norm(W, axis=0)
            blocks[k] = {
                "n_columns": int(ncol),
                "layout_assumed": f"[atom 0:{add_start}] [adduct {add_start}:{ce_start}] [CE sin {ce_start}:{ce_start + 32}] [CE cos {ce_start + 32}:{ce_start + 64}] [instrument {ce_start + 64}:{ncol}]",
                "atom_feat_colnorm_median": float(np.median(colnorm[:add_start])),
                "adduct_colnorm": colnorm[add_start:ce_start].round(4).tolist(),
                "ce_sin_colnorm_by_freq_index": colnorm[ce_start:ce_start + 32].round(4).tolist(),
                "ce_cos_colnorm_by_freq_index": colnorm[ce_start + 32:ce_start + 64].round(4).tolist(),
                "instrument_colnorm": colnorm[ce_start + 64:].round(4).tolist(),
            }
        rec["input_projection_column_norms"] = blocks
        hp = obj.get("hyper_parameters")
        if isinstance(hp, dict):
            rec["hyper_parameters_embed_flags"] = {
                k: hp.get(k) for k in ("embed_collision", "embed_instrument", "embed_adduct", "embed_elem_group", "encode_forms", "node_feats", "pe_embed_k")
            }
        out["checkpoints"][tag] = rec
    with open(out_path, "w") as f:
        f.write(json.dumps(out, indent=1) + "\n")
    brief = {t: {k: v for k, v in r.items() if k not in ("collision_embedder_denominators", "input_projection_column_norms", "adduct_embedder")} for t, r in out["checkpoints"].items()}
    print(json.dumps(brief, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
