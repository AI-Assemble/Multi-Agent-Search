#!/usr/bin/env python3
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import os
import platform
from datetime import datetime
import re
import shlex
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"
INVERT = "\033[7m"

CSV_FIELDS = [
    "attempt_display",
    "attempt_number",
    "total_attempts",
    "window_title",
    "status",
    "return_code",
    "started_at",
    "finished_at",
    "duration_seconds",
    "agent",
    "layout",
    "ghosts",
    "parallel",
    "score",
    "average_score",
    "result",
    "wins",
    "games_reported",
    "win_rate",
    "record",
]


def _paint(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


def _available_layouts(root: Path) -> list[str]:
    layouts_dir = root / "layouts"
    if not layouts_dir.exists():
        return ["mediumClassic"]
    names = [p.stem for p in layouts_dir.glob("*.lay")]
    return sorted(set(names)) or ["mediumClassic"]


def _load_team_banner(root: Path) -> list[str]:
    banner_path = root / "app" / "config" / "name.txt"
    if not banner_path.exists():
        return ["Assemble"]
    lines = banner_path.read_text(encoding="utf-8").splitlines()
    return lines or ["Assemble"]


class _KeyReader:
    def __enter__(self):
        if os.name == "nt":
            import msvcrt  # type: ignore

            self._msvcrt = msvcrt
            return self

        import termios
        import tty

        self._termios = termios
        self._tty = tty
        self._fd = sys.stdin.fileno()
        self._old = termios.tcgetattr(self._fd)
        tty.setraw(self._fd)
        return self

    def __exit__(self, exc_type, exc, tb):
        if os.name != "nt":
            self._termios.tcsetattr(self._fd, self._termios.TCSADRAIN, self._old)

    def read_key(self) -> str:
        if os.name == "nt":
            ch = self._msvcrt.getch()
            if ch in (b"\x00", b"\xe0"):
                ch2 = self._msvcrt.getch()
                if ch2 == b"H":
                    return "UP"
                if ch2 == b"P":
                    return "DOWN"
                return "OTHER"
            if ch == b" ":
                return "SPACE"
            if ch in (b"\r", b"\n"):
                return "ENTER"
            if ch.lower() == b"q":
                return "QUIT"
            if ch.isdigit() and ch != b"0":
                return f"NUM:{ch.decode()}"
            return "OTHER"

        c1 = sys.stdin.read(1)
        if c1 == "\x1b":
            c2 = sys.stdin.read(1)
            c3 = sys.stdin.read(1)
            if c2 == "[" and c3 == "A":
                return "UP"
            if c2 == "[" and c3 == "B":
                return "DOWN"
            return "OTHER"
        if c1 == " ":
            return "SPACE"
        if c1 in ("\r", "\n"):
            return "ENTER"
        if c1.lower() == "q":
            return "QUIT"
        if c1.isdigit() and c1 != "0":
            return f"NUM:{c1}"
        return "OTHER"


def _clear_screen() -> None:
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def choose_option(
    title: str,
    description: str,
    options: list[str],
    default_index: int = 0,
) -> str | None:
    idx = max(0, min(default_index, len(options) - 1))
    with _KeyReader() as reader:
        while True:
            _clear_screen()
            print(_paint(f"{BOLD}Pacman Launcher - Choose Option{RESET}", CYAN))
            print(_paint(title, BOLD))
            print(_paint(description, DIM))
            print()
            print(
                _paint(
                    "Keys: Up/Down = move | Space/Enter = select | 1..9 = quick select | 0/q = back",
                    YELLOW,
                )
            )
            print()
            for i, opt in enumerate(options, start=1):
                if i - 1 == idx:
                    print(_paint(f"  {i}. {opt}", INVERT))
                else:
                    print(f"  {i}. {opt}")

            print()
            print(_paint("  0. Back to main menu", BLUE))

            key = reader.read_key()
            if key == "UP":
                idx = (idx - 1) % len(options)
            elif key == "DOWN":
                idx = (idx + 1) % len(options)
            elif key in ("SPACE", "ENTER"):
                _clear_screen()
                return options[idx]
            elif key.startswith("NUM:"):
                picked = int(key.split(":", 1)[1]) - 1
                if 0 <= picked < len(options):
                    _clear_screen()
                    return options[picked]
            elif key == "QUIT":
                _clear_screen()
                return None


def _prompt_number(title: str, description: str, current_value: int, minimum: int = 1) -> int | None:
    while True:
        _clear_screen()
        print(_paint(f"{BOLD}Pacman Launcher - Enter Value{RESET}", CYAN))
        print(_paint(title, BOLD))
        print(_paint(description, DIM))
        print()
        print(_paint(f"Enter an integer >= {minimum}. Press Enter to keep {current_value}, or q to cancel.", YELLOW))
        raw_value = input(_paint(f"Value [{current_value}]: ", GREEN)).strip()
        if raw_value == "":
            return current_value
        if raw_value.lower() == "q":
            return None
        try:
            parsed_value = int(raw_value)
        except ValueError:
            print(_paint("Please enter a valid integer.", YELLOW))
            input(_paint("Press Enter to continue...", GREEN))
            continue
        if parsed_value < minimum:
            print(_paint(f"Value must be at least {minimum}.", YELLOW))
            input(_paint("Press Enter to continue...", GREEN))
            continue
        return parsed_value


def _render_main_menu(menu_items: list[dict[str, str]], selected_index: int, team_banner: list[str]) -> None:
    selected_item = menu_items[selected_index]
    _clear_screen()
    for line in team_banner:
        print(_paint(line, MAGENTA))
    print()
    print(_paint(f"{BOLD}Pacman Launcher - Main Menu{RESET}", CYAN))
    print(_paint("Configure multiple parameters, then choose Execute.", DIM))
    print()
    print(
        _paint(
            "Keys: Up/Down = move | Space/Enter = select | 1..9 = quick select | q = quit",
            YELLOW,
        )
    )
    print()

    for i, item in enumerate(menu_items, start=1):
        label = f"  {i}. {item['label']}"
        if i - 1 == selected_index:
            print(_paint(label, INVERT))
        else:
            print(label)

    print()
    print(_paint("Selected Item Description:", GREEN))
    print(_paint(f"- {selected_item['description']}", MAGENTA))


def _run_interactive_setup(root: Path, default_parallel: int) -> tuple[str, str, int, int, int]:
    layout_options = _available_layouts(root)

    state = {
        "agent": "ReflexAgent",
        "layout": "mediumClassic" if "mediumClassic" in layout_options else layout_options[0],
        "ghosts": 2,
        "games": 1,
        "parallel": max(1, int(default_parallel)),
    }

    menu_items = [
        {
            "type": "choice",
            "key": "agent",
            "label": f"Agent: {state['agent']}",
            "description": "Select which Pacman agent implementation to run.",
            "title": "Choose agent",
            "options": [
                "ReflexAgent",
                "MinimaxAgent",
                "AlphaBetaAgent",
                "ExpectimaxAgent",
                "KeyboardAgent",
            ],
        },
        {
            "type": "choice",
            "key": "layout",
            "label": f"Layout: {state['layout']}",
            "description": "Select the game map layout.",
            "title": "Choose layout",
            "options": layout_options,
        },
        {
            "type": "number",
            "key": "ghosts",
            "label": f"Ghosts: {state['ghosts']}",
            "description": "Enter how many ghost agents will spawn.",
            "title": "Enter number of ghosts",
            "minimum": 1,
        },
        {
            "type": "number",
            "key": "games",
            "label": f"Games: {state['games']}",
            "description": "Enter how many games to run in this batch.",
            "title": "Enter number of games",
            "minimum": 1,
        },
        {
            "type": "number",
            "key": "parallel",
            "label": f"Parallel: {state['parallel']}",
            "description": "Enter max game windows to run at the same time.",
            "title": "Enter parallel window count",
            "minimum": 1,
        },
        {
            "type": "execute",
            "key": "execute",
            "label": "Execute",
            "description": "Run Pacman now with the selected configuration.",
        },
        {
            "type": "quit",
            "key": "quit",
            "label": "Quit",
            "description": "Exit launcher without running.",
        },
    ]

    idx = 0
    while True:
        for item in menu_items:
            if item["type"] == "choice":
                item["label"] = f"{item['key'].capitalize()}: {state[item['key']]}"
            elif item["type"] == "number":
                item["label"] = f"{item['key'].capitalize()}: {state[item['key']]}"

        _render_main_menu(menu_items, idx, _load_team_banner(root))
        with _KeyReader() as reader:
            key = reader.read_key()

        if key == "UP":
            idx = (idx - 1) % len(menu_items)
            continue
        if key == "DOWN":
            idx = (idx + 1) % len(menu_items)
            continue
        if key == "QUIT":
            _clear_screen()
            raise SystemExit(1)

        activate = False
        if key in ("SPACE", "ENTER"):
            activate = True
        elif key.startswith("NUM:"):
            picked = int(key.split(":", 1)[1]) - 1
            if 0 <= picked < len(menu_items):
                idx = picked
                activate = True

        if not activate:
            continue

        selected = menu_items[idx]
        if selected["type"] == "quit":
            _clear_screen()
            raise SystemExit(1)
        if selected["type"] == "execute":
            _clear_screen()
            return (
                state["agent"],
                state["layout"],
                int(state["ghosts"]),
                int(state["games"]),
                int(state["parallel"]),
            )

        if selected["type"] == "choice":
            choice = choose_option(
                selected["title"],
                selected["description"],
                selected["options"],
                selected["options"].index(state[selected["key"]]),
            )
            if choice is not None:
                state[selected["key"]] = choice
        elif selected["type"] == "number":
            number_value = _prompt_number(
                selected["title"],
                selected["description"],
                int(state[selected["key"]]),
                selected.get("minimum", 1),
            )
            if number_value is not None:
                state[selected["key"]] = number_value


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


def _preview_pythonpath(app_root: Path) -> str:
    existing = os.environ.get("PYTHONPATH", "")
    app_path = str(app_root)
    return app_path if not existing else app_path + os.pathsep + existing


def _log_status(title: str, details: list[tuple[str, str]]) -> None:
    print(_paint(f"{BOLD}{title}{RESET}", CYAN))
    for label, value in details:
        print(f"  {_paint(label + ':', GREEN)} {value}")
    print()


def _next_available_path(directory: Path, stem: str, suffix: str) -> Path:
    candidate = directory / f"{stem}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = directory / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate


def _append_text(path: Path, lock: threading.Lock, content: str) -> None:
    with lock:
        with path.open("a", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()


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


def _format_command(cmd: list[str]) -> str:
    if hasattr(shlex, "join"):
        return shlex.join(cmd)
    return subprocess.list2cmdline(cmd)


def _status_details(
    *,
    root: Path,
    app_root: Path,
    selected_agent: str,
    selected_layout: str,
    selected_ghosts: int,
    selected_games: int,
    extra: list[str],
    provided_any: bool,
    python_bin: str,
    pythonpath: str,
    parallel: int,
) -> list[tuple[str, str]]:
    return [
        ("Launcher mode", "direct args" if provided_any else "interactive menu"),
        ("Repository root", str(root)),
        ("Application root", str(app_root)),
        ("Python", python_bin),
        ("Python version", sys.version.split()[0]),
        ("Platform", platform.platform()),
        ("Agent", selected_agent),
        ("Layout", selected_layout),
        ("Ghosts", str(selected_ghosts)),
        ("Games", str(selected_games)),
        ("Parallel", str(parallel)),
        ("Extra args", " ".join(extra) if extra else "<none>"),
        ("PYTHONPATH", pythonpath),
    ]


def _attempt_display(attempt_number: int, total_attempts: int) -> str:
    return f"Attempts {attempt_number}/{total_attempts} [{attempt_number}]"


def _window_title(attempt_number: int, total_attempts: int) -> str:
    return f"Pacman - Attempt {attempt_number}/{total_attempts}"


def _extract_attempt_metrics(stdout_text: str) -> dict[str, str]:
    metrics = {
        "score": "",
        "average_score": "",
        "result": "",
        "wins": "",
        "games_reported": "",
        "win_rate": "",
        "record": "",
    }

    final_score_match = re.search(
        r"Pacman (?:emerges victorious!|died!) Score:\s*(-?\d+(?:\.\d+)?)",
        stdout_text,
    )
    if final_score_match:
        metrics["score"] = final_score_match.group(1)
    else:
        score_matches = re.findall(r"(?m)^Score:\s*(-?\d+(?:\.\d+)?)\s*$", stdout_text)
        if score_matches:
            metrics["score"] = score_matches[-1]

    average_score_match = re.search(r"Average Score:\s*(-?\d+(?:\.\d+)?)", stdout_text)
    if average_score_match:
        metrics["average_score"] = average_score_match.group(1)
    elif metrics["score"]:
        metrics["average_score"] = metrics["score"]

    win_rate_match = re.search(r"Win Rate:\s*(\d+)/(\d+)\s+\(([^)]+)\)", stdout_text)
    if win_rate_match:
        metrics["wins"] = win_rate_match.group(1)
        metrics["games_reported"] = win_rate_match.group(2)
        metrics["win_rate"] = win_rate_match.group(3)

    record_match = re.search(r"Record:\s*(.+)", stdout_text)
    if record_match:
        metrics["record"] = record_match.group(1).strip()

    if "Pacman emerges victorious!" in stdout_text:
        metrics["result"] = "win"
    elif "Pacman died!" in stdout_text:
        metrics["result"] = "loss"

    return metrics


def _upsert_csv_row(
    csv_path: Path,
    csv_lock: threading.Lock,
    csv_rows: dict[int, dict[str, object]],
    attempt_number: int,
    row: dict[str, object],
) -> None:
    with csv_lock:
        merged_row = dict(csv_rows.get(attempt_number, {}))
        merged_row.update(row)
        csv_rows[attempt_number] = merged_row
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writeheader()
            for ordered_attempt in sorted(csv_rows):
                writer.writerow(
                    {
                        field: csv_rows[ordered_attempt].get(field, "")
                        for field in CSV_FIELDS
                    }
                )
            handle.flush()


def _write_stream_line(
    *,
    log_path: Path,
    log_lock: threading.Lock,
    console_lock: threading.Lock,
    attempt_display: str,
    stream_name: str,
    raw_line: str,
    is_error: bool,
) -> None:
    line = raw_line if raw_line.endswith("\n") else raw_line + "\n"
    prefixed_line = f"[{attempt_display}] {stream_name}: {line}"
    _append_text(log_path, log_lock, prefixed_line)
    with console_lock:
        target = sys.stderr if is_error else sys.stdout
        try:
            target.write(prefixed_line)
            target.flush()
        except OSError:
            pass


def _stream_process_output(
    *,
    pipe,
    stream_name: str,
    output_chunks: list[str],
    log_path: Path,
    log_lock: threading.Lock,
    console_lock: threading.Lock,
    attempt_display: str,
    is_error: bool,
) -> None:
    try:
        for raw_line in iter(pipe.readline, ""):
            if raw_line == "":
                break
            output_chunks.append(raw_line)
            _write_stream_line(
                log_path=log_path,
                log_lock=log_lock,
                console_lock=console_lock,
                attempt_display=attempt_display,
                stream_name=stream_name,
                raw_line=raw_line,
                is_error=is_error,
            )
    finally:
        pipe.close()


def _request_batch_stop(batch_artifacts: dict[str, object], reason: str) -> None:
    cancel_event: threading.Event = batch_artifacts["cancel_event"]
    if cancel_event.is_set():
        return

    cancel_event.set()
    message = f"Launcher stop requested: {reason}"
    _append_text(batch_artifacts["log_path"], batch_artifacts["log_lock"], message + "\n")

    with batch_artifacts["console_lock"]:
        print(_paint(message, YELLOW))

    with batch_artifacts["process_lock"]:
        active_processes = list(batch_artifacts["active_processes"].values())

    for process in active_processes:
        _stop_process(process)


def _watch_for_batch_quit(
    batch_artifacts: dict[str, object],
    listener_stop_event: threading.Event,
) -> None:
    cancel_event: threading.Event = batch_artifacts["cancel_event"]

    if os.name == "nt":
        import msvcrt  # type: ignore

        while not listener_stop_event.is_set() and not cancel_event.is_set():
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch and ch.lower() == "q":
                    _request_batch_stop(batch_artifacts, "q pressed in launcher terminal")
                    return
            time.sleep(0.05)
        return

    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while not listener_stop_event.is_set() and not cancel_event.is_set():
            readable, _, _ = select.select([sys.stdin], [], [], 0.05)
            if not readable:
                continue
            ch = sys.stdin.read(1)
            if ch and ch.lower() == "q":
                _request_batch_stop(batch_artifacts, "q pressed in launcher terminal")
                return
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _create_batch_artifacts(
    *,
    root: Path,
    app_root: Path,
    python_bin: str,
    selected_agent: str,
    selected_layout: str,
    selected_ghosts: int,
    total_games: int,
    parallel: int,
    extra: list[str],
    provided_any: bool,
) -> dict[str, object]:
    log_dir = root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    session_started_at = datetime.now()
    session_stamp = session_started_at.strftime("%Y%m%d-%H%M%S-%f")
    session_stem = f"pacman-run-{session_stamp}"
    log_path = _next_available_path(log_dir, session_stem, ".log")
    csv_path = _next_available_path(log_dir, session_stem, ".csv")
    pythonpath = _preview_pythonpath(app_root)

    status_details = _status_details(
        root=root,
        app_root=app_root,
        selected_agent=selected_agent,
        selected_layout=selected_layout,
        selected_ghosts=selected_ghosts,
        selected_games=total_games,
        extra=extra,
        provided_any=provided_any,
        python_bin=python_bin,
        pythonpath=pythonpath,
        parallel=parallel,
    )

    log_header = "\n".join(
        [
            "Pacman Launcher Session Log",
            f"Session started: {session_started_at.isoformat(timespec='seconds')}",
            f"CSV file: {csv_path}",
            "",
            "== Launcher Status ==",
            *[f"{label}: {value}" for label, value in status_details],
            "",
        ]
    )
    log_path.write_text(log_header, encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        handle.flush()

    return {
        "log_path": log_path,
        "csv_path": csv_path,
        "log_lock": threading.Lock(),
        "csv_lock": threading.Lock(),
        "console_lock": threading.Lock(),
        "process_lock": threading.Lock(),
        "active_processes": {},
        "cancel_event": threading.Event(),
        "csv_rows": {},
    }


def _run_game_attempt(
    *,
    attempt_number: int,
    total_attempts: int,
    root: Path,
    app_root: Path,
    python_bin: str,
    selected_agent: str,
    selected_layout: str,
    selected_ghosts: int,
    extra: list[str],
    provided_any: bool,
    parallel: int,
    batch_artifacts: dict[str, object],
) -> dict[str, object]:
    cmd, env = _build_command(
        python_bin,
        app_root,
        agent=selected_agent,
        layout=selected_layout,
        ghosts=selected_ghosts,
        num_games=1,
        extra=extra,
    )
    env["PYTHONUNBUFFERED"] = "1"

    attempt_display = _attempt_display(attempt_number, total_attempts)
    window_title = _window_title(attempt_number, total_attempts)
    env["PACMAN_WINDOW_TITLE"] = window_title

    pythonpath = env.get("PYTHONPATH", "<unset>")
    status_details = _status_details(
        root=root,
        app_root=app_root,
        selected_agent=selected_agent,
        selected_layout=selected_layout,
        selected_ghosts=selected_ghosts,
        selected_games=total_attempts,
        extra=extra,
        provided_any=provided_any,
        python_bin=python_bin,
        pythonpath=pythonpath,
        parallel=parallel,
    )

    log_path = batch_artifacts["log_path"]
    csv_path = batch_artifacts["csv_path"]
    log_lock = batch_artifacts["log_lock"]
    csv_lock = batch_artifacts["csv_lock"]
    csv_rows = batch_artifacts["csv_rows"]
    console_lock = batch_artifacts["console_lock"]
    process_lock = batch_artifacts["process_lock"]
    active_processes = batch_artifacts["active_processes"]
    cancel_event: threading.Event = batch_artifacts["cancel_event"]

    started_at = datetime.now()
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []
    return_code = 1
    process = None

    if cancel_event.is_set():
        finished_at = started_at
        status_label = "interrupted (launcher stop)"
        _upsert_csv_row(
            csv_path,
            csv_lock,
            csv_rows,
            attempt_number,
            {
                "attempt_display": attempt_display,
                "attempt_number": attempt_number,
                "total_attempts": total_attempts,
                "window_title": window_title,
                "status": status_label,
                "return_code": 130,
                "started_at": started_at.isoformat(timespec="seconds"),
                "finished_at": finished_at.isoformat(timespec="seconds"),
                "duration_seconds": "0.000",
                "agent": selected_agent,
                "layout": selected_layout,
                "ghosts": selected_ghosts,
                "parallel": parallel,
            },
        )
        return {
            "attempt_display": attempt_display,
            "attempt_number": attempt_number,
            "total_attempts": total_attempts,
            "status_label": status_label,
            "return_code": 130,
            "log_path": log_path,
            "csv_path": csv_path,
            "stdout": "",
            "stderr": "",
            "started_at": started_at,
            "finished_at": finished_at,
            "interrupted": True,
            "window_title": window_title,
        }

    _append_text(
        log_path,
        log_lock,
        "\n".join(
            [
                f"== Attempt Started: {attempt_display} ==",
                f"Started: {started_at.isoformat(timespec='seconds')}",
                f"Window title: {window_title}",
                f"Command: {_format_command(cmd)}",
                *[f"{label}: {value}" for label, value in status_details],
                "",
            ]
        ),
    )

    with console_lock:
        _log_status(
            "Attempt Started",
            [
                ("Attempt", attempt_display),
                ("Window title", window_title),
                ("Session log", str(log_path)),
                ("Session csv", str(csv_path)),
            ],
        )

    _upsert_csv_row(
        csv_path,
        csv_lock,
        csv_rows,
        attempt_number,
        {
            "attempt_display": attempt_display,
            "attempt_number": attempt_number,
            "total_attempts": total_attempts,
            "window_title": window_title,
            "status": "running",
            "started_at": started_at.isoformat(timespec="seconds"),
            "agent": selected_agent,
            "layout": selected_layout,
            "ghosts": selected_ghosts,
            "parallel": parallel,
        },
    )

    try:
        process = subprocess.Popen(
            cmd,
            cwd=str(root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            errors="replace",
        )
        with process_lock:
            active_processes[attempt_number] = process

        stdout_thread = threading.Thread(
            target=_stream_process_output,
            kwargs={
                "pipe": process.stdout,
                "stream_name": "stdout",
                "output_chunks": stdout_chunks,
                "log_path": log_path,
                "log_lock": log_lock,
                "console_lock": console_lock,
                "attempt_display": attempt_display,
                "is_error": False,
            },
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=_stream_process_output,
            kwargs={
                "pipe": process.stderr,
                "stream_name": "stderr",
                "output_chunks": stderr_chunks,
                "log_path": log_path,
                "log_lock": log_lock,
                "console_lock": console_lock,
                "attempt_display": attempt_display,
                "is_error": True,
            },
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()
        return_code = process.wait()
        stdout_thread.join()
        stderr_thread.join()
    except Exception as exc:
        stderr_chunks.append(f"{type(exc).__name__}: {exc}\n")
        stderr_chunks.append(traceback.format_exc())
        if process is not None and process.poll() is None:
            process.kill()
    finally:
        if process is not None:
            with process_lock:
                active_processes.pop(attempt_number, None)

    finished_at = datetime.now()
    stdout_text = "".join(stdout_chunks)
    stderr_text = "".join(stderr_chunks)
    interrupted = return_code == 130
    launcher_stopped = cancel_event.is_set()
    if launcher_stopped and return_code != 0:
        interrupted = True
        status_label = "interrupted (launcher stop)"
    else:
        status_label = (
            "interrupted (window closed)"
            if interrupted
            else "completed"
            if return_code == 0
            else "failed"
        )
    metrics = _extract_attempt_metrics(stdout_text)
    duration_seconds = (finished_at - started_at).total_seconds()

    _append_text(
        log_path,
        log_lock,
        "\n".join(
            [
                f"== Attempt Finished: {attempt_display} ==",
                f"Status: {status_label}",
                f"Return code: {return_code}",
                f"Finished: {finished_at.isoformat(timespec='seconds')}",
                f"Duration seconds: {duration_seconds:.3f}",
                f"Score: {metrics['score'] or '<unknown>'}",
                f"Result: {metrics['result'] or '<unknown>'}",
                "",
            ]
        ),
    )

    _upsert_csv_row(
        csv_path,
        csv_lock,
        csv_rows,
        attempt_number,
        {
            "attempt_display": attempt_display,
            "attempt_number": attempt_number,
            "total_attempts": total_attempts,
            "window_title": window_title,
            "status": status_label,
            "return_code": return_code,
            "started_at": started_at.isoformat(timespec="seconds"),
            "finished_at": finished_at.isoformat(timespec="seconds"),
            "duration_seconds": f"{duration_seconds:.3f}",
            "agent": selected_agent,
            "layout": selected_layout,
            "ghosts": selected_ghosts,
            "parallel": parallel,
            **metrics,
        },
    )

    return {
        "attempt_display": attempt_display,
        "attempt_number": attempt_number,
        "total_attempts": total_attempts,
        "status_label": status_label,
        "return_code": return_code,
        "log_path": log_path,
        "csv_path": csv_path,
        "stdout": stdout_text,
        "stderr": stderr_text,
        "started_at": started_at,
        "finished_at": finished_at,
        "interrupted": interrupted,
        "window_title": window_title,
    }


def _report_attempt_result(
    attempt_result: dict[str, object],
    console_lock: threading.Lock,
) -> None:
    log_path = attempt_result["log_path"]
    csv_path = attempt_result["csv_path"]
    status_label = attempt_result["status_label"]
    return_code = attempt_result["return_code"]
    attempt_display = attempt_result["attempt_display"]

    with console_lock:
        _log_status(
            "Attempt Finished",
            [
                ("Attempt", str(attempt_display)),
                ("Status", str(status_label)),
                ("Exit code", str(return_code)),
                ("Session log", str(log_path)),
                ("Session csv", str(csv_path)),
            ],
        )


def _run_game_batch(
    *,
    root: Path,
    app_root: Path,
    python_bin: str,
    selected_agent: str,
    selected_layout: str,
    selected_ghosts: int,
    total_games: int,
    parallel: int,
    extra: list[str],
    provided_any: bool,
    wait_for_q_to_return: bool,
) -> int:
    total_attempts = max(1, total_games)
    worker_count = max(1, parallel)
    overall_exit_code = 0
    batch_artifacts = _create_batch_artifacts(
        root=root,
        app_root=app_root,
        python_bin=python_bin,
        selected_agent=selected_agent,
        selected_layout=selected_layout,
        selected_ghosts=selected_ghosts,
        total_games=total_attempts,
        parallel=worker_count,
        extra=extra,
        provided_any=provided_any,
    )

    _log_status(
        "Batch Artifacts",
        [
            ("Session log", str(batch_artifacts["log_path"])),
            ("Session csv", str(batch_artifacts["csv_path"])),
        ],
    )
    print(_paint("While running: press q in this terminal to interrupt all attempts.", YELLOW))

    listener_stop_event = threading.Event()
    listener_thread = None
    if sys.stdin.isatty():
        listener_thread = threading.Thread(
            target=_watch_for_batch_quit,
            args=(batch_artifacts, listener_stop_event),
            daemon=True,
        )
        listener_thread.start()

    try:
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            futures = [
                executor.submit(
                    _run_game_attempt,
                    attempt_number=attempt_number,
                    total_attempts=total_attempts,
                    root=root,
                    app_root=app_root,
                    python_bin=python_bin,
                    selected_agent=selected_agent,
                    selected_layout=selected_layout,
                    selected_ghosts=selected_ghosts,
                    extra=extra,
                    provided_any=provided_any,
                    parallel=worker_count,
                    batch_artifacts=batch_artifacts,
                )
                for attempt_number in range(1, total_attempts + 1)
            ]

            for future in as_completed(futures):
                attempt_result = future.result()
                if int(attempt_result["return_code"]) not in (0, 130):
                    overall_exit_code = 1
                _report_attempt_result(attempt_result, batch_artifacts["console_lock"])
    finally:
        listener_stop_event.set()
        if listener_thread is not None:
            listener_thread.join(timeout=0.2)

    was_interrupted = batch_artifacts["cancel_event"].is_set()
    _log_status(
        "Batch Finished",
        [
            ("Total attempts", str(total_attempts)),
            ("Parallel", str(worker_count)),
            ("Session log", str(batch_artifacts["log_path"])),
            ("Session csv", str(batch_artifacts["csv_path"])),
            ("Batch status", "interrupted by launcher" if was_interrupted else "completed"),
        ],
    )

    if wait_for_q_to_return:
        print(_paint("Press q to return to the main menu.", YELLOW))
        with _KeyReader() as reader:
            while True:
                if reader.read_key() == "QUIT":
                    break

    return overall_exit_code


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive launcher for Pacman")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--agent")
    parser.add_argument("--layout")
    parser.add_argument("--ghosts", type=int)
    parser.add_argument("--num-games", type=int)
    parser.add_argument("--parallel", type=int)
    parser.add_argument("--", dest="dashdash", nargs="*")
    args, extra = parser.parse_known_args()

    root = Path(__file__).resolve().parents[1]
    app_root = root / "app"

    provided_any = any(
        v is not None for v in [args.agent, args.layout, args.ghosts, args.num_games, args.parallel]
    ) or bool(extra)
    parallel = args.parallel if args.parallel is not None else 1
    if parallel < 1:
        parallel = 1

    if provided_any:
        selected_agent = args.agent or "ReflexAgent"
        selected_layout = args.layout or "mediumClassic"
        selected_ghosts = args.ghosts if args.ghosts is not None else 2
        selected_games = args.num_games if args.num_games is not None else 1
        preview_pythonpath = _preview_pythonpath(app_root)
        _log_status(
            "Launcher Status",
            _status_details(
                root=root,
                app_root=app_root,
                selected_agent=selected_agent,
                selected_layout=selected_layout,
                selected_ghosts=selected_ghosts,
                selected_games=selected_games,
                extra=extra,
                provided_any=provided_any,
                python_bin=args.python_bin,
                pythonpath=preview_pythonpath,
                parallel=parallel,
            ),
        )
        print(_paint("Running now...", GREEN))
        return _run_game_batch(
            root=root,
            app_root=app_root,
            python_bin=args.python_bin,
            selected_agent=selected_agent,
            selected_layout=selected_layout,
            selected_ghosts=selected_ghosts,
            total_games=selected_games,
            parallel=parallel,
            extra=extra,
            provided_any=provided_any,
            wait_for_q_to_return=False,
        )

    while True:
        selected_agent, selected_layout, selected_ghosts, selected_games, selected_parallel = _run_interactive_setup(root, parallel)
        parallel = selected_parallel
        preview_pythonpath = _preview_pythonpath(app_root)
        _log_status(
            "Launcher Status",
            _status_details(
                root=root,
                app_root=app_root,
                selected_agent=selected_agent,
                selected_layout=selected_layout,
                selected_ghosts=selected_ghosts,
                selected_games=selected_games,
                extra=extra,
                provided_any=provided_any,
                python_bin=args.python_bin,
                pythonpath=preview_pythonpath,
                parallel=selected_parallel,
            ),
        )
        print(_paint("Running now...", GREEN))
        _run_game_batch(
            root=root,
            app_root=app_root,
            python_bin=args.python_bin,
            selected_agent=selected_agent,
            selected_layout=selected_layout,
            selected_ghosts=selected_ghosts,
            total_games=selected_games,
            parallel=selected_parallel,
            extra=extra,
            provided_any=provided_any,
            wait_for_q_to_return=True,
        )



if __name__ == "__main__":
    raise SystemExit(main())
