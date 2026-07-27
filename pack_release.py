"""
Release packager: builds a zip without local user data.

Runtime defaults are committed under defaults/ and copied into the live user
locations when missing.
"""

import os
import zipfile
import json
import argparse
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SYSTEM_VARIABLES = PROJECT_ROOT / "database" / "system" / "system_variables.json"

SKIP_DIRS = {"__pycache__", ".git", ".claude", "dist"}
SKIP_FILES = {Path(__file__).name, "3dm.zip"}
VERSION_RE = re.compile(r"^\d+(?:\.\d+)*$")


def _load_system_variables() -> dict:
    with SYSTEM_VARIABLES.open(encoding="utf-8") as f:
        return json.load(f)


def _write_system_variables(system_variables: dict) -> None:
    with SYSTEM_VARIABLES.open("w", encoding="utf-8") as f:
        json.dump(system_variables, f, indent=4)
        f.write("\n")


def _set_version(version: str) -> None:
    system_variables = _load_system_variables()
    system_variables["version"] = version
    _write_system_variables(system_variables)


def _output_zip_path(system_variables: dict) -> Path:
    version = str(system_variables["version"]).replace(".", "-")
    asset_prefix = system_variables.get("release_asset_prefix", "miyou-loader")
    dist_dir = PROJECT_ROOT / "dist"
    dist_dir.mkdir(exist_ok=True)
    return dist_dir / f"{asset_prefix}-{version}.zip"


def _arc_name(rel_posix: str) -> str | None:
    """Return the archive path for a relative posix path, or None to skip."""
    if rel_posix.startswith("modding/3dm/") or rel_posix == "modding/3dm":
        return None
    if rel_posix.startswith("database/user/") and rel_posix.endswith(".json"):
        return None
    if rel_posix.startswith("database/user/custom_bg_image."):
        return None
    if rel_posix == "database/modding/mod_list.json":
        return None
    return rel_posix


def _version_arg(value: str) -> str:
    if not VERSION_RE.fullmatch(value):
        raise argparse.ArgumentTypeError(
            "version must use dotted numbers, for example: 1.2.3"
        )
    return value


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Miyou Loader release zip.")
    parser.add_argument(
        "--version",
        type=_version_arg,
        help="Update database/system/system_variables.json before packaging.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.version:
        _set_version(args.version)

    output_zip = _output_zip_path(_load_system_variables())
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
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

    print(f"Packed: {output_zip}")


if __name__ == "__main__":
    main()
