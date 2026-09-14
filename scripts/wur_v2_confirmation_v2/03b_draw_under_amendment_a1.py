"""MSnLib confirmation study 2: the single draw under protocol V2 Amendment A-1.

Uses the saved response of the predeclared NIST pulse (2026-09-14T03:00:00.000Z) whose RSA signature could not be
verified against NIST's designated 2,048-bit certificate. Accepts it only under rule 3' of the amendment: exact
timestamp, valid outputValue, certificateId = SHA-512(DER), and an identical second retrieval of the same pulse via
its canonical URI. Then derives the seed by the unchanged rule and draws 2,000 scaffold groups once.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from cryptography import x509
from cryptography.hazmat.primitives.serialization import Encoding

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import decode_authority as DA     # noqa: E402

AMENDMENT = "MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2_AMENDMENT_A1.md"
RAND = ROOT / "artifacts/wur_v2_confirmation_v2/randomness"
POP = ROOT / "artifacts/wur_v2_confirmation_v2/population"
RAW_SHA = "6a4eed54b9000c9f6aaa788205788418c83aa4d17dc1dc001f125d4d7d48aa5a"
CERT_SHA = "c342339ca0fe5f1c522e03471b32811310371c3adbb8f107c8d77b5f336bfce9"
CANONICAL_URI = "https://beacon.nist.gov/beacon/2.0/chain/2/pulse/1940454"

_spec = importlib.util.spec_from_file_location("draw03", ROOT / "scripts/wur_v2_confirmation_v2/03_randomness_and_draw.py")
D3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D3)


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def main() -> int:
    if git("status", "--porcelain", "--untracked-files=all"):
        raise SystemExit("STOP: working tree is not clean")
    D3.committed_identical(AMENDMENT)
    head = git("rev-parse", "HEAD")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    remote_head = git("ls-remote", "origin", f"refs/heads/{branch}").split()
    if not remote_head or subprocess.run(["git", "merge-base", "--is-ancestor", git("log", "-1", "--format=%H", "--", AMENDMENT),
                                          remote_head[0]], cwd=ROOT).returncode != 0:
        raise SystemExit("STOP: the amendment commit is not on origin")
    if (POP / "sampled_scaffold_groups.txt").exists() or (RAND / "randomness_and_draw_record.json").exists():
        raise SystemExit("STOP: a draw already exists; one draw")
    raw = D3.committed_identical("artifacts/wur_v2_confirmation_v2/randomness/nist_beacon_pulse_raw.json")
    cert_pem = D3.committed_identical("artifacts/wur_v2_confirmation_v2/randomness/nist_beacon_certificate.pem")
    if hashlib.sha256(raw).hexdigest() != RAW_SHA or hashlib.sha256(cert_pem).hexdigest() != CERT_SHA:
        raise SystemExit("STOP: saved pulse or certificate differ from the amendment's recorded hashes")
    protocol = D3.committed_identical(DA.PROTOCOL_V2).decode()
    pulse = json.loads(raw)["pulse"]
    ts = datetime.strptime(D3.PULSE_TIMESTAMP, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    got = datetime.strptime(pulse["timeStamp"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    cert = x509.load_pem_x509_certificate(cert_pem)
    checks = {
        "a_timestamp_exact": got == ts and D3.PULSE_TIMESTAMP in protocol,
        "b_output_value_valid": hashlib.sha512(D3.signature_input(pulse) + bytes.fromhex(pulse["signatureValue"])).hexdigest()
                                == pulse["outputValue"].lower(),
        "c_certificate_id_is_sha512_of_der": hashlib.sha512(cert.public_bytes(Encoding.DER)).hexdigest() == pulse["certificateId"].lower(),
    }
    second = D3.fetch(CANONICAL_URI)
    checks["d_canonical_uri_returns_identical_pulse"] = json.loads(second)["pulse"] == pulse and pulse["uri"] == CANONICAL_URI
    rsa = D3.verify_pulse(pulse, cert_pem)
    if not all(checks.values()):
        raise SystemExit(f"STOP: amendment A-1 rule 3' not satisfied {checks}; no draw")
    (RAND / "nist_beacon_pulse_canonical_uri_raw.json").write_bytes(second)

    elig_txt = D3.committed_identical("artifacts/wur_v2_confirmation_v2/population/eligible_scaffold_groups.txt").decode()
    manifest = json.loads(D3.committed_identical("artifacts/wur_v2_confirmation_v2/population/eligible_universe_manifest.json"))
    eligible = [g for g in elig_txt.split("\n") if g]
    if eligible != sorted(set(eligible)) or DA.sha256_lines(eligible) != manifest["eligible_groups_sha256_sorted_newline_joined"] \
            or manifest["eligible_groups_sha256_sorted_newline_joined"] not in protocol:
        raise SystemExit("STOP: eligible group list does not match its committed hash")

    output_bytes = bytes.fromhex(pulse["outputValue"])
    seed = int(hashlib.sha256(output_bytes).hexdigest()[:16], 16)
    sampled = np.random.default_rng(seed).choice(np.array(eligible, dtype=object), size=D3.N_GROUPS, replace=False)
    sampled_sorted = sorted(set(sampled.tolist()))
    if len(sampled_sorted) != D3.N_GROUPS:
        raise SystemExit("draw returned duplicates")
    (POP / "sampled_scaffold_groups.txt").write_text("\n".join(sampled_sorted) + "\n")
    record = {
        "study_id": DA.STUDY_ID_V2,
        "protocol_commit": git("log", "-1", "--format=%H", "--", DA.PROTOCOL_V2),
        "amendment": AMENDMENT, "amendment_commit": git("log", "-1", "--format=%H", "--", AMENDMENT),
        "draw_head": head,
        "predeclared_pulse_timestamp": D3.PULSE_TIMESTAMP,
        "pulse": {k: pulse[k] for k in ("uri", "version", "cipherSuite", "chainIndex", "pulseIndex", "timeStamp", "statusCode",
                                         "certificateId", "outputValue")},
        "raw_response_sha256": RAW_SHA, "certificate_sha256": CERT_SHA,
        "canonical_uri_response_sha256": hashlib.sha256(second).hexdigest(),
        "amendment_a1_checks": checks,
        "rsa_signature_check": {**rsa, "certificate_key_bits": cert.public_key().key_size,
                                "signature_bits": len(pulse["signatureValue"]) * 4,
                                "disclosure": "designated certificate key (2,048-bit) cannot have produced the 4,096-bit signature"},
        "beacon_output_sha256": hashlib.sha256(output_bytes).hexdigest(),
        "seed_rule": "seed = int(SHA256(bytes.fromhex(pulse.outputValue)).hexdigest()[:16], 16)",
        "seed": seed,
        "draw_call": "numpy.random.default_rng(seed).choice(np.array(sorted_eligible_groups, dtype=object), size=2000, replace=False)",
        "numpy_version": np.__version__, "drawn_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "eligible_groups_sha256": manifest["eligible_groups_sha256_sorted_newline_joined"], "n_eligible_groups": len(eligible),
        "draw_order": sampled.tolist(),
        "sampled_groups_sha256_sorted_newline_joined": DA.sha256_lines(sampled_sorted),
    }
    (RAND / "randomness_and_draw_record.json").write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k not in ("draw_order",)}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
