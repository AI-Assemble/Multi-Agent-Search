from __future__ import annotations

import importlib
import runpy
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import Iterable

ROOT = Path(__file__).resolve().parent
CORE_DIR = ROOT / "src" / "core"
TESTS_DIR = ROOT / "tests"


def _ensure_paths(paths: Iterable[Path]) -> None:
    for path in reversed([Path(p).resolve() for p in paths]):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def import_module(import_name: str, extra_paths: Iterable[Path] = ()) -> ModuleType:
    _ensure_paths([ROOT, *extra_paths])
    return importlib.import_module(import_name)


def load_module(module_name: str, path: Path, extra_paths: Iterable[Path] = ()) -> ModuleType:
    _ensure_paths([ROOT, *extra_paths])
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {path}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _export(globals_dict: dict, module: ModuleType) -> ModuleType:
    public_names = getattr(module, "__all__", None)
    if public_names is None:
        public_names = [name for name in module.__dict__ if not name.startswith("_")]

    for name in public_names:
        globals_dict[name] = getattr(module, name)

    globals_dict["_TARGET_MODULE"] = module
    return module


def export_import(globals_dict: dict, import_name: str, extra_paths: Iterable[Path] = ()) -> ModuleType:
    return _export(globals_dict, import_module(import_name, extra_paths))


def export_module(globals_dict: dict, module_name: str, path: Path, extra_paths: Iterable[Path] = ()) -> ModuleType:
    return _export(globals_dict, load_module(module_name, path, extra_paths))


def run_script(path: Path, extra_paths: Iterable[Path] = (), argv: list[str] | None = None) -> None:
    _ensure_paths([ROOT, *extra_paths])
    old_argv = sys.argv[:]
    if argv is not None:
        sys.argv = argv
    try:
        runpy.run_path(str(path), run_name="__main__")
    finally:
        sys.argv = old_argv
