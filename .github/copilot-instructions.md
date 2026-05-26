# Project Guidelines

## Spec-Driven Development First
This repository follows Spec-Driven Development (SDD).

Order of truth for every change:
1. Business behavior in Gherkin features under `features/`.
2. API contract in `openapi.yaml`.
3. Tests in `tests/` (pytest) and BDD scenarios (behave).
4. Implementation in `app/routes/`, `app/services/`, and `app/models/`.

If code and spec disagree, update the spec first and then align code.

## Required Workflow Per Change
1. Define or update behavior scenario in `features/*.feature`.
2. Define or update endpoint contract and examples in `openapi.yaml`.
3. Add or update failing tests in `tests/test_*.py`.
4. Implement minimal code change to make tests pass.
5. Run full test suite and report any regressions.

## Build and Test Commands
- Install deps: `pip install -r requirements.txt`
- Run tests: `pytest -q`
- Run BDD: `behave`
- Run app: `python run.py`

## Conventions
- Keep route handlers thin; place business rules in services.
- Return explicit and stable error messages for business-rule failures.
- Preserve endpoint response shapes used by existing tests.
- For each new business rule, include at least one success and one failure test.

## Definition Of Done
A change is complete only when:
1. Updated feature scenarios reflect intended behavior.
2. `openapi.yaml` is aligned with the implemented API.
3. `pytest -q` passes.
4. Relevant `behave` scenarios pass.
