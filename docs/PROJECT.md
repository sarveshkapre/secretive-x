# PROJECT

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Dev
```bash
PYTHONPATH=src python3 -m secretive_x.cli --help
```

## Test
```bash
PYTHONPATH=src pytest
```

## Lint
```bash
ruff check src tests
```

## Typecheck
```bash
mypy src
```

## Build
```bash
python3 -m build
```

## Security
```bash
bandit -q -r src
pip-audit -r requirements.txt
```

## Check (quality gate)
```bash
make check
```

## Release
```bash
make release
```

## Next 3 improvements
1. Secure Enclave provider (macOS)
2. TPM provider (Linux/Windows)
3. Agent integration for key caching
