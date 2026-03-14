"""
modder.py — Memory skin path patcher
Rewritten from scratch using raw ctypes + kernel32.

Architecture:
  - Single-pass VirtualQueryEx walk (no double-loop for progress counting)
  - Bulk ReadProcessMemory into reusable bytearray buffer (zero extra allocation per region)
  - All target strings scanned in one buffer pass per region
  - Address cache: full scan runs once, subsequent patches are direct writes
  - Process handle opened once, reused across all operations
"""

import ctypes
import ctypes.wintypes
import re
from ctypes import windll, byref, sizeof
from dataclasses import dataclass, field
from typing import Optional, Callable

# A live path must (optionally) start with '/' or '\' padding characters,
# then be rooted at 'chr' or 'mod', and end with '.gim'.
_LIVE_PATH_RE = re.compile(r'^[/\\]*(chr|mod)[/\\].+\.gim$', re.IGNORECASE)

# == INSTANCE =================
skin_modder = None

# ── Windows constants ──────────────────────────────────────────────────────────
PROCESS_VM_READ        = 0x0010
PROCESS_VM_WRITE       = 0x0020
PROCESS_VM_OPERATION   = 0x0008
PROCESS_QUERY_INFO     = 0x0400

MEM_COMMIT             = 0x1000
MEM_PRIVATE            = 0x20000   # heap / stack pages

# Readable, copy-on-write, readable+writable, read+write+execute variants
READABLE_PROTECTS      = {0x02, 0x04, 0x08, 0x20, 0x40, 0x80}

MAX_ADDRESS            = 0x7FFFFFFFFFFF  # user-mode ceiling on 64-bit Windows

# ── Structures ─────────────────────────────────────────────────────────────────
class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress",       ctypes.c_ulonglong),
        ("AllocationBase",    ctypes.c_ulonglong),
        ("AllocationProtect", ctypes.wintypes.DWORD),
        ("__alignment1",      ctypes.wintypes.DWORD),
        ("RegionSize",        ctypes.c_ulonglong),
        ("State",             ctypes.wintypes.DWORD),
        ("Protect",           ctypes.wintypes.DWORD),
        ("Type",              ctypes.wintypes.DWORD),
        ("__alignment2",      ctypes.wintypes.DWORD),
    ]

# ── Low-level kernel32 wrappers ────────────────────────────────────────────────
_k32 = windll.kernel32

_k32.OpenProcess.restype  = ctypes.wintypes.HANDLE
_k32.OpenProcess.argtypes = [ctypes.wintypes.DWORD, ctypes.wintypes.BOOL, ctypes.wintypes.DWORD]

_k32.CloseHandle.restype  = ctypes.wintypes.BOOL
_k32.CloseHandle.argtypes = [ctypes.wintypes.HANDLE]

_k32.ReadProcessMemory.restype  = ctypes.wintypes.BOOL
_k32.ReadProcessMemory.argtypes = [
    ctypes.wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]

_k32.WriteProcessMemory.restype  = ctypes.wintypes.BOOL
_k32.WriteProcessMemory.argtypes = [
    ctypes.wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]

_k32.VirtualQueryEx.restype  = ctypes.c_size_t
_k32.VirtualQueryEx.argtypes = [
    ctypes.wintypes.HANDLE,
    ctypes.c_void_p,
    ctypes.POINTER(MEMORY_BASIC_INFORMATION),
    ctypes.c_size_t,
]

_psapi = ctypes.WinDLL("psapi")

# EnumProcesses to resolve name → PID
_psapi.EnumProcesses.restype  = ctypes.wintypes.BOOL
_psapi.EnumProcesses.argtypes = [
    ctypes.POINTER(ctypes.wintypes.DWORD),
    ctypes.wintypes.DWORD,
    ctypes.POINTER(ctypes.wintypes.DWORD),
]

_psapi.GetProcessImageFileNameA.restype  = ctypes.wintypes.DWORD
_psapi.GetProcessImageFileNameA.argtypes = [
    ctypes.wintypes.HANDLE,
    ctypes.c_char_p,
    ctypes.wintypes.DWORD,
]


# ── Helper: resolve process name → PID ────────────────────────────────────────
def _pid_by_name(process_name: str) -> int:
    name_bytes = process_name.lower().encode()
    pids = (ctypes.wintypes.DWORD * 1024)()
    cb_needed = ctypes.wintypes.DWORD(0)
    _psapi.EnumProcesses(pids, sizeof(pids), byref(cb_needed))
    count = cb_needed.value // sizeof(ctypes.wintypes.DWORD)

    buf = ctypes.create_string_buffer(512)
    for i in range(count):
        pid = pids[i]
        h = _k32.OpenProcess(PROCESS_QUERY_INFO | PROCESS_VM_READ, False, pid)
        if not h:
            continue
        if _psapi.GetProcessImageFileNameA(h, buf, sizeof(buf)):
            exe = buf.value.split(b"\\")[-1].lower()
            if exe == name_bytes:
                _k32.CloseHandle(h)
                return pid
        _k32.CloseHandle(h)
    raise RuntimeError(f"Process '{process_name}' not found.")


# ── Core class ─────────────────────────────────────────────────────────────────
@dataclass
class SkinModder:
    """
    Attach once, scan once, patch many times.

    Usage:
        modder = SkinModder("game.exe")
        modder.scan(["skins/official/hero.png", "skins/official/map.png"])
        modder.patch("skins/official/hero.png", "skins/custom/hero.png")
        modder.close()

    Or use as a context manager:
        with SkinModder("game.exe") as modder:
            modder.scan([...])
            modder.patch(...)
    """

    process_name: str
    _handle: ctypes.wintypes.HANDLE = field(default=None, init=False, repr=False)
    _pid: int = field(default=0, init=False)
    # cache: original_string → list of absolute addresses
    _cache: dict[str, list[int]] = field(default_factory=dict, init=False)

    def __post_init__(self):
        global skin_modder
        # Carry forward the address cache so unmod/re-patch doesn't require a full re-scan
        if skin_modder is not None:
            self._cache.update(skin_modder._cache)
        skin_modder = self
        self._pid = _pid_by_name(self.process_name)
        access = PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFO
        self._handle = _k32.OpenProcess(access, False, self._pid)
        if not self._handle:
            raise PermissionError(f"Cannot open process PID={self._pid}. Run as administrator.")
        print(f"[modder] Attached to '{self.process_name}' PID={self._pid}")

    def close(self):
        if self._handle:
            _k32.CloseHandle(self._handle)
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    # ── Scan ──────────────────────────────────────────────────────────────────
    def scan(
        self,
        targets: list[str],
        *,
        force: bool = False,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> dict[str, list[int]]:
        """
        Scan process heap for all target strings.

        Args:
            targets:     List of original skin path strings to find.
            force:       Re-scan even if addresses are already cached.
            progress_cb: Optional callback(scanned_regions, total_regions).
                         For Tkinter: pass a lambda that updates a progressbar.

        Returns:
            Dict mapping each target string to a list of found addresses.
        """
        # Filter out already-cached targets unless force=True
        to_scan = targets if force else [t for t in targets if t not in self._cache]
        if not to_scan:
            print("[modder] All targets already cached, skipping scan.")
            return {t: self._cache[t] for t in targets}

        # Pre-encode targets as null-terminated UTF-8 bytes
        encoded: dict[str, bytes] = {s: s.encode("utf-8") + b"\x00" for s in to_scan}
        found: dict[str, list[int]] = {s: [] for s in to_scan}

        # ── Single-pass region walk ───────────────────────────────────────────
        # We collect qualifying regions first so we can report accurate progress
        # without a second VirtualQueryEx walk.
        regions: list[tuple[int, int]] = []  # (base_address, size)
        addr = 0
        mbi = MEMORY_BASIC_INFORMATION()
        mbi_size = sizeof(mbi)

        while addr < MAX_ADDRESS:
            ret = _k32.VirtualQueryEx(self._handle, ctypes.c_void_p(addr), byref(mbi), mbi_size)
            if not ret:
                break
            if (
                mbi.State   == MEM_COMMIT
                and mbi.Type == MEM_PRIVATE
                and mbi.Protect in READABLE_PROTECTS
            ):
                regions.append((mbi.BaseAddress, mbi.RegionSize))
            addr += mbi.RegionSize

        total = len(regions)
        print(f"[modder] {total} qualifying heap regions to scan.")

        # Pre-allocate a single reusable buffer — avoids per-region allocation
        # Resize only when a larger region is encountered.
        buf_size   = 0
        buf        = None
        bytes_read = ctypes.c_size_t(0)

        for i, (base, size) in enumerate(regions):
            # Grow buffer only if needed
            if size > buf_size:
                buf      = (ctypes.c_char * size)()
                buf_size = size

            ok = _k32.ReadProcessMemory(
                self._handle,
                ctypes.c_void_p(base),
                buf,
                size,
                byref(bytes_read),
            )
            if not ok or bytes_read.value == 0:
                continue

            # View as bytes without copying (memoryview)
            view = memoryview(buf)[:bytes_read.value].tobytes()

            # Search all targets in this region in one pass each
            for s, needle in encoded.items():
                offset = 0
                nlen   = len(needle)
                while True:
                    idx = view.find(needle, offset)
                    if idx == -1:
                        break
                    abs_addr = base + idx
                    found[s].append(abs_addr)
                    print(f"  [{s}] → {hex(abs_addr)}")
                    offset = idx + nlen  # skip past this match (non-overlapping)

            if progress_cb:
                progress_cb(i + 1, total)

        # Merge into cache
        for s, addrs in found.items():
            self._cache.setdefault(s, [])
            # Deduplicate while preserving order
            seen = set(self._cache[s])
            for a in addrs:
                if a not in seen:
                    self._cache[s].append(a)
                    seen.add(a)

        total_found = sum(len(v) for v in found.values())
        print(f"[modder] Scan complete. {total_found} match(es) across {len(to_scan)} target(s).")
        return {t: self._cache.get(t, []) for t in targets}

    # ── Patch ─────────────────────────────────────────────────────────────────
    def patch(
        self,
        original: str,
        replacement: str,
        *,
        pad: bool = True,
    ) -> int:
        """
        Write replacement string to all cached addresses for `original`.

        Args:
            original:    The original skin path string (must have been scanned).
            replacement: The custom/local skin path to write.
            pad:         If True, left-pad replacement with '/' to match original
                         length so the string fits exactly in-place. If False,
                         replacement must be <= len(original).

        Returns:
            Number of addresses successfully patched.
        """
        if original not in self._cache or not self._cache[original]:
            raise KeyError(
                f"'{original}' not in scan cache. Call scan() first."
            )

        payload = self._build_payload(original, replacement, pad)
        if payload is None:
            raise ValueError(
                f"Replacement '{replacement}' is longer than original '{original}' "
                f"({len(replacement)} > {len(original)}). Cannot patch in-place."
            )

        raw       = payload.encode("utf-8")
        raw_len   = len(raw)
        buf       = (ctypes.c_char * raw_len)(*raw)
        written   = ctypes.c_size_t(0)
        patched   = 0

        for addr in self._cache[original]:
            ok = _k32.WriteProcessMemory(
                self._handle,
                ctypes.c_void_p(addr),
                buf,
                raw_len,
                byref(written),
            )
            if ok and written.value == raw_len:
                print(f"  [patch] {hex(addr)} ✓  '{original}' → '{payload}'")
                patched += 1
            else:
                err = _k32.GetLastError()
                print(f"  [patch] {hex(addr)} ✗  WriteProcessMemory failed (err={err})")

        return patched

    def patch_many(
        self,
        mapping: dict[str, str],
        *,
        pad: bool = True,
    ) -> dict[str, int]:
        """
        Patch multiple original→replacement pairs at once.

        Args:
            mapping: {original_path: replacement_path}
            pad:     Passed through to patch().

        Returns:
            {original_path: count_of_patched_addresses}
        """
        results = {}
        path_errors: list[str] = []
        for original, replacement in mapping.items():
            try:
                results[original] = self.patch(original, replacement, pad=pad)
            except KeyError as e:
                print(f"  [patch_many] Skipped '{original}': {e}")
                results[original] = 0
            except ValueError as e:
                path_errors.append(str(e))
                results[original] = 0
        if path_errors:
            raise ValueError("\n".join(path_errors))
        return results

    def unmod(self, skin_name: str) -> dict[str, list[int]]:
        """Restore original skin paths for `skin_name` in process memory.

        Steps:
          1. Resolve all file paths for the skin from skin_dict.
          2. For each cached path, read memory at every known address:
               - If the read fails or the memory is zeroed (address freed),
                 evict that address from the cache.
          3. Write the original skin path back to every verified live address.

        Args:
            skin_name: The unique name key from skin_list.json.

        Returns:
            {skin_path: [successfully_restored_addresses]} for every path touched.

        Raises:
            KeyError: skin_name not found in skin_list.json.
        """
        from modding.path_dictionary import skin_dict

        if skin_name not in skin_dict:
            raise KeyError(f"Skin '{skin_name}' not found in skin_list.json.")

        skin_record = skin_dict[skin_name]   # {key: original_path, ...}
        restored: dict[str, list[int]] = {}
        bytes_read = ctypes.c_size_t(0)

        for original_path in skin_record.values():
            if original_path not in self._cache:
                continue

            read_len = len(original_path.encode("utf-8")) + 1   # +1 for null terminator
            read_buf = (ctypes.c_char * read_len)()
            live_addrs: list[int] = []

            for addr in self._cache[original_path]:
                ok = _k32.ReadProcessMemory(
                    self._handle,
                    ctypes.c_void_p(addr),
                    read_buf,
                    read_len,
                    byref(bytes_read),
                )
                content = bytes(read_buf[:bytes_read.value]).decode("utf-8", errors="replace").rstrip("\x00")
                if not ok or bytes_read.value == 0 or not _LIVE_PATH_RE.match(content):
                    print(f"  [unmod] {hex(addr)}: stale/freed — evicted from cache.")
                    continue
                live_addrs.append(addr)

            self._cache[original_path] = live_addrs

            if not live_addrs:
                continue

            # Write the original path back to every live address
            raw     = original_path.encode("utf-8") + b"\x00"
            raw_len = len(raw)
            w_buf   = (ctypes.c_char * raw_len)(*raw)
            written = ctypes.c_size_t(0)
            ok_addrs: list[int] = []

            for addr in live_addrs:
                ok = _k32.WriteProcessMemory(
                    self._handle,
                    ctypes.c_void_p(addr),
                    w_buf,
                    raw_len,
                    byref(written),
                )
                if ok and written.value == raw_len:
                    print(f"  [unmod] Restored {hex(addr)}: '{original_path}'")
                    ok_addrs.append(addr)
                else:
                    err = _k32.GetLastError()
                    print(f"  [unmod] {hex(addr)} ✗ write failed (err={err})")

            if ok_addrs:
                restored[original_path] = ok_addrs

        return restored

    def invalidate_cache(self, *targets: str):
        """Remove specific targets from cache, forcing re-scan on next scan() call."""
        for t in targets:
            self._cache.pop(t, None)

    def clear_cache(self):
        """Clear the entire address cache."""
        self._cache.clear()

    @property
    def cache(self) -> dict[str, list[int]]:
        """Read-only view of the current address cache."""
        return dict(self._cache)

    # ── Internal ──────────────────────────────────────────────────────────────
    @staticmethod
    def _build_payload(placeholder: str, mod: str, pad: bool) -> Optional[str]:
        """
        Build the string to write in-place.

        - If mod is longer than placeholder: impossible, return None.
        - If same length: use mod as-is.
        - If shorter and pad=True: left-pad with '/' to match placeholder length.
        - If shorter and pad=False: use mod as-is (caller accepts shorter write).
        """
        if len(mod) > len(placeholder):
            raise ValueError(f"[apply_mod] Replacement '{mod}' is longer than placeholder '{placeholder}'")
        if len(mod) == len(placeholder) or not pad:
            return mod
        return mod.rjust(len(placeholder), "/")


# ── Convenience top-level functions (drop-in-compatible with old API) ──────────
def find_memory_address(
    process_name: str,
    old_str: str,
    progress_bar=None,
) -> list[int]:
    """
    Drop-in replacement for the old find_memory_address().
    Returns a list of addresses where old_str was found.
    """
    cb = None
    if progress_bar is not None:
        progress_bar["value"]   = 0
        progress_bar["maximum"] = 1  # will be updated by scan

        def cb(scanned, total):
            progress_bar["maximum"] = total
            progress_bar["value"]   = scanned
            progress_bar.update()

    with SkinModder(process_name) as m:
        results = m.scan([old_str], progress_cb=cb)
        return results.get(old_str, [])


def apply_mod(
    process_name: str,
    address_list: list[int],
    placeholder: str,
    mod: str,
    is_padding: bool = True,
) -> bool:
    """
    Drop-in replacement for the old apply_mod().
    Patches the given addresses directly (no re-scan).
    """
    payload = SkinModder._build_payload(placeholder, mod, is_padding)
    if payload is None:
        print(f"[apply_mod] Replacement '{mod}' is longer than placeholder.")
        raise ValueError(f"[apply_mod] Replacement '{mod}' is longer than placeholder '{placeholder}'")

    raw     = payload.encode("utf-8")
    raw_len = len(raw)
    buf     = (ctypes.c_char * raw_len)(*raw)
    written = ctypes.c_size_t(0)

    access = PROCESS_VM_WRITE | PROCESS_VM_OPERATION | PROCESS_QUERY_INFO
    pid    = _pid_by_name(process_name)
    handle = _k32.OpenProcess(access, False, pid)
    if not handle:
        raise PermissionError(f"Cannot open process. Run as administrator.")

    try:
        for addr in address_list:
            ok = _k32.WriteProcessMemory(handle, ctypes.c_void_p(addr), buf, raw_len, byref(written))
            if ok:
                print(f"Patched {hex(addr)}")
    finally:
        _k32.CloseHandle(handle)

    return True


def unmod_skin(skin_name: str) -> dict[str, list[int]]:
    """Module-level convenience wrapper for SkinModder.unmod().

    Opens a fresh process handle (inheriting the existing address cache so no
    re-scan is needed) and restores the original skin paths for `skin_name`.

    Args:
        skin_name: The unique name key from skin_list.json.

    Returns:
        {skin_path: [successfully_restored_addresses]}

    Raises:
        KeyError:       skin_name not found in skin_list.json.
        RuntimeError:   game process is not running.
        PermissionError: cannot open the process (run as administrator).
    """
    import base64
    process_name = base64.decodebytes(b"ZHdyZy5leGU=").decode()
    with SkinModder(process_name) as modder:
        return modder.unmod(skin_name)