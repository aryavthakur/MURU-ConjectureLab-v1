"""Project-scope gate (2026-09-19). Design B is CANCELLED and must never execute.

MURU is now computational and online/public-data only: no wet lab, no compound purchasing, no vendor outreach,
no physical samples, no new mass-spectrometer acquisition. Every Design B entry point calls refuse() first.
There is deliberately no override variable. See MURU_CE_INTERFACE_ADJUDICATION_DESIGN_B_SCOPE_CLOSURE.md.
"""
CLOSURE_RECORD = "MURU_CE_INTERFACE_ADJUDICATION_DESIGN_B_SCOPE_CLOSURE.md"


def refuse() -> None:
    raise SystemExit(
        "refusing: Design B is CANCELLED by the 2026-09-19 project-scope correction (online/public-data only; "
        f"no procurement, vendor contact, samples or acquisition). See {CLOSURE_RECORD}."
    )
