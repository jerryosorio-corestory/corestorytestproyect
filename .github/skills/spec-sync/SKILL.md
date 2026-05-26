---
name: spec-sync
description: 'Synchronize feature files, OpenAPI contract, tests, and Flask implementation. Use for drift detection and contract-behavior consistency checks.'
argument-hint: 'Provide scope: books, members, loans, or full project.'
user-invocable: true
---

# Spec Sync Audit

Use this skill to detect and fix drift between specs and code.

## Drift Types
1. Feature drift: behavior in `features/` not covered in tests.
2. Contract drift: `openapi.yaml` differs from actual endpoint behavior.
3. Implementation drift: code applies rules not represented in specs.

## Procedure
1. Map each changed endpoint to:
- Gherkin scenario(s)
- OpenAPI path and responses
- pytest case(s)
2. Verify that expected status codes and payload shapes match across all artifacts.
3. Verify business-rule errors are documented and tested.
4. Run validation commands:
- `pytest -q`
- `behave`
5. Apply minimal fixes in spec, tests, or code to remove drift.

## Acceptance Criteria
1. No undocumented status code changes.
2. No scenario without automated test coverage.
3. No service rule missing from feature or contract specs.
4. Test suite passes after synchronization.

## Report Format
1. Mismatches found.
2. Files updated to resolve mismatches.
3. Test and BDD execution status.
4. Residual risk and recommendations.
