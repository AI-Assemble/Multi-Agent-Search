import sys

from _compat import CORE_DIR, TESTS_DIR, export_module, run_script

_TARGET_PATH = TESTS_DIR / "autograder.py"
export_module(globals(), "legacy_autograder", _TARGET_PATH, extra_paths=[TESTS_DIR, CORE_DIR])


def _with_default_code_root(argv: list[str]) -> list[str]:
    options_with_value = {"--code-directory", "--student-code", "--test-case-code", "--test-directory"}
    for index, arg in enumerate(argv):
        if arg == "--code-directory":
            return argv
        if any(arg.startswith(option + "=") for option in options_with_value):
            if arg.startswith("--code-directory="):
                return argv
    return ["--code-directory", str(CORE_DIR), *argv]


if __name__ == "__main__":
    run_script(
        _TARGET_PATH,
        extra_paths=[TESTS_DIR, CORE_DIR],
        argv=[sys.argv[0], *_with_default_code_root(sys.argv[1:])],
    )
