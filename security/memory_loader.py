import importlib.abc
import importlib.machinery
import importlib.util
import io
import sys
import zipfile


class MemoryImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """
    Loads Python modules from an in-memory ZIP without touching disk.

    Usage:
        importer = MemoryImporter(zip_bytes)
        importer.install()          # inserts at sys.meta_path[0]
        # all subsequent imports are served from the ZIP first
        importer.uninstall()        # remove when done (optional)

    The ZIP should contain .py files with paths matching the package
    hierarchy, e.g.:
        ui/__init__.py
        ui/main_page/__init__.py
        ui/main_page/_apply_panel.py
    """

    def __init__(self, zip_bytes: bytes):
        self._zip = zipfile.ZipFile(io.BytesIO(zip_bytes))
        self._modules: dict[str, str] = {}   # fullname → zip entry path
        self._packages: set[str]      = set()

        for name in self._zip.namelist():
            if not name.endswith(".py"):
                continue
            if name.endswith("/__init__.py"):
                # e.g. ui/main_page/__init__.py  →  ui.main_page  (package)
                pkg = name[: -len("/__init__.py")].replace("/", ".")
                self._modules[pkg] = name
                self._packages.add(pkg)
            else:
                # e.g. ui/main_page/_apply_panel.py  →  ui.main_page._apply_panel
                mod = name[:-3].replace("/", ".")
                self._modules[mod] = name

    # ── MetaPathFinder ───────────────────────────────────────────────────────

    def find_spec(self, fullname: str, path, target=None):
        if fullname not in self._modules:
            return None
        is_pkg = fullname in self._packages
        return importlib.machinery.ModuleSpec(
            fullname,
            self,
            origin=self._modules[fullname],
            is_package=is_pkg,
        )

    # ── Loader ───────────────────────────────────────────────────────────────

    def create_module(self, spec):
        return None  # use default module creation

    def exec_module(self, module):
        zip_path = self._modules[module.__spec__.name]
        source   = self._zip.read(zip_path)
        exec(compile(source, zip_path, "exec"), module.__dict__)

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def install(self) -> None:
        """Insert at front of sys.meta_path so ZIP modules take priority."""
        sys.meta_path.insert(0, self)

    def uninstall(self) -> None:
        try:
            sys.meta_path.remove(self)
        except ValueError:
            pass
