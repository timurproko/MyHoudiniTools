from nodes.scripts import null as _null

try:
    _null.on_loaded(kwargs)
except Exception:
    pass
