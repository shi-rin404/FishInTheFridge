"""
Release packager — builds a zip with sanitised user data, without touching any
source files on disk.

What it changes inside the zip only:
  - database/user/presets.json      → {}
  - database/modding/mod_list.json  → {}
  - database/user/memory.json       → game_executable set to null
  - modding/3dm/                    → excluded
  - modding/_3dm/                   → renamed to modding/3dm/ in the zip
"""

import json
import os
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_ZIP   = PROJECT_ROOT.parent / f"{PROJECT_ROOT.name}_release.zip"

SKIP_DIRS  = {"__pycache__", ".git", ".claude"}
SKIP_FILES = {Path(__file__).name}   # exclude this script itself

OVERRIDDEN_POSIX_PATHS = {
    "database/user/presets.json",
    "database/modding/mod_list.json",
    "database/user/memory.json",
}


def _build_overrides() -> dict[str, bytes]:
    overrides: dict[str, bytes] = {}

    overrides["database/user/presets.json"]     = b"{}"
    overrides["database/modding/mod_list.json"]  = b"{}"

    memory_src = PROJECT_ROOT / "database" / "user" / "memory.json"
    with memory_src.open(encoding="utf-8") as f:
        memory = json.load(f)
    memory["game_executable"] = None
    overrides["database/user/memory.json"] = json.dumps(memory, indent=4, ensure_ascii=False).encode()

    return overrides


def _arc_name(rel_posix: str) -> str | None:
    """Return the archive path for a relative posix path, or None to skip."""
    if rel_posix.startswith("modding/3dm/") or rel_posix == "modding/3dm":
        return None
    if rel_posix.startswith("modding/_3dm/"):
        return "modding/3dm/" + rel_posix[len("modding/_3dm/"):]
    if rel_posix == "modding/_3dm":
        return "modding/3dm"
    return rel_posix


def main() -> None:
    overrides = _build_overrides()

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
            rel_dir  = Path(dirpath).relative_to(PROJECT_ROOT)
            rel_posix = rel_dir.as_posix()

            # Prune traversal: skip unwanted dirs and the real 3dm folder
            dirnames[:] = [
                d for d in dirnames
                if d not in SKIP_DIRS
                and not (rel_posix == "modding" and d == "3dm")
            ]

            # Explicitly add a directory entry so empty folders are preserved
            if rel_posix != ".":
                arc_dir = _arc_name(rel_posix)
                if arc_dir is not None:
                    zf.writestr(zipfile.ZipInfo(arc_dir + "/"), b"")

            for fname in filenames:
                if fname in SKIP_FILES:
                    continue

                file_path = Path(dirpath) / fname
                rel_file  = (rel_dir / fname).as_posix()

                arc = _arc_name(rel_file)
                if arc is None:
                    continue

                if rel_file in overrides:
                    zf.writestr(arc, overrides[rel_file])
                else:
                    zf.write(file_path, arc)

    print(f"Packed: {OUTPUT_ZIP}")


if __name__ == "__main__":
    main()
