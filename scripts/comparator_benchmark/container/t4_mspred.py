"""T4 inside the ms-pred image: structure / parser / featurization acceptance only. No model forward pass.

ICEBERG 2.1: replays predict_smis.prepare_entry (canonicalisation, InChIKey, CE parse, instrument normalisation) and
the featurisation steps of gen_model.predict_mol / joint_model (FragmentEngine root, formula vectors, both
TreeProcessors' featurize_frag with positional embedding, adduct and instrument one-hots, adduct mass offsets).
GLACIER: calls predict_smis_joint.prepare_entry itself, then GraphormerFeatDataset.__getitem__ and collate_predict.
Checkpoints are loaded only to read the featuriser hyperparameters.
"""
import json
import math
import sys
import traceback

import pandas as pd
import torch
from rdkit import Chem

from ms_pred import common

model, tsv, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
df = pd.read_csv(tsv, sep="\t")
results = []

if model == "iceberg":
    import ast
    from ms_pred.iceberg import gen_model, inten_model, dag_data
    from ms_pred.iceberg.predict_smis import normalize_instrument
    from ms_pred.magma import fragmentation

    gen = gen_model.FragGNN.load_from_checkpoint("/ckpt/iceberg21_msg_simulation/gen/best.ckpt", map_location="cpu")
    inten = inten_model.IntenGNN.load_from_checkpoint("/ckpt/iceberg21_msg_simulation/inten_contr/best.ckpt", map_location="cpu")
    inten_tp = dag_data.TreeProcessor(root_encode=inten.root_encode, pe_embed_k=inten.pe_embed_k, add_hs=inten.add_hs,
                                      embed_elem_group=inten.embed_elem_group)
    for _, entry in df.iterrows():
        rec = {"spec": entry["spec"], "ok": False}
        try:
            smi = Chem.MolToSmiles(Chem.MolFromSmiles(entry["smiles"]))          # predict_smis, strict_sanitize=False
            rec["canonical_smiles"] = smi
            rec["inchikey"] = common.inchikey_from_smiles(smi)
            ces = [common.collision_energy_to_float(c) for c in ast.literal_eval(entry["collision_energies"])]
            assert ces and not any(math.isnan(c) for c in ces), "collision energy not parsed"
            instrument = normalize_instrument(entry["instrument"])
            _ = common.ion2onehot_pos[entry["ionization"]], common.instrument2onehot_pos[instrument]
            _ = common.ion2mass[entry["ionization"]], float(entry["precursor"])
            engine = fragmentation.FragmentEngine(smi, mol_str_canonicalized=True)
            root_frag = engine.get_root_frag()
            root_form = common.form_from_smi(smi)
            vec = common.formula_to_dense(root_form)
            g = gen.tree_processor.featurize_frag(frag=root_frag, engine=engine, add_random_walk=False)
            gen.tree_processor.add_pe_embed(g["graph"])
            g2 = inten_tp.featurize_frag(frag=root_frag, engine=engine, add_random_walk=False)
            rec.update(ok=True, natoms=int(engine.natoms), instrument=instrument, ce=ces,
                       root_formula=root_form, node_feat_dim=int(g["graph"].ndata["h"].shape[1]))
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"
            rec["trace"] = traceback.format_exc()[-1500:]
        results.append(rec)

elif model == "glacier":
    from ms_pred.glacier import predict_smis_joint as PJ
    PJ._lazy_imports()
    jm = PJ.joint_model.JointModel.load_from_checkpoint("/ckpt/glacier_msg/best.ckpt", map_location="cpu")
    tp = PJ.glacier_dataset.TreeProcessor(pe_embed_k=jm.pe_embed_k, root_encode="graphormer",
                                          embed_elem_group=jm.embed_elem_group, multi_hop_max_dist=jm.multi_hop_max_dist)
    for _, entry in df.iterrows():
        rec = {"spec": entry["spec"], "ok": False}
        try:
            entries = PJ.prepare_entry(entry)
            if not entries:
                raise ValueError("prepare_entry returned no entries (unparseable, invalid atom, >100 heavy atoms or no CE)")
            ds = PJ.GraphormerFeatDataset(entries, tree_processor=tp, sort_for_batching=True, feat_cache_size=0)
            items = [ds[i] for i in range(len(ds))]
            batch = PJ.collate_predict(items)
            rec.update(ok=True, canonical_smiles=entries[0][0], n_entries=len(entries), ce=[e[2] for e in entries],
                       num_atoms=[int(x) for x in torch.as_tensor(batch["num_atoms"]).flatten().tolist()])
        except Exception as e:
            rec["error"] = f"{type(e).__name__}: {e}"
            rec["trace"] = traceback.format_exc()[-1500:]
        results.append(rec)

json.dump(results, open(out_path, "w"))
print(model, "accepted", sum(r["ok"] for r in results), "of", len(results))
