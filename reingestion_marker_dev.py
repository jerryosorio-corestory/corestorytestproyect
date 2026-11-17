"""Canary file toggled by src/scripts/toggle-reingestion-marker.mjs to verify Rebuild index actually discovers file changes (see COR-4121). Toggled at 2026-11-17T10:53:25.400Z."""


def reingestion_marker():
    return "present"
