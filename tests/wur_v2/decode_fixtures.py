"""Synthetic fixtures for the study-2 decode-boundary tests: tiny mzML bytes, throwaway git repositories with a
bare `origin`, a minimal exposure registry, anchor and validation environments. No real MSnLib file is used."""
from __future__ import annotations

import base64
import csv
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import numpy as np

from muru.wur_v2 import decode_authority as DA


def _bda(values, kind_acc, bits64):
    raw = np.asarray(values, "<f8" if bits64 else "<f4").tobytes()
    return (f'<binaryDataArray encodedLength="0"><cvParam accession="{"MS:1000523" if bits64 else "MS:1000521"}" name="f"/>'
            f'<cvParam accession="{kind_acc}" name="a"/><binary>{base64.b64encode(raw).decode()}</binary></binaryDataArray>')


def mzml_bytes(scans, marker=0.0) -> bytes:
    """scans: (spectrum_id, ms_level, selected_ion_mz or None or list of m/z, collision_energy). `marker` shifts
    the m/z array so two files with identical headers still have different arrays and bytes."""
    specs = []
    for i, (sid, level, mz, ce) in enumerate(scans):
        prec = ""
        if mz is not None:
            ions = mz if isinstance(mz, list) else [mz]
            sel = "".join(f'<selectedIon><cvParam accession="MS:1000744" name="sel" value="{v}"/></selectedIon>' for v in ions)
            prec = (f'<precursorList count="1"><precursor><selectedIonList count="{len(ions)}">{sel}</selectedIonList>'
                    f'<activation><cvParam accession="MS:1000045" name="ce" value="{ce}"/></activation></precursor></precursorList>')
        specs.append(
            f'<spectrum index="{i}" id="{sid}" defaultArrayLength="2"><cvParam accession="MS:1000511" name="ms level" value="{level}"/>'
            f'<scanList count="1"><scan><scanWindowList count="1"><scanWindow><cvParam accession="MS:1000501" name="lo" value="40"/>'
            f'<cvParam accession="MS:1000500" name="hi" value="1000"/></scanWindow></scanWindowList></scan></scanList>{prec}'
            f'<binaryDataArrayList count="2">{_bda([50.0 + i + marker, 99.0 + i], "MS:1000514", True)}'
            f'{_bda([10.0, 20.0], "MS:1000515", False)}</binaryDataArrayList></spectrum>')
    return ('<?xml version="1.0" encoding="utf-8"?><mzML xmlns="http://psi.hupo.org/ms/mzml"><run>'
            f'<spectrumList count="{len(scans)}">' + "".join(specs) + "</spectrumList></run></mzML>").encode()


def write_mzml(path: Path, scans, marker=0.0) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(mzml_bytes(scans, marker))
    return path


def sha(b) -> str:
    return hashlib.sha256(b if isinstance(b, (bytes, bytearray)) else Path(b).read_bytes()).hexdigest()


def git(root, *args, check=True):
    r = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {args}: {r.stderr}")
    return r.stdout.strip()


def init_repo(root: Path, with_origin=True) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@t")
    git(root, "config", "user.name", "t")
    if with_origin:
        origin = root.parent / f"{root.name}_origin.git"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, capture_output=True)
        git(root, "remote", "add", "origin", str(origin))
    return root


def write_csv(path: Path, rows, cols):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def write_registry(repo: Path, exposed_rows, decoded_rows, excluded_keys=(), excluded_groups=()) -> str:
    d = repo / DA.REGISTRY_DIR
    write_csv(repo / DA.EXPOSED_FILES, exposed_rows, ["file", "file_sha256", "unique_sample_id", "events"])
    write_csv(repo / DA.DECODED_SPECTRA, decoded_rows, ["event", "file", "unique_sample_id", "spectrum_id",
                                                        "selected_ion_mz", "rung", "surfaced_to_operator"])
    (repo / DA.EXCLUDED_KEYS).write_text("".join(f"{k}\n" for k in sorted(excluded_keys)))
    (repo / DA.EXCLUDED_GROUPS).write_text("".join(f"{g}\n" for g in sorted(excluded_groups)))
    names = ["exposed_files.csv", "decoded_spectra.csv", "excluded_compound_keys.txt", "excluded_scaffold_groups.txt"]
    (repo / DA.REGISTRY_MANIFEST).write_text(json.dumps({"output_file_sha256": {n: sha(d / n) for n in names}}))
    return sha(repo / DA.REGISTRY_MANIFEST)


# pooled anchor well: a NON-anchor compound (m/z 500.0) acquired FIRST, the anchor (m/z 300.0) later
POOLED = [("s0", 1, None, None), ("s1", 2, 500.0, 20.0), ("s2", 2, 500.0, 60.0), ("s3", 2, 300.0, 20.0), ("s4", 2, 300.0, 60.0)]


def anchor_env(tmp_path: Path, extra_allow=(), extra_decoded=(), pooled_scans=POOLED, anchor_mh="300.0",
               anchor_key="ANCHORKEY", commit=True) -> dict:
    data = tmp_path / "data"
    pooled = write_mzml(data / "pluskal_A1_id.mzML", pooled_scans)
    other = write_mzml(data / "pluskal_B7_id.mzML", [("t1", 2, 300.0, 20.0), ("t2", 2, 300.0, 60.0)], marker=7.0)
    repo = init_repo(tmp_path / "repo", with_origin=False)
    (repo / DA.CENSUS).parent.mkdir(parents=True, exist_ok=True)
    (repo / DA.CENSUS).write_text(json.dumps({"anchors": {"design": {"v2_dev_five_rung": {"keys": ["ANCHORKEY"]}}}}))
    decoded = [{"event": "E", "file": pooled.name, "unique_sample_id": "pluskal_A1_id", "spectrum_id": s,
                "selected_ion_mz": str(mz), "rung": "", "surfaced_to_operator": "False"}
               for s, lvl, mz, ce in pooled_scans if mz is not None] + list(extra_decoded)
    reg_sha = write_registry(repo, [{"file": pooled.name, "file_sha256": sha(pooled), "unique_sample_id": "pluskal_A1_id",
                                     "events": "E"}], decoded)
    allow = [{"file": pooled.name, "file_sha256": sha(pooled), "spectrum_id": s, "selected_ion_mz": "300.0",
              "anchor_key": anchor_key, "anchor_mh": anchor_mh} for s in ("s3", "s4")] + list(extra_allow)
    write_csv(repo / DA.ANCHOR_ALLOWLIST, allow, ["file", "file_sha256", "spectrum_id", "selected_ion_mz", "anchor_key", "anchor_mh"])
    if commit:
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "registry + allowlist")
    return {"repo": repo, "pooled": pooled, "other": other, "log": tmp_path / "preflight_log.jsonl", "registry_sha": reg_sha}


def anchor_authority(env, **ov):
    kw = dict(log_path=env["log"], root=env["repo"], code_root=None, registry_manifest_sha256=env["registry_sha"])
    kw.update(ov)
    return DA._for_tests(DA.AnchorPreflightAuthority, **kw)


VAL = [("v1", 2, 412.2, 20.0), ("v2", 2, 412.2, 60.0), ("v3", 2, 612.3, 20.0)]
MEMBER = "mzml/pluskal_C3_id.mzML"


def validation_env(tmp_path: Path, *, commit_freeze=True, publish=True, scans=VAL, pop_key="KEYA", group="GA",
                   excluded_keys=(), excluded_groups=(), exposed_extra=(), allow_mz="412.2",
                   manifest_tweak=None, frozen_tweak=None, scan_key=None, pop_mh="412.2", pop_wells="pluskal_C3_id",
                   rungs=("20", "60"), row_well="pluskal_C3_id") -> dict:
    zips = tmp_path / "zips"
    zips.mkdir(parents=True, exist_ok=True)
    member_bytes = mzml_bytes(scans)
    with zipfile.ZipFile(zips / "lib.zip", "w") as zf:
        zf.writestr(MEMBER, member_bytes)
    fname = MEMBER.rsplit("/", 1)[-1]
    repo = init_repo(tmp_path / "repo")
    (repo / "README").write_text("r\n")
    git(repo, "add", "README")
    git(repo, "commit", "-q", "-m", "protocol")
    (repo / DA.PROTOCOL_V2).write_text("protocol v2\n")
    cand, comp = {"name": "CAND", "coef": [1, 2]}, {"name": "COMP", "coef": [3]}
    for rel, obj in ((DA.CANDIDATE_JSON, cand), (DA.COMPARATOR_JSON, comp)):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(json.dumps(obj))
    reg_sha = write_registry(repo, [{"file": "pluskal_A1_id.mzML", "file_sha256": "0" * 64, "unique_sample_id": "pluskal_A1_id",
                                     "events": "E"}, *exposed_extra], [], excluded_keys, excluded_groups)
    write_csv(repo / DA.POPULATION_CSV, [{"key": pop_key, "scaffold_group": group, "mh": pop_mh, "wells": pop_wells}],
              ["key", "scaffold_group", "mh", "wells"])
    scan_rows = [{"source_zip": "lib.zip", "member": MEMBER, "file": fname, "file_sha256": sha(member_bytes),
                  "unique_sample_id": row_well, "spectrum_id": s, "selected_ion_mz": allow_mz, "key": scan_key or pop_key,
                  "rung": r} for s, r in zip(("v1", "v2"), rungs)]
    write_csv(repo / DA.SCAN_ALLOWLIST, scan_rows,
              ["source_zip", "member", "file", "file_sha256", "unique_sample_id", "spectrum_id", "selected_ion_mz", "key", "rung"])
    (repo / DA.FREEZE_DOC).write_text("FINAL FREEZE study 2\n")
    hashes = {"candidate_hash": DA.canonical_json_sha256(cand), "comparator_hash": DA.canonical_json_sha256(comp),
              "population_key_hash": DA.sha256_lines([pop_key]), "scaffold_group_hash": DA.sha256_lines([group]),
              "spectrum_manifest_hash": DA.sha256_lines([f"{fname}:v1", f"{fname}:v2"]), "registry_manifest_sha256": reg_sha}
    frozen = {rel: sha(repo / rel) for rel in DA.REQUIRED_FROZEN}
    if frozen_tweak:
        frozen_tweak(frozen)
    manifest = {"study_id": DA.STUDY_ID_V2, **hashes, "frozen_files": frozen}
    if manifest_tweak:
        manifest_tweak(manifest)
    (repo / DA.FREEZE_MANIFEST).parent.mkdir(parents=True, exist_ok=True)
    (repo / DA.FREEZE_MANIFEST).write_text(json.dumps(manifest, indent=1))
    env = {"repo": repo, "zips": zips, "member_bytes": member_bytes, "fname": fname, "ledger": tmp_path / "ledger",
           "registry_sha": reg_sha}
    if commit_freeze:
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "FINAL FREEZE")
        git(repo, "push", "-q", "origin", "main")
        if publish:
            publish_freeze(env)
    return env


def publish_freeze(env, register=True):
    """Raw publication for negative tests (bypasses verify_freeze_candidate on purpose)."""
    head = git(env["repo"], "rev-parse", "HEAD")
    git(env["repo"], "push", "-q", "-f", "origin", f"{head}:{DA.FREEZE_REF}")
    if register:
        reg = env["repo"] / ".git" / "muru-access-ledger" / f"{DA.STUDY_ID_V2}.freeze.json"
        reg.parent.mkdir(parents=True, exist_ok=True)
        reg.write_text(json.dumps({"freeze_commit": head}))


def v2_overrides(env, **ov):
    kw = dict(root=env["repo"], code_root=None, ledger_dirs=(env["ledger"],), zip_dir=env["zips"],
              registry_manifest_sha256=env["registry_sha"],
              canonical_remote=git(env["repo"], "remote", "get-url", "origin"))
    kw.update(ov)
    return kw


def v2_authority(env, **ov):
    kw = v2_overrides(env)
    kw.update(ov)
    return DA._for_tests(DA.ConfirmationV2Authority, **kw)


def member(env):
    from muru.wur_v2 import external_mzml as X
    return X.ZipMember(env["zips"] / "lib.zip", MEMBER)
