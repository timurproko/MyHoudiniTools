from nodes.scripts import visualize as _visualize

try:
    _visualize.visualize_gradient(kwargs.get("node"), kwargs=kwargs)
except Exception:
    pass
