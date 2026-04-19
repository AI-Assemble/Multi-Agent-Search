import csv
import os
import platform
import subprocess
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from .colors import BOLD, CYAN, GREEN, MAGENTA, RESET, YELLOW, _paint
from .fs import _next_available_path, _preview_pythonpath
from .keys import _KeyReader, _clear_screen
from .metrics import CSV_FIELDS, _extract_attempt_metrics, _upsert_csv_row
from .process import _append_text, _build_command, _format_command, _stop_process


def _log_status(title: str, details: list[tuple[str, str]]) -> None:
    print(_paint(f"{BOLD}{title}{RESET}", CYAN))
    for label, value in details:
        print(f"  {_paint(label + ':', GREEN)} {value}")
    print()


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


def _create_attempt_state(attempt_number: int, total_attempts: int) -> dict[str, object]:
    return {
        "attempt_display": _attempt_display(attempt_number, total_attempts),
        "window_title": _window_title(attempt_number, total_attempts),
        "status": "pending",
        "stdout_lines": 0,
        "stderr_lines": 0,
        "started_at": "",
        "finished_at": "",
        "duration_seconds": "",
        "score": "",
        "result": "",
        "return_code": "",
    }


def _set_batch_message(batch_artifacts: dict[str, object], message: str) -> None:
    with batch_artifacts["state_lock"]:
        batch_artifacts["message"] = message


def _update_attempt_state(
    batch_artifacts: dict[str, object],
    attempt_number: int,
    **updates: object,
) -> None:
    with batch_artifacts["state_lock"]:
        attempt_state = batch_artifacts["attempt_states"].setdefault(
            attempt_number,
            _create_attempt_state(attempt_number, int(batch_artifacts["total_attempts"])),
        )
        attempt_state.update(updates)


def _refresh_batch_console(batch_artifacts: dict[str, object]) -> None:
    if not batch_artifacts["dashboard_enabled"]:
        return

    with batch_artifacts["state_lock"]:
        phase = str(batch_artifacts["phase"])
        message = str(batch_artifacts["message"])
        total_attempts = int(batch_artifacts["total_attempts"])
        worker_count = int(batch_artifacts["worker_count"])
        selected_agent = str(batch_artifacts["selected_agent"])
        selected_layout = str(batch_artifacts["selected_layout"])
        selected_ghosts = int(batch_artifacts["selected_ghosts"])
        log_path = str(batch_artifacts["log_path"])
        csv_path = str(batch_artifacts["csv_path"])
        attempt_states = {
            attempt_number: dict(state)
            for attempt_number, state in batch_artifacts["attempt_states"].items()
        }

    counts = {"pending": 0, "running": 0, "completed": 0, "failed": 0, "interrupted": 0}
    for state in attempt_states.values():
        status = str(state.get("status", "pending"))
        if status == "pending":
            counts["pending"] += 1
        elif status == "running":
            counts["running"] += 1
        elif status == "completed":
            counts["completed"] += 1
        elif status.startswith("interrupted"):
            counts["interrupted"] += 1
        else:
            counts["failed"] += 1

    title = "Pacman Launcher - Batch Finished" if phase == "finished" else "Pacman Launcher - Batch Running"
    instruction = (
        "Press q to return to the main menu."
        if phase == "finished" and batch_artifacts["wait_for_q_to_return"]
        else "Press q in this terminal to interrupt all attempts."
        if phase == "running"
        else "Batch finished."
    )

    with batch_artifacts["console_lock"]:
        _clear_screen()
        print(_paint(f"{BOLD}{title}{RESET}", CYAN))
        print(_paint(instruction, YELLOW))
        print()
        print(f"{_paint('Agent:', GREEN)} {selected_agent}")
        print(f"{_paint('Layout:', GREEN)} {selected_layout}")
        print(f"{_paint('Ghosts:', GREEN)} {selected_ghosts}")
        print(f"{_paint('Attempts:', GREEN)} {total_attempts}")
        print(f"{_paint('Parallel:', GREEN)} {worker_count}")
        print(f"{_paint('Session log:', GREEN)} {log_path}")
        print(f"{_paint('Session csv:', GREEN)} {csv_path}")
        print()
        print(
            f"{_paint('Summary:', GREEN)} "
            f"pending={counts['pending']} | running={counts['running']} | "
            f"completed={counts['completed']} | failed={counts['failed']} | interrupted={counts['interrupted']}"
        )
        print(f"{_paint('Message:', GREEN)} {message}")
        print()

        for attempt_number in range(1, total_attempts + 1):
            state = attempt_states.get(attempt_number, _create_attempt_state(attempt_number, total_attempts))
            line = (
                f"[{attempt_number}] {state['status']} | "
                f"stdout={state.get('stdout_lines', 0)} | stderr={state.get('stderr_lines', 0)}"
            )
            if state.get("return_code") not in ("", None):
                line += f" | exit={state['return_code']}"
            if state.get("score"):
                line += f" | score={state['score']}"
            if state.get("result"):
                line += f" | result={state['result']}"
            print(line)


def _write_stream_line(
    *,
    log_path: Path,
    log_lock: threading.Lock,
    attempt_display: str,
    stream_name: str,
    raw_line: str,
    batch_artifacts: dict[str, object],
    attempt_number: int,
) -> None:
    line = raw_line if raw_line.endswith("\n") else raw_line + "\n"
    prefixed_line = f"[{attempt_display}] {stream_name}: {line}"
    _append_text(log_path, log_lock, prefixed_line)
    counter_name = "stderr_lines" if stream_name == "stderr" else "stdout_lines"
    with batch_artifacts["state_lock"]:
        attempt_state = batch_artifacts["attempt_states"].setdefault(
            attempt_number,
            _create_attempt_state(attempt_number, int(batch_artifacts["total_attempts"])),
        )
        attempt_state[counter_name] = int(attempt_state.get(counter_name, 0)) + 1


def _stream_process_output(
    *,
    pipe,
    stream_name: str,
    output_chunks: list[str],
    log_path: Path,
    log_lock: threading.Lock,
    attempt_display: str,
    batch_artifacts: dict[str, object],
    attempt_number: int,
) -> None:
    try:
        for raw_line in iter(pipe.readline, ""):
            if raw_line == "":
                break
            output_chunks.append(raw_line)
            _write_stream_line(
                log_path=log_path,
                log_lock=log_lock,
                attempt_display=attempt_display,
                stream_name=stream_name,
                raw_line=raw_line,
                batch_artifacts=batch_artifacts,
                attempt_number=attempt_number,
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
    _set_batch_message(batch_artifacts, message)
    _refresh_batch_console(batch_artifacts)

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


def _run_batch_renderer(
    batch_artifacts: dict[str, object],
    renderer_stop_event: threading.Event,
) -> None:
    while not renderer_stop_event.is_set():
        _refresh_batch_console(batch_artifacts)
        renderer_stop_event.wait(0.25)


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
        "state_lock": threading.Lock(),
        "process_lock": threading.Lock(),
        "active_processes": {},
        "cancel_event": threading.Event(),
        "csv_rows": {},
        "attempt_states": {},
        "message": "Preparing batch...",
        "phase": "running",
        "dashboard_enabled": sys.stdout.isatty(),
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
        _update_attempt_state(
            batch_artifacts,
            attempt_number,
            status=status_label,
            return_code=130,
            started_at=started_at.isoformat(timespec="seconds"),
            finished_at=finished_at.isoformat(timespec="seconds"),
            duration_seconds="0.000",
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
    _update_attempt_state(
        batch_artifacts,
        attempt_number,
        status="running",
        started_at=started_at.isoformat(timespec="seconds"),
        window_title=window_title,
    )
    _set_batch_message(batch_artifacts, f"{attempt_display} started")
    _refresh_batch_console(batch_artifacts)

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
                "attempt_display": attempt_display,
                "batch_artifacts": batch_artifacts,
                "attempt_number": attempt_number,
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
                "attempt_display": attempt_display,
                "batch_artifacts": batch_artifacts,
                "attempt_number": attempt_number,
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
    _update_attempt_state(
        batch_artifacts,
        attempt_number,
        status=status_label,
        return_code=return_code,
        finished_at=finished_at.isoformat(timespec="seconds"),
        duration_seconds=f"{duration_seconds:.3f}",
        score=metrics["score"],
        result=metrics["result"],
    )
    _set_batch_message(batch_artifacts, f"{attempt_display} finished with status: {status_label}")
    _refresh_batch_console(batch_artifacts)

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
    batch_artifacts: dict[str, object],
) -> None:
    status_label = attempt_result["status_label"]
    attempt_display = attempt_result["attempt_display"]
    _set_batch_message(batch_artifacts, f"{attempt_display} recorded as {status_label}")
    _refresh_batch_console(batch_artifacts)


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
    batch_artifacts["total_attempts"] = total_attempts
    batch_artifacts["worker_count"] = worker_count
    batch_artifacts["selected_agent"] = selected_agent
    batch_artifacts["selected_layout"] = selected_layout
    batch_artifacts["selected_ghosts"] = selected_ghosts
    batch_artifacts["wait_for_q_to_return"] = wait_for_q_to_return
    batch_artifacts["attempt_states"] = {
        attempt_number: _create_attempt_state(attempt_number, total_attempts)
        for attempt_number in range(1, total_attempts + 1)
    }
    _set_batch_message(batch_artifacts, "Batch started")
    _refresh_batch_console(batch_artifacts)

    listener_stop_event = threading.Event()
    listener_thread = None
    renderer_stop_event = threading.Event()
    renderer_thread = None
    if batch_artifacts["dashboard_enabled"]:
        renderer_thread = threading.Thread(
            target=_run_batch_renderer,
            args=(batch_artifacts, renderer_stop_event),
            daemon=True,
        )
        renderer_thread.start()
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
                _report_attempt_result(attempt_result, batch_artifacts)
    finally:
        listener_stop_event.set()
        if listener_thread is not None:
            listener_thread.join(timeout=0.2)
        renderer_stop_event.set()
        if renderer_thread is not None:
            renderer_thread.join(timeout=0.3)

    was_interrupted = batch_artifacts["cancel_event"].is_set()
    batch_artifacts["phase"] = "finished"
    _set_batch_message(
        batch_artifacts,
        "Batch interrupted by launcher" if was_interrupted else "Batch completed",
    )
    _refresh_batch_console(batch_artifacts)

    if wait_for_q_to_return:
        with _KeyReader() as reader:
            while True:
                if reader.read_key() == "QUIT":
                    break

    return overall_exit_code
