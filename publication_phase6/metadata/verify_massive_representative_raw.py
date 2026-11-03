#!/usr/bin/env python3
"""Stream the one public MassIVE RAW used for the Phase 6 linkage check.

By default HTTPS certificate validation is enabled. The 2026-11-03 execution had
a self-signed certificate chain on the MassIVE download endpoint, so the recorded
check used an explicitly unverified TLS context and then compared the full-file
SHA-1 to the checksum already embedded in the hash-verified mzML source record.
The downloaded payload is never written to disk.
"""
import argparse,hashlib,ssl,urllib.parse,urllib.request
FD='f.MSV000094528/raw/20220601_positive/20220613_100AGC_60000Res_pluskal_mce_1D1_A18_id.raw'
EXPECTED='ea7e6f809882e4a9ff4c04f7cef2011ca2c6efb3'; EXPECTED_SIZE=31994595
p=argparse.ArgumentParser();p.add_argument('--allow-unverified-tls',action='store_true');a=p.parse_args()
url='https://massive.ucsd.edu/ProteoSAFe/DownloadResultFile?'+urllib.parse.urlencode({'file':FD,'forceDownload':'true'})
ctx=ssl._create_unverified_context() if a.allow_unverified_tls else None
req=urllib.request.Request(url,headers={'User-Agent':'MURU-Phase6-Metadata-Audit/1.0'})
h=hashlib.sha1();n=0
with urllib.request.urlopen(req,context=ctx,timeout=180) as response:
 while block:=response.read(1024*1024):h.update(block);n+=len(block)
if n!=EXPECTED_SIZE or h.hexdigest()!=EXPECTED:raise SystemExit(f'FAIL size={n} sha1={h.hexdigest()}')
print(f'PASS MassIVE RAW {FD}: bytes={n} SHA1={h.hexdigest()} matches hash-verified mzML sourceFile')
