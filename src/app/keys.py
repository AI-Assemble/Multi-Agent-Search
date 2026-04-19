import os
import sys


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
