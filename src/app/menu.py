from pathlib import Path

from .colors import BLUE, BOLD, CYAN, DIM, GREEN, INVERT, MAGENTA, RESET, YELLOW, _paint
from .fs import _available_layouts, _load_team_banner
from .keys import _KeyReader, _clear_screen


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
            if item["type"] in ("choice", "number"):
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
