from _compat import CORE_DIR, export_import, run_script

_TARGET_IMPORT = "controller.pacman"
_TARGET_PATH = CORE_DIR / "controller/pacman.py"
export_import(globals(), _TARGET_IMPORT, extra_paths=[CORE_DIR])

if __name__ == "__main__":
    run_script(_TARGET_PATH, extra_paths=[CORE_DIR])
