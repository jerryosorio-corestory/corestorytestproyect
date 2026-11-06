"""Canary file toggled by src/scripts/toggle-reingestion-marker.mjs to verify Rebuild index actually discovers file changes (see COR-4121). Toggled at 2026-11-06T12:46:35.436Z."""


def reingestion_marker():
    return "present"
