import base64, string
from os import path

DEFAULT_GAME_EXECUTABLE:str = base64.decodebytes(b"TG9hZGluZyBCYXkgR2FtZXNcSWRlbnRpdHkgVlxkd3JnLmV4ZQ==").decode()

def find_game_executable() -> str | None:
    for letter in [_letter for _letter in string.ascii_uppercase if _letter.isalpha()]:
        if path.exists(f"{letter}:\\"):
            if path.exists(f"{letter}:\\{DEFAULT_GAME_EXECUTABLE}"):
                return f"{letter}:\\\\{DEFAULT_GAME_EXECUTABLE}"
    return None