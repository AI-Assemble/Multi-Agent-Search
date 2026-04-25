<h1> 
Pacman Multi-Agent Project

<br>
<img src="assets/pacman.png" width="400" align="center" />
</h1>

This repository is set up as a complete Python project with:

- a `pyproject.toml` project configuration
- `pytest`-based test hooks that execute the existing Pacman autograder questions
- `Taskfile.yml` as the single source of truth for test commands
- GitHub Actions CI to run tests on push and pull request

## Project Structure

* `src/`: all Python source packages
  * `src/core/`: Pacman game source — MVC + Agent-Based architecture
    * `model/`, `view/`, `controller/`: MVC layers
    * `agents/`: agent implementations (`Reflex`, `Minimax`, `AlphaBeta`, `Expectimax`, etc.)
    * `config/`: project parameter configuration for autograder
  * `src/app/`: interactive CLI launcher, split into focused modules:
    * `colors.py`, `keys.py`, `fs.py`, `menu.py`, `process.py`, `metrics.py`, `batch.py`
    * `__main__.py`: entry point — invoke with `PYTHONPATH=src python -m app`
* `tests/`: all test assets in one place
  * `autograder.py`, `grading.py`, `testClasses.py`, `testParser.py`, `multiagentTestClasses.py`: autograder engine (moved from `src/core/`)
  * `make_pytest.py`: pytest bridge that drives the autograder
  * `q1/` … `q5/`: per-question `.test` and `.solution` files side by side
* `layouts/`: Pacman map layout files
- `Taskfile.yml`: reusable local/CI task definitions
- `.vscode/tasks.json`: VS Code task bindings — includes `Run: Pacman Launcher` and all test targets
- `.vscode/launch.json`: VS Code debug profiles — `Launcher` runs `python -m app` with `PYTHONPATH=src`
- `.github/workflows/q1.yml` ... `.github/workflows/q5.yml`: per-question CI workflows

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

## Three Ways To Run

This repo supports three equivalent workflows:

1. `Legacy-compatible mode`:
Use the classic Berkeley-style file names from the repository root such as `pacman.py`, `autograder.py`, and `multiAgents.py`.
This is the easiest path if you want the original assignment commands from the docs to keep working.

2. `Refactored native mode`:
Use the current package layout under `src/core` and `tests`.
This is the better fit if you want to work directly with the new structure and explicit package paths.

3. `Taskfile mode`:
Use the `Taskfile.yml` targets to run the launcher and tests consistently across environments (CI uses the same targets).
This is the most robust and reproducible way to run, and the one we recommend for most users.

### Legacy-compatible mode

Run Pacman from the repository root:

```bash
python pacman.py
python pacman.py -p ReflexAgent -l testClassic
```

Run the autograder from the repository root:

```bash
python autograder.py
python autograder.py -q q2 --no-graphics
```

Edit the compatibility file at the repository root if you want to follow the original assignment wording:

```bash
multiAgents.py
```

These root-level files are thin facades that forward to the refactored implementation under `src/core` and `tests`.

### Refactored native mode

Run the graphical launcher:

```bash
PYTHONPATH=src .venv/Scripts/python.exe -m app --python-bin .venv/Scripts/python.exe
```

Run Pacman directly from the refactored package:

```bash
PYTHONPATH=src/core .venv/Scripts/python.exe -m controller.pacman -p ReflexAgent -l mediumClassic -k 2
```

Run the autograder directly against the refactored structure:

```bash
PYTHONPATH="tests;src/core" .venv/Scripts/python.exe -m autograder -q q2 --no-graphics
```

Edit the canonical implementation file if you want to work directly in the new structure:

```bash
src/core/agents/multiAgents.py
```

### Option 3: Taskfile mode

Use the `Taskfile.yml` targets as a single, reproducible way to run the launcher and tests. The Taskfile is used by CI and local development and automatically prefers `uv run` when available, falling back to the active Python interpreter.

Run the graphical launcher via Task:

```bash
task run:pacman
```

Run tests via Task:

```bash
task test
task test:fast
task test:q2
```

You can also pass environment overrides to Task (example: choose interpreter or agent):

```bash
PYTHON_BIN=/path/to/python task test
PACMAN_AGENT=ExpectimaxAgent PACMAN_LAYOUT=minimaxClassic task run:pacman
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

Run graphical simulation:

```bash
task run:pacman
```

By default, `task run:pacman` opens an interactive launcher before execution.
After each game finishes, the launcher prints a detailed status log and returns to the main menu.
Each attempt also saves a timestamped `.log` file under `logs/` and prints the saved path on the CLI.
Closing a graphics window marks that game as interrupted and the launcher keeps running the remaining attempts.

You can configure multiple parameters first (Agent, Layout, Ghosts, Games), then return to the main menu and choose `Execute` to start.
Ghosts and Games now accept direct numeric input instead of fixed option lists.
Parallel also accepts direct numeric input from the launcher menu.
You can also set `--parallel=num` to run up to `num` game windows at the same time.

The launcher now includes:

- Colorized CLI output for better readability
- A live description panel for the currently selected menu item
- A clear key legend inside the UI

- Up/Down arrows: move selection
- `Space` or `Enter`: select the focused option
- Number keys `1..9`: quick-select by option index
- `q`: quit launcher (without running)

Optional overrides:

```bash
PACMAN_AGENT=ExpectimaxAgent PACMAN_LAYOUT=minimaxClassic PACMAN_GHOSTS=2 task run:pacman
```

When launch parameters are provided (`PACMAN_AGENT`, `PACMAN_LAYOUT`, `PACMAN_GHOSTS`, `PACMAN_GAMES`, `PACMAN_PARALLEL`, `PACMAN_EXTRA_ARGS`), the launcher skips the interactive menu and runs directly.
Add `PACMAN_PARALLEL` if you want Taskfile to pass `--parallel` automatically.

Direct module-mode examples (without Taskfile, refactored native mode):

```bash
PYTHONPATH=src .venv/Scripts/python.exe -m app --python-bin .venv/Scripts/python.exe
```

```bash
PYTHONPATH=src/core .venv/Scripts/python.exe -m controller.pacman -p ReflexAgent -l mediumClassic -k 2
```

```bash
# Run autograder directly (tests/ dir contains both engine and test data)
PYTHONPATH="tests;src/core" .venv/Scripts/python.exe -m autograder -q q2 --no-graphics
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

- each question has its own workflow (`CI Q1` ... `CI Q5`)
- every workflow triggers on `push` to `main` and all pull requests
- every workflow uses Python `3.11` only
- every workflow installs and uses Task runner
- each workflow executes one Taskfile target (`task test:q1` ... `task test:q5`)
- skip CI by starting your commit message with `[skip ci]` on push
- skip CI on pull request by starting PR title with `[skip ci]`
