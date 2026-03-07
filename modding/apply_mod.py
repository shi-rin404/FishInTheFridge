import base64

from .modder import SkinModder

def apply_mod(original_to_mod:dict[str, str]) -> bool:
    with SkinModder(base64.decodebytes(b"ZHdyZy5leGU=").decode()) as modder:
        modder.scan(list(original_to_mod.keys()))
        modder.patch_many(original_to_mod)

    return True