from importlib import import_module
from pathlib import Path

for _f in Path(__file__).parent.glob("on_*.py"):
    _name = _f.stem
    globals()[_name] = getattr(import_module(f".{_name}", package=__name__), _name)