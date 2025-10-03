# Security Policy

If you discover a vulnerability, please email security@mmprotest.org or open a private advisory on GitHub.
Scope: this repository and its dependencies as pinned in `pyproject.toml`.

## Reporting
- Provide reproduction steps and affected versions.
- We aim to respond within 7 days and issue a fix or mitigation where applicable.

## Data Handling
- Avoid committing real PII in `.noema` bundles or logs.
- Use the deterministic dummy backend for examples and tests.
