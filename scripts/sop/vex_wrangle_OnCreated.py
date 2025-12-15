from nodes.scripts import vex_wrangle as _vex_wrangle

try:
    node = kwargs.get("node")
    if node is not None:
        _vex_wrangle.create_parms(node)
except Exception:
    pass


