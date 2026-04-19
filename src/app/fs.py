import os
from pathlib import Path


def _available_layouts(root: Path) -> list[str]:
    layouts_dir = root / "layouts"
    if not layouts_dir.exists():
        return ["mediumClassic"]
    names = [p.stem for p in layouts_dir.glob("*.lay")]
    return sorted(set(names)) or ["mediumClassic"]


def _load_team_banner(root: Path) -> list[str]:
    banner_path = root / "src" / "core" / "config" / "name.txt"
    if not banner_path.exists():
        return ["Assemble"]
    lines = banner_path.read_text(encoding="utf-8").splitlines()
    return lines or ["Assemble"]


def _next_available_path(directory: Path, stem: str, suffix: str) -> Path:
    candidate = directory / f"{stem}{suffix}"
    counter = 2
    while candidate.exists():
        candidate = directory / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate


def _preview_pythonpath(app_root: Path) -> str:
    existing = os.environ.get("PYTHONPATH", "")
    app_path = str(app_root)
    return app_path if not existing else app_path + os.pathsep + existing
