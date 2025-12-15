import hou_module_loader

_vex_wrangle = None
for _rel in ("scripts/sop/vex_wrangle.py", "scripts/sop/scripts/vex_wrangle.py"):
    try:
        _vex_wrangle = hou_module_loader.load_from_hou_path(_rel, "vex_wrangle")
        break
    except Exception:
        _vex_wrangle = None

try:
    if _vex_wrangle is not None:
        node = kwargs.get("node")
        if node is not None:
            _vex_wrangle.create_parms(node)
except Exception:
    pass


