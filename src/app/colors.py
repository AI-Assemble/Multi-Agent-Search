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
