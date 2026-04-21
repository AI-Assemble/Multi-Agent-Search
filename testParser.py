from _compat import CORE_DIR, TESTS_DIR, export_module, run_script

_TARGET_PATH = TESTS_DIR / 'testParser.py'
export_module(globals(), 'legacy_testParser', _TARGET_PATH, extra_paths=[TESTS_DIR, CORE_DIR])

if __name__ == '__main__':
    run_script(_TARGET_PATH, extra_paths=[TESTS_DIR, CORE_DIR])
