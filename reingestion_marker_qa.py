"""Canary file toggled by src/scripts/toggle-reingestion-marker.mjs to verify Rebuild index actually discovers file changes (see COR-4121). Toggled at 2026-11-10T19:51:47.627Z."""


def reingestion_marker():
    return "present"
