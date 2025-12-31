#!/usr/bin/env python3
"""
Build script for Blender add-ons in this repository.

When run from the project root, it will:
- Find every immediate subdirectory that contains a README.md file.
- Create a ZIP archive for each such directory in the build/ folder.
- Preserve the top-level directory inside the ZIP (required by Blender). 
- Exclude common junk (build/, __pycache__/, *.pyc, .git, .idea, etc.).

Usage:
  python build_addons.py

Zip output:
  build/<addon_name>.zip

Tested on Windows, uses only Python standard library.
"""
from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


EXCLUDE_DIR_NAMES = {
    'build',
    '.git',
    '.idea',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
}

EXCLUDE_FILE_SUFFIXES = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib',
}

EXCLUDE_FILE_NAMES = {
    '.DS_Store',
    'Thumbs.db',
}


def has_readme_case_insensitive(directory: Path) -> bool:
    # Windows is case-insensitive, but to be robust across platforms, check case-insensitively
    for child in directory.iterdir():
        if child.is_file() and child.name.lower() == 'readme.md':
            return True
    return False


def find_targets(root: Path) -> list[Path]:
    targets: list[Path] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        if child.name in EXCLUDE_DIR_NAMES:
            continue
        if child.name.startswith('.'):
            continue
        if has_readme_case_insensitive(child):
            targets.append(child)
    return targets


def should_exclude(path: Path) -> bool:
    # Exclude if any parent directory is in the excluded names
    for part in path.parts:
        if part in EXCLUDE_DIR_NAMES:
            return True
    name = path.name
    if name in EXCLUDE_FILE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDE_FILE_SUFFIXES:
        return True
    return False


def zip_directory(src_dir: Path, out_zip: Path) -> None:
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(out_zip, 'w', ZIP_DEFLATED) as zf:
        for file in src_dir.rglob('*'):
            if file.is_dir():
                continue
            if should_exclude(file):
                continue
            # Preserve the top-level directory name inside the archive
            rel = file.relative_to(src_dir)
            arcname = f"{src_dir.name}/{rel.as_posix()}"
            zf.write(file, arcname)


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent
    print(f"Building addons from: {root}")

    targets = find_targets(root)
    if not targets:
        print("No addon directories with README.md found. Nothing to do.")
        return 0

    build_dir = root / 'build'
    build_dir.mkdir(exist_ok=True)

    built = 0
    for target in targets:
        zip_path = build_dir / f"{target.name}.zip"
        print(f"- Zipping '{target.name}' -> {zip_path}")
        try:
            zip_directory(target, zip_path)
            # Warn if no __init__.py at addon root (Blender requires it)
            if not (target / '__init__.py').exists():
                print(f"  [warn] {target.name} has no __init__.py at top-level. Blender may not recognize it as an addon.")
            built += 1
        except Exception as e:
            print(f"  [error] Failed to build {target.name}: {e}")

    print(f"Done. Built {built} addon(s). Output: {build_dir}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
