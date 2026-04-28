import os
import re
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = REPO_ROOT / "src"
TESTS_DIR = REPO_ROOT / "tests"


def _should_run(question: str) -> bool:
    """Allow scoping test execution with PACMAN_QUESTIONS=q1,q2,..."""
    selected = os.getenv("PACMAN_QUESTIONS", "").strip()
    if not selected:
        return True
    allowed = {item.strip().lower() for item in selected.split(",") if item.strip()}
    return question.lower() in allowed


@pytest.mark.parametrize(
    "question",
    [
        "q1",
        "q2",
        "q3",
        "q4",
        pytest.param("q5", marks=pytest.mark.slow),
        "q6",
    ],
)
def test_autograder_question(question: str) -> None:
    if not _should_run(question):
        pytest.skip(f"{question} skipped by PACMAN_QUESTIONS filter")

    pythonpath = str(TESTS_DIR) + os.pathsep + str(APP_DIR)
    env = {**os.environ, "PYTHONPATH": pythonpath}

    cmd = [
        sys.executable,
        "-m",
        "autograder",
        "-q",
        question,
        "--no-graphics",
    ]
    completed = subprocess.run(
        cmd,
        cwd=str(APP_DIR),
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
        check=False,
    )

    output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    print(output, end="")

    assert completed.returncode == 0, (
        f"Autograder failed for {question} with exit code {completed.returncode}.\n"
        f"Command: {' '.join(cmd)}\n\n"
        f"Output:\n{output[-8000:]}"
    )

    score_matches = re.findall(
        rf"Question\s+{re.escape(question)}:\s*(\d+)\s*/\s*(\d+)",
        output,
    )
    assert score_matches, (
        f"Could not find score line for {question} in autograder output.\n"
        f"Output:\n{output[-8000:]}"
    )

    earned, total = map(int, score_matches[-1])
    assert earned == total, (
        f"{question} did not receive full score: {earned}/{total}.\n"
        f"Output:\n{output[-8000:]}"
    )
