---
name: spec-driven-development
description: 'Apply Spec-Driven Development in this Flask project. Use for spec-first delivery from Gherkin and OpenAPI to tests, implementation, and verification. Trigger words: SDD, spec-first, behavior-first, implement from feature file.'
argument-hint: 'Describe the business rule or endpoint to implement, including acceptance criteria.'
user-invocable: true
---

# Spec-Driven Development Workflow

Use this skill to implement changes in spec-first order.

## Inputs
1. Behavior specs in `features/*.feature`.
2. Contract spec in `openapi.yaml`.
3. Existing tests in `tests/test_*.py`.

## Procedure
1. Clarify behavior and edge cases from feature scenarios.
2. Update or extend `openapi.yaml` for request, responses, status codes, and examples.
3. Write failing tests in `tests/` for:
- success path
- business-rule rejection path
- invalid input path
4. Implement minimal code changes under `app/`:
- `app/routes/` for HTTP parsing and response mapping
- `app/services/` for business rules
- `app/models/` only when state or schema changes are needed
5. Validate with:
- `pytest -q`
- `behave` (or targeted features)
6. If tests fail, fix by tightening spec or code so they converge.

## Output Checklist
1. Spec files changed.
2. Tests added or updated.
3. Implementation files changed.
4. Command results and final pass status.
5. Follow-up tasks, if any.

## Project-Specific Notes
- Keep business logic in service classes.
- Keep route layers thin and deterministic.
- Preserve stable error message wording used by tests.
