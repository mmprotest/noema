# Contributing

Thanks for considering a contribution! Ways to help:
- Bug reports and minimal reproductions
- Docs improvements and examples
- Small, focused PRs

## Dev Setup
```bash
uv venv
uv pip install -e .[dev]
pre-commit install
pytest -q
```

## Coding Style

- Ruff and mypy must pass.
- Add or adjust tests for behavior changes.

## PR Checklist

- [ ] Update README/docs if needed
- [ ] Keep CI green
- [ ] Note changes in `CHANGELOG.md`
