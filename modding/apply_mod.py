import base64

from .modder import SkinModder as skin_modder


class AssetsNotLoadedError(RuntimeError):
    pass


def apply_mod(
    original_to_mod: dict[str, str],
    *,
    force: bool = False,
    sentinel_targets: list[str] | None = None,
) -> bool:
    with skin_modder(base64.decodebytes(b"ZHdyZy5leGU=").decode()) as modder:
        targets = list(dict.fromkeys([*original_to_mod.keys(), *(sentinel_targets or [])]))
        scan_results = modder.scan(targets, force=force)
        missing_sentinels = [
            target for target in (sentinel_targets or [])
            if not scan_results.get(target)
        ]
        if missing_sentinels:
            raise AssetsNotLoadedError("Required game assets have not loaded yet.")
        modder.patch_many(original_to_mod)
    return True
