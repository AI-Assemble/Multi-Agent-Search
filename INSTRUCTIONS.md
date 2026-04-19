# Project Instructions

This file defines the working rules for this repository.

## 1) Assignment Scope

- Main coding task for the course assignment is in app/agents/multiAgents.py.
- Keep provided class and function names unchanged to stay compatible with the autograder.
- Do not modify autograder internals unless you are intentionally changing test infrastructure.

### Architecture Layout

- app/model contains world/state model code.
- app/view contains graphics/text rendering code.
- app/controller contains game-loop/control entry code.
- app/agents contains Pacman and Ghost agent logic.
- app/testing contains autograder and grading internals.
- app/config contains project parameters used by the autograder.
- Do not add compatibility wrappers back into app/*.py root.

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
- Launch profiles in .vscode/launch.json are available for per-question pytest runs.
- Keep task and launch entries aligned with Taskfile target names.

## 6) How To Add A New Question

When a new question is introduced (example: q6), apply this checklist:

1. Tests and assets
   - Add relevant test case folder under tests/q6.
   - Put .test files under tests/q6.
   - Put .solution files under solutions/q6.
   - Ensure autograder can run q6 from app.

2. Pytest bridge
   - Update tests/test_autograder_questions.py:
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
