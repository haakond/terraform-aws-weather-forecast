---
inclusion: fileMatch
fileMatchPattern: "**/*.py"
---

# Python Steering

## Mandatory Delegation
- **NEVER edit `*.py` files directly** — always delegate to the `python` subagent via `invokeSubAgent`, regardless of how small the change is.

## Virtual Environment

Always run Python tests inside the virtual environment at `.venv/` in the project root.

### Setup (one-time)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install pytest boto3 moto requests
```

### Running Tests
```bash
source .venv/bin/activate
python -m pytest tests/unit/ -v
```

### Rules
- Never run pytest globally — always activate the venv first
- Use `python -m pytest` instead of bare `pytest`
- The venv directory (`.venv/`) is in `.gitignore`

## Terminal Safety — Never Concatenate Python to Terminal

**CRITICAL**: Never paste or concatenate Python code directly into the terminal via shell commands. This kills the terminal session.

**❌ INCORRECT:**
```bash
python3 -c "import json; print(json.dumps({'key': 'value'}))"
```

**✅ CORRECT — use fsWrite to create files, then execute:**
1. Use `fsWrite` to write Python scripts to `.py` files
2. Run the script: `source .venv/bin/activate && python script.py`
3. For code edits, use multiple small `editCode` / `strReplace` calls

## moto — Fixture Owns the Mock Context, Not the Test

**❌ INCORRECT — adding `@mock_aws` to the test when fixture already owns context:**
```python
@pytest.fixture
def table():
    with mock_aws():
        yield create_table()

@mock_aws  # Creates separate context — table won't exist here
def test_something(table):
    ...
```

**✅ CORRECT — let the fixture own the context:**
```python
@pytest.fixture
def table():
    with mock_aws():
        yield create_table()

def test_something(table):  # No @mock_aws here
    ...
```
