---
license: mit
size_categories:
- 100K<n<1M
pretty_name: MassSpecGym
dataset_info:
  config_name: main
task_categories:
- other
tags:
- chemistry
- mass-spectrometry
- molecule-discovery
configs:
- config_name: main
  data_files:
  - split: val
    path: data/MassSpecGym1.5.tsv
---

<p align="center">
  <img src="assets/MassSpecGym_abstract.svg" width="80%"/>
</p>

MassSpecGym provides a dataset and benchmark for the discovery and identification of new molecules from tandem mass spectrometry (MS/MS) spectra. The provided challenges abstract the process of scientific discovery of new molecules from biological and environmental samples into well-defined machine learning problems.

## Papers

- **MassSpecGym in the Wild: Uncovering and Correcting Evaluation Pitfalls in AI-Driven Molecule Discovery** (2025): [Paper Link](https://huggingface.co/papers/2606.19624)
- **MassSpecGym: A benchmark for the discovery and identification of molecules** (NeurIPS 2024): [Paper Link](https://huggingface.co/papers/2410.23326)

## Links

- **GitHub:** [pluskal-lab/MassSpecGym](https://github.com/pluskal-lab/MassSpecGym)
- **Leaderboard:** [https://massspecgym.onrender.com/](https://massspecgym.onrender.com/)

## Sample Usage

You can load the MassSpecGym dataset directly into a pandas DataFrame using the `massspecgym` library:

```python
from massspecgym.utils import load_massspecgym
df = load_massspecgym()
```

Alternatively, you can use the provided PyTorch `Dataset` wrapper:

```python
from massspecgym.data import MassSpecDataset
from massspecgym.data.transforms import SpecTokenizer, MolFingerprinter

dataset = MassSpecDataset(
    spec_transform=SpecTokenizer(n_peaks=60),
    mol_transform=MolFingerprinter(),
)
```

## MassSpecGym v1.5 update

MassSpecGym v1.5 addresses several evaluation pitfalls identified in the "MassSpecGym in the Wild" audit. It adds six files to this data repository, and corrects the description of one existing file:

- `data/MassSpecGym1.5.tsv` — main dataset file. Schema is identical to v1 and content is nearly identical, except that the `smiles` column is re-standardized with `rdkit.Chem.MolToSmiles(canonical=True)` instead of the PubChem-standardized form used in v1.
- `data/auxiliary/MassSpecGym1.5.mgf` — MGF export of the above for tools that prefer MGF over TSV.
- `data/molecules/MassSpecGym1.5_retrieval_candidates_mass.json` — mass-filtered retrieval candidate pool. Same candidates as in v1 but with SMILES standardized using RDKit.
- `data/molecules/MassSpecGym1.5_retrieval_candidates_formula.json` — formula-filtered retrieval candidate pool. Same candidates as in v1 but with SMILES standardized using RDKit.
- `data/molecules/MassSpecGym1.5_pretraining_molecules_2.5M_tani070.txt` — approximately 2.5 million small-molecule SMILES intended as pretraining data, aggregated from DSSTox, HMDB, COCONUT, and MOSES. Every molecule has Tanimoto similarity < 0.7 to all MassSpecGym test molecules (4096-bit ECFP4).
- `data/molecules/MassSpecGym1.5_pretraining_molecules_50M_tani070.txt` — approximately 50 million small-molecule SMILES intended as pretraining data, sampled from ZINC and UniChem.
- `data/molecules/MassSpecGym_molecules_MCES2_disjoint_with_test_fold_4M.tsv` — unchanged file, corrected description. Despite its name and the original MassSpecGym paper wording (MCES distance < 2 from the test fold), exhaustive re-verification shows this set is disjoint more strictly at MCES ≤ 2 from both the val and test folds.

## Citation

If you use MassSpecGym in your work, please cite the original NeurIPS paper:

```bibtex
@inproceedings{bushuiev2024massspecgym,
 author = {Bushuiev, Roman and Bushuiev, Anton and de Jonge, Niek F. and Young, Adamo and Kretschmer, Fleming and Samusevich, Raman and Heirman, Janne and Wang, Fei and Zhang, Luke and D\"{u}hrkop, Kai and Ludwig, Marcus and Haupt, Nils A. and Kalia, Apurva and Brungs, Corinna and Schmid, Robin and Greiner, Russell and Wang, Bo and Wishart, David S. and Liu, Li-Ping and Rousu, Juho and Bittremieux, Wout and Rost, Hannes and Mak, Tytus D. and Hassoun, Soha and Huber, Florian and van der Hooft, Justin J.J. and Stravs, Michael A. and B\"{o}cker, Sebastian and Sivic, Josef and Pluskal, Tom\'{a}\v{s}},
 booktitle = {Advances in Neural Information Processing Systems},
 editor = {A. Globerson and L. Mackey and D. Belgrave and A. Fan and U. Paquet and J. Tomczak and C. Zhang},
 pages = {110010--110027},
 publisher = {Curran Associates, Inc.},
 title = {MassSpecGym: A benchmark for the discovery and identification of molecules},
 url = {https://proceedings.neurips.cc/paper_files/paper/2024/file/c6c31413d5c53b7d1c343c1498734b0f-Paper-Datasets_and_Benchmarks_Track.pdf},
 volume = {37},
 year = {2024}
}
```