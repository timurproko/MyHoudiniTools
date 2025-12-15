from nodes.scripts import null as _null

try:
    _null.on_created(kwargs)
except Exception:
    pass
