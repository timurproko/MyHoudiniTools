import hou
from nodes.scripts import vex_wrangle as _vex_wrangle

try:
    node = kwargs.get("node")
    if node is not None:
        tname = (node.type().name() or "").lower()
        if tname == "vex_wrangle" or tname.startswith("vex_wrangle::"):
            def _on_node_deleted(**cb_kwargs):
                try:
                    _vex_wrangle.on_deleted(node)
                except Exception:
                    pass
            
            node.addEventCallback(
                (hou.nodeEventType.BeingDeleted,),
                _on_node_deleted
            )
except Exception:
    pass
