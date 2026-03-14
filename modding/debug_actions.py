import base64
import ctypes

from modding.modder import SkinModder, _k32, _pid_by_name, PROCESS_VM_READ, PROCESS_VM_WRITE, PROCESS_VM_OPERATION, PROCESS_QUERY_INFO

# addr → initial_value (the string that was searched for at scan time)
debug_cache: dict[int, str] = {}

_proc = lambda: base64.decodebytes(b"ZHdyZy5leGU=").decode()


def debug_scan(search_string: str, change_to: str, progress_cb=None) -> dict[int, str]:
    """Scan for search_string with force=True, patch all found addresses to change_to.
    Stores results in debug_cache. Returns {addr: initial_value}."""
    if len(change_to.encode("utf-8")) > len(search_string.encode("utf-8")):
        raise ValueError(
            f"New value '{change_to}' ({len(change_to)}) is longer than "
            f"search string '{search_string}' ({len(search_string)}). Cannot patch in-place."
        )

    with SkinModder(_proc()) as modder:
        result = modder.scan([search_string], force=True, progress_cb=progress_cb)
        addresses = list(result.get(search_string, []))

        if addresses:
            raw = change_to.encode("utf-8") + b"\x00"
            raw_len = len(raw)
            buf = (ctypes.c_char * raw_len)(*raw)
            written = ctypes.c_size_t(0)
            for addr in addresses:
                _k32.WriteProcessMemory(
                    modder._handle, ctypes.c_void_p(addr), buf, raw_len, ctypes.byref(written)
                )

    entries = {addr: search_string for addr in addresses}
    debug_cache.clear()
    debug_cache.update(entries)
    return entries


def debug_retrieve(addrs: list[int], check_length: bool) -> tuple[list[int], list[int]]:
    """Write initial values back to addresses from debug_cache.
    check_length=True → skip addresses where the current in-memory length != initial length.
    Returns (restored_addrs, skipped_addrs)."""
    pid = _pid_by_name(_proc())
    access = PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFO
    handle = _k32.OpenProcess(access, False, pid)
    if not handle:
        raise PermissionError("Cannot open process. Run as administrator.")
    try:
        restored: list[int] = []
        skipped:  list[int] = []
        bytes_read = ctypes.c_size_t(0)

        for addr in addrs:
            initial = debug_cache.get(addr)
            if initial is None:
                continue

            if check_length:
                read_len = max(len(initial.encode("utf-8")) + 8, 64)
                read_buf = (ctypes.c_char * read_len)()
                ok_read = _k32.ReadProcessMemory(
                    handle, ctypes.c_void_p(addr), read_buf, read_len, ctypes.byref(bytes_read)
                )
                if ok_read and bytes_read.value > 0:
                    current = bytes(read_buf[:bytes_read.value]).decode("utf-8", errors="replace").split("\x00")[0]
                    if len(current) != len(initial):
                        skipped.append(addr)
                        continue

            raw = initial.encode("utf-8") + b"\x00"
            buf = (ctypes.c_char * len(raw))(*raw)
            written = ctypes.c_size_t(0)
            ok = _k32.WriteProcessMemory(handle, ctypes.c_void_p(addr), buf, len(raw), ctypes.byref(written))
            if ok and written.value == len(raw):
                restored.append(addr)
            else:
                skipped.append(addr)

        return restored, skipped
    finally:
        _k32.CloseHandle(handle)


def debug_edit(addrs: list[int], new_value: str, check_length: bool) -> tuple[list[int], list[int]]:
    """Patch addresses to new_value.
    check_length=True → skip addresses where len(new_value) != len(initial_value).
    Returns (patched_addrs, skipped_addrs)."""
    pid = _pid_by_name(_proc())
    handle = _k32.OpenProcess(PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFO, False, pid)
    if not handle:
        raise PermissionError("Cannot open process. Run as administrator.")
    try:
        patched: list[int] = []
        skipped: list[int] = []
        raw = new_value.encode("utf-8") + b"\x00"
        buf = (ctypes.c_char * len(raw))(*raw)
        written = ctypes.c_size_t(0)

        for addr in addrs:
            initial = debug_cache.get(addr, "")
            if check_length and len(new_value) != len(initial):
                skipped.append(addr)
                continue
            if len(new_value) > len(initial):
                skipped.append(addr)
                continue
            ok = _k32.WriteProcessMemory(handle, ctypes.c_void_p(addr), buf, len(raw), ctypes.byref(written))
            if ok and written.value == len(raw):
                patched.append(addr)
            else:
                skipped.append(addr)
        return patched, skipped
    finally:
        _k32.CloseHandle(handle)
