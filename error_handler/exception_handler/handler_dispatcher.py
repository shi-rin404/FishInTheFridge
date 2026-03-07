from . import *

error_handlers = {
    name[3:]: obj
    for name, obj in globals().items()
    if name.startswith("on_") and callable(obj)
}
