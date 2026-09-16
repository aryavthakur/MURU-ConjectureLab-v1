"""P3 helper: print a Jupyter notebook's code/markdown cells with cell index and
per-cell line numbers, plus text outputs (truncated). Used to cite notebook
cell:line evidence for MassSpecGym curation provenance. Reads a local .ipynb
fetched from GitHub via gh api; performs no network access itself."""
import json, sys

path = sys.argv[1]
maxout = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
nb = json.load(open(path))
for i, c in enumerate(nb["cells"]):
    src = "".join(c["source"]) if isinstance(c["source"], list) else c["source"]
    print(f"##### cell {i} [{c['cell_type']}]")
    for j, line in enumerate(src.split("\n"), 1):
        print(f"{j:4d}| {line}")
    if c["cell_type"] == "code" and maxout > 0:
        buf = []
        for o in c.get("outputs", []):
            if "text" in o:
                buf.append("".join(o["text"]))
            elif "data" in o and "text/plain" in o["data"]:
                buf.append("".join(o["data"]["text/plain"]))
        out = "\n".join(buf)
        if out:
            if len(out) > maxout:
                out = out[:maxout] + f"\n... [truncated {len(out)-maxout} chars]"
            print("----- output")
            print(out)
