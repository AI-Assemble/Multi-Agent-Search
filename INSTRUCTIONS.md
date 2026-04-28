# Project Instructions

This file defines the working rules for this repository.

## 1) Assignment Scope

- Main coding task for the course assignment is in src/core/agents/multiAgents.py.
- Keep provided class and function names unchanged to stay compatible with the autograder.
- Do not modify autograder internals unless you are intentionally changing test infrastructure.
- File naming convention: snake_case for all new Python files (e.g. my_module.py, not myModule.py).

### Architecture Layout

- src/core/model: world/state model code.
- src/core/view: graphics/text rendering code.
- src/core/controller: game-loop/control entry code.
- src/core/agents: Pacman and Ghost agent logic.
- src/core/config: project parameters used by the autograder.
- src/app/: interactive CLI launcher, split into focused modules:
  - colors.py: ANSI constants and paint helper.
  - keys.py: raw keyboard reader and screen clear.
  - fs.py: filesystem helpers (layouts, banner, log paths).
  - menu.py: interactive TUI menus and setup wizard.
  - process.py: subprocess utilities (build command, stop process, append log).
  - metrics.py: score/result extraction from stdout and CSV row management.
  - batch.py: batch orchestration, live dashboard, and game attempt runner.
  - __main__.py: entry point, invoke with `PYTHONPATH=src python -m app`.
- tests/: autograder engine + test data together.
  - autograder.py, grading.py, testClasses.py, testParser.py, multiagentTestClasses.py: engine.
  - make_pytest.py: pytest bridge.
  - q1/ … q5/: .test and .solution files side by side.
- Do not add compatibility wrappers back into src/core/*.py root.

## 2) Testing Rules

- Use Taskfile as the single source of truth for test execution.
- Run tests through Task targets, not ad hoc command variations.
- Preferred runtime path is uv run when available.
- If uv is not installed, commands must fallback to normal Python execution.
- Current pytest wrapper is score-aware:
  - It checks per-question score lines from autograder output.
  - A test passes only when earned score equals total score for that question.

## 3) Local Execution

Recommended setup:

1. Install uv.
2. Run uv sync --group dev.
3. Run Task targets, for example:
   - task test
   - task test:fast
   - task test:q2

If a specific interpreter is needed:

- Set PYTHON_BIN to the interpreter path before running task.

## 4) CI/CD Rules

- CI is split per question with separate workflows:
  - .github/workflows/q1.yml
  - .github/workflows/q2.yml
  - .github/workflows/q3.yml
  - .github/workflows/q4.yml
  - .github/workflows/q5.yml
- All workflows run with Python 3.11 only.
- Dependencies are installed from pyproject.toml via uv sync --group dev.
- CI skip policy:
  - Push: start commit message with [skip ci]
  - Pull request: start PR title with [skip ci]

## 5) VS Code Integration Rules

- VS Code tasks are bindings to Taskfile targets in .vscode/tasks.json.
- .vscode/tasks.json includes a "Run: Pacman Launcher" task that delegates to task run:pacman.
- Launch profiles in .vscode/launch.json are available for per-question pytest runs and the launcher.
- The "Launcher" debug profile uses module: app with PYTHONPATH set to the workspace src/ directory.
- Keep task and launch entries aligned with Taskfile target names.

## 6) How To Add A New Question

When a new question is introduced (example: q6), apply this checklist:

1. Tests and assets
   - Add relevant test case folder under tests/q6.
   - Put .test files under tests/q6.
   - Put .solution files under tests/q6 (alongside .test files).
   - Ensure autograder can run q6 from src/core.

2. Pytest bridge
   - Update tests/make_pytest.py:
     - Add q6 into parametrized question list.
     - Mark as slow only if needed.

3. Taskfile
   - Add a new target in Taskfile.yml:
     - test:q6
   - Keep uv-first and Python fallback behavior.

4. VS Code tasks
   - Add Tests: Q6 in .vscode/tasks.json mapped to task test:q6.

5. VS Code launch
   - Add Pytest: Q6 in .vscode/launch.json with PACMAN_QUESTIONS=q6.

6. CI workflow
   - Create .github/workflows/q6.yml.
   - Use Python 3.11.
   - Install uv.
   - Run uv sync --group dev.
   - Execute task test:q6.
   - Keep the same [skip ci] condition pattern as other workflows.

7. Documentation
   - Update README.md CI section and task examples to include q6.
   - Update this file if process rules change.

8. Validation
   - Run local check first:
     - task test:q6
   - Run broader checks if needed:
     - task test:fast
     - task test

## 7) Definition of Done

Changes are complete when all of the following are true:

- Task target for the affected question runs correctly.
- CI workflow for that question is valid and consistent with repository rules.
- README and INSTRUCTIONS are updated if behavior changed.
- No JSON/YAML syntax errors in .vscode and .github/workflows files.

## 8) Q6 Investigation Context: Risk-aware Evaluation Function

- User request on 2026-04-28: redesign Q6 from AI usage reflection into a coding task named Risk-aware Evaluation Function, and add related tests/docs/functions.
- Existing Q6 docs only described a Gradescope reflection; no `tests/q6` folder existed.
- Existing autograder support already includes `EvalAgentTest` in `tests/multiagentTestClasses.py`, which can run a named Pacman agent over multiple games and award partial credit for non-timeouts, average score, and wins.
- Q6 mirrors the Q5 structure:
  - `src/core/agents/multiAgents.py` contains the submission-facing `riskAwareEvaluationFunction(state)` TODO stub; do not provide a ready-made scoring formula there.
  - Q6 tests should run an existing search agent with `agentArgs: "evalFn=riskAware"` rather than using a separate Q6 agent/helper module.
  - Keep the Q6 abbreviation `riskAware = riskAwareEvaluationFunction` in `multiAgents.py`; do not add a separate `q6` alias.
- Q6 test infrastructure:
  - `tests/q6/CONFIG`
  - `tests/q6/grade-agent.test`
  - `tests/q6/grade-agent.solution`
  - `tests/CONFIG` includes q6 in autograder order.
  - `tests/make_pytest.py` includes q6 in pytest-driven question coverage.
- Q6 execution entry points:
  - `task test:q6`
  - VS Code task `Tests: Q6`
  - VS Code launch profile `Pytest: Q6`
  - CI workflow `.github/workflows/q6.yml`
