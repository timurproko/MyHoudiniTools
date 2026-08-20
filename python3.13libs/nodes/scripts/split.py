import hou
from ..constants import split as _split_consts
import mytools

_SESSION_KEY = "_MYTOOLS_SPLIT_NEGATE_COLOR_SIDS"

def is_split(node):
    try:
        if not node or not isinstance(node, hou.Node):
            return False
        tname = node.type().name() or ""
        return tname.split("::", 1)[0] == "split"
    except Exception:
        return False


def apply_color(node):
    try:
        if not is_split(node):
            return False
        p = node.parm("negate")
        if p is None:
            return False
        is_negated = bool(p.evalAsInt())
        color = _split_consts.NEGATE_ON_COLOR if is_negated else _split_consts.NEGATE_OFF_COLOR
        node.setColor(hou.Color(color))
        return True
    except Exception:
        return False


def _negate_changed(node, _event_type=None, **kwargs):
    try:
        parm_tuple = kwargs.get("parm_tuple")
        if parm_tuple is None or parm_tuple.name() != "negate":
            return
        apply_color(node)
    except Exception:
        return


def ensure_installed(node):
    try:
        if not is_split(node):
            return False
        sid = node.sessionId()
        reg = mytools.session_set(_SESSION_KEY)
        if sid not in reg:
            node.addEventCallback((hou.nodeEventType.ParmTupleChanged,), _negate_changed)
            reg.add(sid)
        return apply_color(node)
    except Exception:
        return False


def toggle_negate(node):
    """
    Toggle 'negate' parm on split node and refresh color.
    Returns True if toggled.
    """
    try:
        if not is_split(node):
            return False
        ensure_installed(node)
        p = node.parm("negate")
        if p is None:
            return False
        v = 1 if int(p.evalAsInt()) == 0 else 0
        with hou.undos.group("Split: Toggle Invert Selection"):
            p.set(v)
        apply_color(node)
        return True
    except Exception:
        return False


