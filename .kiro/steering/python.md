---
inclusion: fileMatch
fileMatchPattern: "**/*.py"
---

# Python

## Mandatory Delegation
- **NEVER edit `*.py` files directly** — always delegate to the `python` subagent via `invokeSubAgent`, regardless of how small the change is.

## Terminal Safety — Never Concatenate Python to Terminal

**CRITICAL — violating this kills the terminal session. No exceptions.**

❌ FORBIDDEN — inline Python via shell:
```bash
python3 -c "import json; print(json.dumps({'key': 'value'}))"
```

❌ FORBIDDEN — piping content into Python:
```bash
echo 'print("hello")' | python3
```

✅ CORRECT — write a `.py` file first, then execute as separate commands:
1. Use `fsWrite` to create the `.py` script
2. Activate venv: `source .venv/bin/activate` (separate command)
3. Run: `python script.py` (separate command)
4. Delete the script if it was one-off

## Never Chain Shell Commands

**NEVER** use `&&`, `||`, `;`, `|`, `2>&1`, or any other chaining. Each command must be a separate invocation.

## Virtual Environment

All Python execution happens inside `.venv/` in the project root.

### Setup (one-time, if venv missing)
Run each as a separate shell invocation:
1. `python3 -m venv .venv`
2. `source .venv/bin/activate`
3. `pip install -r requirements.txt`

### Running Tests
Run each as a separate shell invocation:
1. `source .venv/bin/activate`
2. `python -m pytest tests/unit/ -v`

### Rules
- Never run Python or pytest globally — always activate the venv first
- Use `python -m pytest` instead of bare `pytest`
- The venv directory (`.venv/`) is in `.gitignore`

## Testing with pytest

- Write focused tests for individual functions and classes
- Use descriptive test names: `test_handler_returns_200_on_valid_input`
- Tests live in `tests/unit/`
- Test edge cases: empty inputs, boundary values, error conditions, None values

## AWS Mocking with moto

- Use `@mock_aws` decorator (moto 5.x) for all AWS service mocking
- Always set `AWS_DEFAULT_REGION` in test environment
- Set up mock resources in fixtures before invoking Lambda handlers

### Fixture Owns the Mock Context, Not the Test

❌ INCORRECT — adding `@mock_aws` to the test when fixture already owns context:
```python
@pytest.fixture
def table():
    with mock_aws():
        yield create_table()

@mock_aws  # Creates separate context — table won't exist here
def test_something(table):
    ...
```

✅ CORRECT — let the fixture own the context:
```python
@pytest.fixture
def table():
    with mock_aws():
        yield create_table()

def test_something(table):  # No @mock_aws here
    ...
```

## boto3 Best Practices
- Create clients/resources inside functions, not at module level (testability)
- Use `region_name` parameter explicitly
- Handle `ClientError` exceptions with specific error code checks
