#!/usr/bin/env python3
import argparse
import os
import platform
import subprocess
import sys
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


def _paint(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"


def _available_layouts(root: Path) -> list[str]:
    layouts_dir = root / "layouts"
    if not layouts_dir.exists():
        return ["mediumClassic"]
    names = [p.stem for p in layouts_dir.glob("*.lay")]
    return sorted(set(names)) or ["mediumClassic"]


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
            if ch == b"q":
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
        if c1 == "q":
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


def _render_main_menu(menu_items: list[dict[str, str]], selected_index: int) -> None:
    selected_item = menu_items[selected_index]
    _clear_screen()
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


def _run_interactive_setup(root: Path) -> tuple[str, str, int, int]:
    layout_options = _available_layouts(root)

    state = {
        "agent": "ReflexAgent",
        "layout": "mediumClassic" if "mediumClassic" in layout_options else layout_options[0],
        "ghosts": "2",
        "games": "1",
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
            "type": "choice",
            "key": "ghosts",
            "label": f"Ghosts: {state['ghosts']}",
            "description": "Choose how many ghost agents will spawn.",
            "title": "Choose number of ghosts",
            "options": ["1", "2", "3", "4"],
        },
        {
            "type": "choice",
            "key": "games",
            "label": f"Games: {state['games']}",
            "description": "Choose how many games to play in this run.",
            "title": "Choose number of games",
            "options": ["1", "3", "5", "10"],
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
    with _KeyReader() as reader:
        while True:
            for item in menu_items:
                if item["type"] == "choice":
                    item["label"] = f"{item['key'].capitalize()}: {state[item['key']]}"

            _render_main_menu(menu_items, idx)
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
                )

            choice = choose_option(
                selected["title"],
                selected["description"],
                selected["options"],
                selected["options"].index(state[selected["key"]]),
            )
            if choice is not None:
                state[selected["key"]] = choice


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
        ("Extra args", " ".join(extra) if extra else "<none>"),
        ("PYTHONPATH", os.environ.get("PYTHONPATH", "<unset>")),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive launcher for Pacman")
    parser.add_argument("--python-bin", default=sys.executable)
    parser.add_argument("--agent")
    parser.add_argument("--layout")
    parser.add_argument("--ghosts", type=int)
    parser.add_argument("--num-games", type=int)
    parser.add_argument("--", dest="dashdash", nargs="*")
    args, extra = parser.parse_known_args()

    root = Path(__file__).resolve().parents[1]
    app_root = root / "app"

    provided_any = any(
        v is not None for v in [args.agent, args.layout, args.ghosts, args.num_games]
    ) or bool(extra)

    if provided_any:
        selected_agent = args.agent or "ReflexAgent"
        selected_layout = args.layout or "mediumClassic"
        selected_ghosts = args.ghosts if args.ghosts is not None else 2
        selected_games = args.num_games if args.num_games is not None else 1
        cmd, env = _build_command(
            args.python_bin,
            app_root,
            agent=selected_agent,
            layout=selected_layout,
            ghosts=selected_ghosts,
            num_games=selected_games,
            extra=extra,
        )

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
            ),
        )
        print(_paint("Running now...", GREEN))
        result = subprocess.run(cmd, cwd=str(root), env=env, check=False)
        _log_status(
            "Run Finished",
            [
                ("Exit code", str(result.returncode)),
                ("Action", "Returned to caller after direct run"),
            ],
        )
        return result.returncode

    while True:
        selected_agent, selected_layout, selected_ghosts, selected_games = _run_interactive_setup(root)

        cmd, env = _build_command(
            args.python_bin,
            app_root,
            agent=selected_agent,
            layout=selected_layout,
            ghosts=selected_ghosts,
            num_games=selected_games,
            extra=extra,
        )

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
            ),
        )
        print(_paint("Running now...", GREEN))
        result = subprocess.run(cmd, cwd=str(root), env=env, check=False)
        _log_status(
            "Run Finished",
            [
                ("Exit code", str(result.returncode)),
                ("Action", "Returned to main menu"),
            ],
        )



if __name__ == "__main__":
    raise SystemExit(main())
