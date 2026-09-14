"""Print the hyper_parameters stored in Lightning checkpoints (no model instantiation, no inference)."""
import json, sys, torch
for p in sys.argv[1:]:
    ck = torch.load(p, map_location="cpu", weights_only=False)
    hp = ck.get("hyper_parameters", {})
    print(json.dumps({"path": p, "epoch": ck.get("epoch"), "global_step": ck.get("global_step"),
                      "pytorch_lightning_version": ck.get("pytorch-lightning_version"),
                      "hyper_parameters": {k: (v if isinstance(v, (int, float, str, bool, type(None), list)) else str(v)) for k, v in hp.items()}}, default=str))
