import hou


_SESSION_KEY = "_MYTOOLS_COLOR_SYNC_CB"


def _session_registry():
    try:
        reg = getattr(hou.session, _SESSION_KEY, None)
        if isinstance(reg, set):
            return reg
        reg = set()
        setattr(hou.session, _SESSION_KEY, reg)
        return reg
    except Exception:
        return set()


def _color_changed(node, _event_type=None, **kwargs):
    try:
        parm_tuple = kwargs.get("parm_tuple")
        if parm_tuple is None:
            return
        if parm_tuple.name() != "color":
            return
        color = parm_tuple.eval()
        node.setColor(hou.Color(color))
    except Exception:
        return


def ensure_installed(node):
    try:
        if node is None:
            return False

        sid = getattr(node, "sessionId", None)
        sid = sid() if callable(sid) else id(node)

        reg = _session_registry()
        if sid in reg:
            return True

        node.addEventCallback((hou.nodeEventType.ParmTupleChanged,), _color_changed)
        reg.add(sid)
        return True
    except Exception:
        return False


