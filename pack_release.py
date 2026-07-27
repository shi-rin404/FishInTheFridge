"""
Release packager: builds a zip without local user data.

Runtime defaults are committed under defaults/ and copied into the live user
locations when missing.
"""

import os
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_ZIP = PROJECT_ROOT.parent / f"{PROJECT_ROOT.name}_release.zip"

SKIP_DIRS = {"__pycache__", ".git", ".claude"}
SKIP_FILES = {Path(__file__).name, "3dm.zip"}


def _arc_name(rel_posix: str) -> str | None:
    """Return the archive path for a relative posix path, or None to skip."""
    if rel_posix.startswith("modding/3dm/") or rel_posix == "modding/3dm":
        return None
    if rel_posix.startswith("database/user/") and rel_posix.endswith(".json"):
        return None
    if rel_posix == "database/modding/mod_list.json":
        return None
    return rel_posix


def main() -> None:
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for dirpath, dirnames, filenames in os.walk(PROJECT_ROOT):
            rel_dir = Path(dirpath).relative_to(PROJECT_ROOT)
            rel_posix = rel_dir.as_posix()

            dirnames[:] = [
                d for d in dirnames
                if d not in SKIP_DIRS
                and not (rel_posix == "modding" and d == "3dm")
            ]

            if rel_posix != ".":
                arc_dir = _arc_name(rel_posix)
                if arc_dir is not None:
                    zf.writestr(zipfile.ZipInfo(arc_dir + "/"), b"")

            for fname in filenames:
                if fname in SKIP_FILES:
                    continue

                file_path = Path(dirpath) / fname
                rel_file = (rel_dir / fname).as_posix()

                arc = _arc_name(rel_file)
                if arc is None:
                    continue

                zf.write(file_path, arc)

    print(f"Packed: {OUTPUT_ZIP}")


if __name__ == "__main__":
    main()
