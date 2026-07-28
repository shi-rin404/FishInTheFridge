import json
import re
from pathlib import Path, PurePosixPath

from core.variable_manager import program_variables
from modding import path_dictionary as pd


_MTG_REFERENCE_RE = re.compile(rb"chr[^\x00\r\n\"']+?\.mtg", re.IGNORECASE)


def load_character_keywords() -> list[tuple[str, str]]:
    try:
        with open(program_variables.character_list_path, encoding="utf-8") as f:
            character_keywords = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []
    return sorted(
        (
            (keyword.lower(), character)
            for keyword, character in character_keywords.items()
            if isinstance(keyword, str)
            and keyword
            and isinstance(character, str)
            and character
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )


def character_from_text(
    text: str,
    character_keywords: list[tuple[str, str]],
) -> str:
    text = text.lower()
    for keyword, character in character_keywords:
        if keyword in text:
            return character
    return pd.NO_CHARACTER_INFO


def character_from_skin_record(
    record: dict,
    character_keywords: list[tuple[str, str]],
) -> str:
    skin_path = record.get("skin")
    if not isinstance(skin_path, str):
        return pd.NO_CHARACTER_INFO
    return character_from_text(skin_path, character_keywords)


def character_from_mod_manifest(
    record: dict,
    manifest_path: str | Path,
    character_keywords: list[tuple[str, str]],
) -> str:
    character = record.get("character")
    if isinstance(character, str) and character.strip():
        return character.strip()
    return _character_from_mod_skin_fallback(
        record,
        Path(manifest_path),
        character_keywords,
    )


def _character_from_mod_skin_fallback(
    record: dict,
    manifest_path: Path,
    character_keywords: list[tuple[str, str]],
) -> str:
    skin_path = record.get("skin")
    if not isinstance(skin_path, str) or not skin_path:
        return pd.NO_CHARACTER_INFO

    mtg_path = _first_existing_mod_file(manifest_path, skin_path, ".mtg")
    if mtg_path is not None:
        return _character_from_file_text(mtg_path, character_keywords)

    gim_path = _first_existing_mod_file(manifest_path, skin_path, ".gim")
    if gim_path is None:
        return pd.NO_CHARACTER_INFO
    return _character_from_gim_mtg_reference(gim_path, character_keywords)


def _first_existing_mod_file(
    manifest_path: Path,
    skin_path: str,
    suffix: str,
) -> Path | None:
    for candidate in _mod_file_candidates(manifest_path, skin_path, suffix):
        if candidate.is_file():
            return candidate
    return None


def _mod_file_candidates(
    manifest_path: Path,
    skin_path: str,
    suffix: str,
) -> list[Path]:
    from database.user.user_variables import user_variables

    normalized = skin_path.replace("\\", "/")
    try:
        rel_path = PurePosixPath(normalized).with_suffix(suffix)
    except ValueError:
        return []

    mod_root = Path(user_variables.mod_dir)
    manifest_dir = manifest_path.parent
    candidates = [
        mod_root / Path(*rel_path.parts),
        mod_root.parent / Path(*rel_path.parts),
        manifest_dir / Path(*rel_path.parts),
        manifest_dir / rel_path.name,
    ]
    if rel_path.parts and rel_path.parts[0].lower() == "mod":
        stripped = Path(*rel_path.parts[1:])
        candidates.extend(
            [
                mod_root / stripped,
                manifest_dir / stripped,
            ]
        )

    unique_candidates = []
    seen = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            unique_candidates.append(candidate)
    return unique_candidates


def _character_from_file_text(
    path: Path,
    character_keywords: list[tuple[str, str]],
) -> str:
    try:
        text = path.read_bytes().decode("utf-8", errors="ignore")
    except OSError:
        return pd.NO_CHARACTER_INFO
    return character_from_text(text, character_keywords)


def _character_from_gim_mtg_reference(
    path: Path,
    character_keywords: list[tuple[str, str]],
) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return pd.NO_CHARACTER_INFO
    for match in _MTG_REFERENCE_RE.finditer(data):
        character = character_from_text(
            match.group(0).decode("utf-8", errors="ignore"),
            character_keywords,
        )
        if character != pd.NO_CHARACTER_INFO:
            return character
    return pd.NO_CHARACTER_INFO
