import hou
import mytools


_SESSION_KEY = "_MYTOOLS_COLOR_SYNC_CB"

def _color_changed(node, _event_type=None, **kwargs):
    try:
        parm_tuple = kwargs.get("parm_tuple")
        if parm_tuple is None:
            return
        if parm_tuple.name() != "color":
            return
        color = parm_tuple.eval()
        gamma = 0.45
        darkened_color = tuple(c ** gamma for c in color)
        node.setColor(hou.Color(darkened_color))
    except Exception:
        return


def ensure_installed(node):
    try:
        if node is None:
            return False

        sid = getattr(node, "sessionId", None)
        sid = sid() if callable(sid) else id(node)

        reg = mytools.session_set(_SESSION_KEY)
        if sid in reg:
            return True

        node.addEventCallback((hou.nodeEventType.ParmTupleChanged,), _color_changed)
        color_parm = node.parmTuple("color")
        if color_parm is not None:
            try:
                color = color_parm.eval()
                gamma = 0.45
                darkened_color = tuple(c ** gamma for c in color)
                node.setColor(hou.Color(darkened_color))
            except Exception:
                pass
        reg.add(sid)
        return True
    except Exception:
        return False


