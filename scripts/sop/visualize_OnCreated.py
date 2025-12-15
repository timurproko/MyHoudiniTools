import hou_module_loader

_visualize = None
for _rel in ("scripts/sop/visualize.py", "scripts/sop/scripts/visualize.py"):
    try:
        _visualize = hou_module_loader.load_from_hou_path(_rel, "visualize")
        break
    except Exception:
        _visualize = None

try:
    if _visualize is not None:
        _visualize.visualize_gradient(kwargs.get("node"), kwargs=kwargs)
except Exception:
    pass
