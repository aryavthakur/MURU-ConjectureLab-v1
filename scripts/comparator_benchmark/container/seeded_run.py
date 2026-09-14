"""Run an unmodified ms-pred prediction script after applying the seeding its own CLI declares.

predict_smis.py and predict_smis_joint.py expose --seed (default 42), but predict_smis.py leaves the call
`pl.utilities.seed.seed_everything(kwargs.get("seed"))` commented out while shuffling its entries with Python's
`random`. This wrapper applies pytorch_lightning.seed_everything(<seed>) and then executes the script unchanged.
Usage: python seeded_run.py <seed> <script.py> [script args...]
"""
import runpy
import sys

import pytorch_lightning as pl

seed = int(sys.argv[1])
script = sys.argv[2]
pl.seed_everything(seed, workers=True)
sys.argv = [script] + sys.argv[3:]
runpy.run_path(script, run_name="__main__")
