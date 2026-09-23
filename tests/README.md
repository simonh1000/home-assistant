# Home Assistant Automation Emulation Tests

This directory contains real-engine emulation tests for [`src/automations/ev-capacity-guardian.yaml`](../src/automations/ev-capacity-guardian.yaml).

Instead of re-implementing the state machine in custom Python code, these tests run **unmodified Home Assistant YAML automations** inside a headless, in-memory Home Assistant core using `pytest-homeassistant-custom-component`.

## Environment Setup

The test environment uses `uv` with Python 3.13 and lives in an isolated virtual environment at `tests/.venv` (~563 MB).

### Python Concepts

- **`venv` (Virtual Environment):** A virtual environment is a self-contained folder that isolates Python packages specifically for a single project. This prevents software dependencies and versions from interfering with your system Python or other projects on your machine.
- **`uv`:** `uv` is an extremely fast, modern tool used to manage Python versions and install project packages. It downloads the required Python runtime and dependencies in seconds while keeping everything cleanly contained inside your project.

To set up or sync the environment:
```bash
uv venv tests/.venv --python 3.13
uv pip install --python tests/.venv pytest pytest-homeassistant-custom-component pyyaml
```

## Running the Tests

To run the entire test suite:
```bash
tests/.venv/bin/pytest tests/ -v
```

To run the CSV history replay test with live console output (Flanders capacity tariff peak report & state change events table):
```bash
tests/.venv/bin/pytest tests/test_csv_replay.py -v -s
```

## Test Files

- `conftest.py`: Bootstraps Home Assistant core components (`automation`, `input_select`, `input_boolean`, `sensor`, `select`) and tracks service calls.
- `test_ev_capacity_guardian.py`: Synthetic unit tests verifying automation triggers (e.g., high load pause >6kW for 30s, non-charging notifications, quiet house transition to cooldown).
- `test_csv_replay.py`: Replays real P1 meter history from `tests/test1.csv` through HA's engine, outputting state change events and Flanders Tariff savings.
- `test1.csv`: Historical P1 meter readings export.
