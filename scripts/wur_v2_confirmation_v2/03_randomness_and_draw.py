"""MSnLib confirmation study 2, protocol V2 sections 6-7: the one external randomness pulse and the one draw.

Retrieves exactly the NIST Randomness Beacon 2.0 pulse predeclared in MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md,
saves the raw response and certificate, verifies the RSA-SHA512 signature and outputValue by the NIST 2.0
serialization, derives the NumPy seed by the predeclared rule, and draws 2,000 scaffold groups once.

It refuses to run before the pulse time, if the protocol or eligible list is not committed at HEAD with the
recorded hashes, if any randomness record or draw already exists (on disk or in git history), or if the returned
pulse does not carry exactly the predeclared timestamp. On any failure it STOPS without drawing; a different
pulse may only be used after a separately committed protocol amendment.
"""
from __future__ import annotations

import hashlib
import json
import struct
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from muru.wur_v2 import decode_authority as DA     # noqa: E402

PULSE_TIMESTAMP = "2026-09-14T03:00:00.000Z"                    # predeclared in protocol V2 section 6
PULSE_URL = "https://beacon.nist.gov/beacon/2.0/pulse/time/{ms}"
CERT_URL = "https://beacon.nist.gov/beacon/2.0/certificate/{cid}"
N_GROUPS = 2000
PROTOCOL = ROOT / DA.PROTOCOL_V2
POP = ROOT / "artifacts/wur_v2_confirmation_v2/population"
RAND = ROOT / "artifacts/wur_v2_confirmation_v2/randomness"


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def committed_identical(rel: str) -> bytes:
    b = (ROOT / rel).read_bytes()
    blob = subprocess.run(["git", "cat-file", "blob", f"HEAD:{rel}"], cwd=ROOT, capture_output=True).stdout
    if b != blob:
        raise SystemExit(f"{rel} is not committed at HEAD byte-for-byte")
    return b


def fetch(url: str, attempts: int = 5) -> bytes:
    last = None
    for i in range(attempts):                      # retries of the SAME url only; a pulse's content is fixed
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=60) as r:
                return r.read()
        except Exception as e:                     # noqa: BLE001
            last = e
            time.sleep(10 * (i + 1))
    raise SystemExit(f"STOP: {url} unavailable after {attempts} attempts ({last}); no draw")


def _u32(n: int) -> bytes:
    return struct.pack(">i", int(n))


def _hexb(h: str) -> bytes:
    b = bytes.fromhex(h)
    return _u32(len(b)) + b


def _str(s: str) -> bytes:
    return _u32(len(s)) + s.encode("utf-8")


def signature_input(p: dict) -> bytes:
    """NIST Randomness Beacon 2.0 pulse serialization (the bytes that are signed)."""
    out = _str(p["uri"]) + _str(p["version"]) + _u32(p["cipherSuite"]) + _u32(p["period"]) + _hexb(p["certificateId"])
    out += struct.pack(">q", int(p["chainIndex"])) + struct.pack(">q", int(p["pulseIndex"])) + _str(p["timeStamp"])
    out += _hexb(p["localRandomValue"]) + _hexb(p["external"]["sourceId"]) + _u32(p["external"]["statusCode"])
    out += _hexb(p["external"]["value"])
    for item in p["listValues"]:
        out += _hexb(item["value"])
    out += _hexb(p["precommitmentValue"]) + _u32(p["statusCode"])
    return out


def verify_pulse(p: dict, cert_pem: bytes) -> dict:
    from cryptography import x509
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    msg = signature_input(p)
    sig = bytes.fromhex(p["signatureValue"])
    cert = x509.load_pem_x509_certificate(cert_pem)
    try:
        cert.public_key().verify(sig, msg, padding.PKCS1v15(), hashes.SHA512())
        sig_ok = True
    except InvalidSignature:
        sig_ok = False
    output_ok = hashlib.sha512(msg + sig).hexdigest() == p["outputValue"].lower()
    cert_id_ok = hashlib.sha512(cert_pem).hexdigest() == p["certificateId"].lower()   # informational only
    return {"signature_valid": sig_ok, "output_value_valid": output_ok, "certificate_id_is_sha512_of_pem": cert_id_ok,
            "certificate_subject": cert.subject.rfc4514_string(), "certificate_issuer": cert.issuer.rfc4514_string()}


def main() -> int:
    ts = datetime.strptime(PULSE_TIMESTAMP, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    ms = int(ts.timestamp() * 1000)
    if datetime.now(timezone.utc) < ts:
        raise SystemExit(f"STOP: the predeclared pulse {PULSE_TIMESTAMP} is in the future")
    if git("status", "--porcelain", "--untracked-files=all"):
        raise SystemExit("STOP: working tree is not clean")
    protocol = committed_identical(DA.PROTOCOL_V2).decode()
    if PULSE_TIMESTAMP not in protocol:
        raise SystemExit("STOP: the committed protocol does not predeclare this pulse timestamp")
    if git("log", "--all", "--reflog", "--format=%H", "--", str(RAND.relative_to(ROOT))) or RAND.exists() \
            or (POP / "sampled_scaffold_groups.txt").exists():
        raise SystemExit("STOP: a randomness record or draw already exists; one pulse, one draw")
    elig_txt = committed_identical("artifacts/wur_v2_confirmation_v2/population/eligible_scaffold_groups.txt").decode()
    manifest = json.loads(committed_identical("artifacts/wur_v2_confirmation_v2/population/eligible_universe_manifest.json"))
    eligible = [g for g in elig_txt.split("\n") if g]
    if eligible != sorted(set(eligible)) or DA.sha256_lines(eligible) != manifest["eligible_groups_sha256_sorted_newline_joined"]:
        raise SystemExit("STOP: eligible group list does not match its manifest")
    if manifest["eligible_groups_sha256_sorted_newline_joined"] not in protocol:
        raise SystemExit("STOP: the committed protocol does not record the eligible group list hash")
    protocol_commit = git("log", "-1", "--format=%H", "--", DA.PROTOCOL_V2)

    raw = fetch(PULSE_URL.format(ms=ms))
    body = json.loads(raw)
    pulse = body["pulse"]
    returned = datetime.strptime(pulse["timeStamp"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    RAND.mkdir(parents=True, exist_ok=False)
    (RAND / "nist_beacon_pulse_raw.json").write_bytes(raw)
    if returned != ts:
        (RAND / "STOPPED.json").write_text(json.dumps({"reason": "returned pulse timestamp differs", "returned": pulse["timeStamp"]}))
        raise SystemExit(f"STOP: returned pulse {pulse['timeStamp']} is not the predeclared {PULSE_TIMESTAMP}; no draw")
    cert = fetch(CERT_URL.format(cid=pulse["certificateId"]))
    (RAND / "nist_beacon_certificate.pem").write_bytes(cert)
    verification = verify_pulse(pulse, cert)
    if not (verification["signature_valid"] and verification["output_value_valid"]):
        (RAND / "STOPPED.json").write_text(json.dumps({"reason": "pulse verification failed", **verification}))
        raise SystemExit(f"STOP: pulse verification failed {verification}; no draw")

    output_bytes = bytes.fromhex(pulse["outputValue"])
    seed = int(hashlib.sha256(output_bytes).hexdigest()[:16], 16)
    rng = np.random.default_rng(seed)
    sampled = rng.choice(np.array(eligible, dtype=object), size=N_GROUPS, replace=False)
    sampled_sorted = sorted(set(sampled.tolist()))
    if len(sampled_sorted) != N_GROUPS:
        raise SystemExit("draw returned duplicates")
    (POP / "sampled_scaffold_groups.txt").write_text("\n".join(sampled_sorted) + "\n")
    record = {
        "study_id": DA.STUDY_ID_V2,
        "protocol_commit": protocol_commit,
        "protocol_sha256": hashlib.sha256(protocol.encode()).hexdigest(),
        "predeclared_pulse_timestamp": PULSE_TIMESTAMP, "request_url": PULSE_URL.format(ms=ms),
        "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pulse": {k: pulse[k] for k in ("uri", "version", "chainIndex", "pulseIndex", "timeStamp", "statusCode",
                                         "certificateId", "outputValue")},
        "raw_response_sha256": hashlib.sha256(raw).hexdigest(),
        "certificate_sha256": hashlib.sha256(cert).hexdigest(),
        "verification": verification,
        "beacon_output_sha256": hashlib.sha256(output_bytes).hexdigest(),
        "seed_rule": "seed = int(SHA256(bytes.fromhex(pulse.outputValue)).hexdigest()[:16], 16)",
        "seed": seed,
        "draw_call": "numpy.random.default_rng(seed).choice(np.array(sorted_eligible_groups, dtype=object), size=2000, replace=False)",
        "numpy_version": np.__version__,
        "eligible_groups_sha256": manifest["eligible_groups_sha256_sorted_newline_joined"],
        "n_eligible_groups": len(eligible),
        "draw_order": sampled.tolist(),
        "sampled_groups_sha256_sorted_newline_joined": DA.sha256_lines(sampled_sorted),
    }
    (RAND / "randomness_and_draw_record.json").write_text(json.dumps(record, indent=1) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k != "draw_order"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
