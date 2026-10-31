"""Canary file toggled by src/scripts/toggle-reingestion-marker.mjs to verify Rebuild index actually discovers file changes (see COR-4121). Toggled at 2026-10-31T00:06:23.083Z."""


def reingestion_marker():
    return "present"
