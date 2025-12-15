from nodes.scripts import split as _split

try:
    _split.ensure_installed(kwargs.get("node"))
except Exception:
    pass
