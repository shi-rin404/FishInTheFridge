import base64

from .modder import SkinModder as skin_modder

def apply_mod(original_to_mod: dict[str, str], *, force: bool = False) -> bool:
    with skin_modder(base64.decodebytes(b"ZHdyZy5leGU=").decode()) as modder:
        modder.scan(list(original_to_mod.keys()), force=force)
        modder.patch_many(original_to_mod)
    return True