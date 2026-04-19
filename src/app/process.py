import os
import shlex
import subprocess
import threading
import time
from pathlib import Path


def _build_command(
    python_bin: str,
    app_root: Path,
    *,
    agent: str,
    layout: str,
    ghosts: int,
    num_games: int,
    extra: list[str],
) -> tuple[list[str], dict[str, str]]:
    cmd = [
        python_bin,
        "-m",
        "controller.pacman",
        "-p",
        agent,
        "-l",
        layout,
        "-k",
        str(ghosts),
        "-n",
        str(num_games),
        *extra,
    ]
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    app_path = str(app_root)
    env["PYTHONPATH"] = app_path if not existing else app_path + os.pathsep + existing
    return cmd, env


def _format_command(cmd: list[str]) -> str:
    if hasattr(shlex, "join"):
        return shlex.join(cmd)
    return subprocess.list2cmdline(cmd)


def _stop_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        process.terminate()
    except OSError:
        return

    deadline = time.time() + 1.0
    while process.poll() is None and time.time() < deadline:
        time.sleep(0.05)

    if process.poll() is None:
        try:
            process.kill()
        except OSError:
            pass


def _append_text(path: Path, lock: threading.Lock, content: str) -> None:
    with lock:
        with path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
