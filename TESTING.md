# Testing Guide

## Quick Commands

```bash
# Fejlesztés közben (gyors)
pytest -m unit

# Release előtt (teljes)
pytest

# Csak agents
pytest -m "unit and agents"

# Csak integráció (lassú)
pytest -m integration

# Coverage report
pytest -m unit --cov=src --cov-report=html
```

## Test Categories

- **unit**: Mock tesztek (90%) - gyors feedback
- **integration**: Valódi API tesztek (10%) - release validation
- **e2e**: End-to-end tesztek - critical flows only
