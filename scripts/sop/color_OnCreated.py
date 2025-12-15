from nodes.scripts import color as _color

try:
    _color.ensure_installed(kwargs.get("node"))
except Exception:
    pass