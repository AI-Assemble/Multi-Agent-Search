# Pacman Multi-Agent Project

This repository is set up as a complete Python project with:

* a `pyproject.toml` project configuration
* `pytest`-based test hooks that execute the existing Pacman autograder questions
* `Taskfile.yml` as the single source of truth for test commands
* GitHub Actions CI to run tests on push and pull request

## Project Structure

* `app/`: Berkeley Pacman source code and autograder
* `app/tests/`: existing assignment tests used by `autograder.py`
* `tests/`: pytest hooks that invoke `autograder.py`
* `Taskfile.yml`: reusable local/CI task definitions
* `.vscode/tasks.json`: VS Code bindings to Taskfile tasks
* `.github/workflows/q1.yml` ... `.github/workflows/q5.yml`: per-question CI workflows

## Local Setup (.venv)

Recommended: use [`uv`](https://docs.astral.sh/uv/) for environment and dependency management.

```bash
uv sync
```

If you prefer manual setup with `.venv`, use the steps below.

Create virtual environment (if needed):

```powershell
python -m venv .venv
```

Install development dependencies:

```powershell
.venv\Scripts\python.exe -m ensurepip --upgrade
.venv\Scripts\python.exe -m pip install --upgrade pip uv
uv sync --group dev
```

## Run Tests (Taskfile)

Install Task runner (one-time):

> You can see another installation method on the official [Taskfile website](https://taskfile.dev/docs/installation).

```bash
# Windows (Scoop)
scoop install task

# macOS (Homebrew)
brew install go-task

# Linux/macOS (official install script)
sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d
```

Then run tests through Taskfile:

```bash
task test
task test:fast
task test:slow
task test:q2
task test:q2q3
```

Note: Taskfile is configured to try `uv run` first for Python commands, and automatically fallback to regular Python when `uv` is unavailable.

If you want Taskfile to use a specific interpreter:

```bash
PYTHON_BIN=/path/to/python task test
```

PowerShell:

```powershell
$env:PYTHON_BIN = "<path-to-python>"
task test
```

## Run Tests (Direct pytest)

Run all hooked autograder tests through pytest:

```powershell
.venv\Scripts\python.exe -m pytest
```

Run only selected question(s):

```powershell
$env:PACMAN_QUESTIONS="q2,q3"
.venv\Scripts\python.exe -m pytest
```

Run only slow checks (currently Q5):

```powershell
.venv\Scripts\python.exe -m pytest -m slow
```

## CI Behavior

Workflow files: `.github/workflows/q1.yml` ... `.github/workflows/q5.yml`

* each question has its own workflow (`CI Q1` ... `CI Q5`)
* every workflow triggers on `push` to `main` and all pull requests
* every workflow uses Python `3.11` only
* every workflow installs and uses Task runner
* each workflow executes one Taskfile target (`task test:q1` ... `task test:q5`)
* skip CI by starting your commit message with `[skip ci]` on push
* skip CI on pull request by starting PR title with `[skip ci]`
