"""Master script to generate all MURU Pre-Results figures.

Produces publication-quality figures:
- Figure 1: MURU computational architecture (SVG, PDF, PNG)
- Figure 2: Prospective-governance timeline & partition seals (SVG, PDF, PNG)
- Figure 3: Synthetic benchmark architecture & truth taxonomy (SVG, PDF, PNG)
- Figure 4: Null-calibration architecture & monotonic threshold protocol (SVG, PDF, PNG)
- Figure 5: Secondary endpoint design (Parameter Recovery & Predictive Equivalence) (SVG, PDF, PNG)
- Figure 6: Evidence hierarchy & scientific claim boundaries (SVG, PDF, PNG)

No result numbers. Strictly reproducible.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add script directory to sys.path
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import fig01_computational_architecture
import fig02_governance_timeline
import fig03_benchmark_architecture
import fig04_null_calibration_architecture
import fig05_secondary_endpoints_design
import fig06_evidence_hierarchy

def main() -> None:
    out_dir = SCRIPTS_DIR.parent / "pre_results"
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("MURU CONJECTURELAB v1: PRE-RESULTS FIGURE PRODUCTION")
    print("=" * 70)
    print(f"Output directory: {out_dir}")
    print("Binding rule: No prospective result numbers or fake curves rendered.")
    print("-" * 70)
    
    generators = [
        ("Figure 1", fig01_computational_architecture.generate_figure),
        ("Figure 2", fig02_governance_timeline.generate_figure),
        ("Figure 3", fig03_benchmark_architecture.generate_figure),
        ("Figure 4", fig04_null_calibration_architecture.generate_figure),
        ("Figure 5", fig05_secondary_endpoints_design.generate_figure),
        ("Figure 6", fig06_evidence_hierarchy.generate_figure),
    ]
    
    results = {}
    for name, gen_fn in generators:
        print(f"Generating {name}...")
        paths = gen_fn(out_dir)
        results[name] = paths
        for ext, path in paths.items():
            assert path.exists() and path.stat().st_size > 0, f"Failed for {path}"
            print(f"  [{ext.upper()}] {path.name} ({path.stat().st_size:,} bytes)")
            
    print("=" * 70)
    print("ALL 6 FIGURES SUCCESSFULLY GENERATED IN SVG, PDF, AND PNG (300 DPI)")
    print("=" * 70)

if __name__ == "__main__":
    main()
