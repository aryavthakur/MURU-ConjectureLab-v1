# Protocol V2 Amendment A-1: verification of the predeclared randomness pulse

**Study:** `muru-v2-msnlib-confirmation-2.0`. **Amends:** `MURU_V2_MSNLIB_CONFIRMATION_PROTOCOL_V2.md` section 6, rule 3
only. Committed and pushed **before any seed is derived and before any draw**. No replacement-population data of any
kind (not even a sampled group list) exists at this commit.

## What happened

At 2026-09-14T03:01:23Z `scripts/wur_v2_confirmation_v2/03_randomness_and_draw.py` requested the predeclared pulse once
(`https://beacon.nist.gov/beacon/2.0/pulse/time/1789354800000`) and received:

- `uri` `https://beacon.nist.gov/beacon/2.0/chain/2/pulse/1940454`, `timeStamp` `2026-09-14T03:00:00.000Z` (exactly the
  predeclared pulse), `statusCode` 0, `cipherSuite` 0;
- raw response saved as `artifacts/wur_v2_confirmation_v2/randomness/nist_beacon_pulse_raw.json`, sha256
  `6a4eed54b9000c9f6aaa788205788418c83aa4d17dc1dc001f125d4d7d48aa5a`;
- the certificate named by the pulse, from `https://beacon.nist.gov/beacon/2.0/certificate/<certificateId>`, saved as
  `nist_beacon_certificate.pem`, sha256 `c342339ca0fe5f1c522e03471b32811310371c3adbb8f107c8d77b5f336bfce9`.

Verification results:
- `outputValue` equals SHA-512 of the NIST 2.0 serialization followed by the signature bytes: **valid**;
- `certificateId` equals SHA-512 of the DER encoding of the returned certificate: **valid** (it is the certificate
  the pulse designates);
- RSA-SHA512 `signatureValue`: **not verifiable**. The designated certificate carries a **2,048-bit** RSA key
  (valid 2026-09-03 to 2027-03-20), while `signatureValue` is a **4,096-bit** value (1,024 hex characters). A 2,048-bit
  key cannot have produced it. The verifier is not at fault: the same code verified the chain 1 pulse 1 signature
  against its 4,096-bit certificate before the protocol commit, and the chain 1 key does not verify this pulse
  (PKCS#1 v1.5 or PSS).

Section 6 rule 3 required STOP on a failed verification. The script stopped: `STOPPED.json` (sha256
`75d345d40ad0ac7c6379e6e5c7fd4c77f78366ddfde2aa3801a569d130901a8a`) was written, no seed was derived, nothing was drawn.

## Amendment

Rule 3 of section 6 is replaced, for this pulse only, by:

3'. The pulse is accepted if (a) its `timeStamp` is exactly the predeclared one; (b) `outputValue` equals SHA-512 of
the NIST 2.0 serialization followed by the signature bytes; (c) `certificateId` equals SHA-512 of the DER encoding of
the certificate NIST serves for it; and (d) a second retrieval of the **same** pulse through its canonical URI
(`https://beacon.nist.gov/beacon/2.0/chain/2/pulse/1940454`) returns a pulse object identical in every field to the
saved response. The RSA signature result and the key-size mismatch are recorded and disclosed, not used as a gate.

Everything else in section 6 and section 7 is unchanged: the same pulse, the same seed rule
`seed = int(hashlib.sha256(bytes.fromhex(pulse.outputValue)).hexdigest()[:16], 16)`, the same single draw.

## Why this does not weaken the independence of the draw

The purpose of section 6 is that the seed is not chosen by us. That is unaffected: the pulse was fixed by timestamp
before it existed, it was retrieved once from NIST over TLS, its content is publicly re-fetchable by anyone at the
canonical URI, and this amendment changes only how that one pulse's provenance is documented. No alternative pulse and
no alternative seed is considered. The amendment gives strictly less latitude than substituting another pulse, which
the governing mandate permits only through a documented amendment made before any replacement-population outcome is
seen.

The draw is executed by `scripts/wur_v2_confirmation_v2/03b_draw_under_amendment_a1.py`, which refuses to run unless
this amendment is committed at HEAD and present on origin.
