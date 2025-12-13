import hou
import traceback
import hou_module_loader

_split_consts = hou_module_loader.load_from_hou_path(
    "scripts/sop/constants/split.py",
    "_mytools_split_constants",
)
NEGATE_OFF_COLOR = _split_consts.NEGATE_OFF_COLOR
NEGATE_ON_COLOR = _split_consts.NEGATE_ON_COLOR


def _debug_enabled():
    try:
        return int(str(hou.getenv("MYTOOLS_DEBUG_SPLIT_COLOR") or "0").strip() or "0") == 1
    except Exception:
        return False


def _is_split(node):
    try:
        tname = node.type().name() or ""
        return tname.split("::", 1)[0] == "split"
    except Exception:
        return False


def _apply_color(node):
    try:
        if not _is_split(node):
            return
        p = node.parm("negate")
        if p is None:
            return
        is_negated = bool(p.evalAsInt())
        node.setColor(NEGATE_ON_COLOR if is_negated else NEGATE_OFF_COLOR)
    except Exception:
        if _debug_enabled():
            print(traceback.format_exc())


def _negate_changed(node, event_type, **kwargs):
    try:
        parm_tuple = kwargs.get("parm_tuple")
        if parm_tuple is None or parm_tuple.name() != "negate":
            return
        _apply_color(node)
    except Exception:
        if _debug_enabled():
            print(traceback.format_exc())


def ensure(node):
    try:
        if not node or not isinstance(node, hou.Node) or not _is_split(node):
            return

        reg = getattr(hou.session, "_MYTOOLS_SPLIT_NEGATE_COLOR_SIDS", None)
        if reg is None:
            reg = set()
            setattr(hou.session, "_MYTOOLS_SPLIT_NEGATE_COLOR_SIDS", reg)

        sid = node.sessionId()
        if sid not in reg:
            node.addEventCallback((hou.nodeEventType.ParmTupleChanged,), _negate_changed)
            reg.add(sid)

        _apply_color(node)
    except Exception:
        if _debug_enabled():
            print(traceback.format_exc())


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    try:
        if uievent.eventtype != "mousedown":
            return False
        if not uievent.mousestate.lmb:
            return False
        if not uievent.modifierstate.ctrl:
            return False
        if uievent.modifierstate.shift or uievent.modifierstate.alt:
            return False

        if ctx["is_flag_click"](uievent):
            return False

        node = ctx["get_node_under_mouse"](uievent)
        if not node or ctx["is_non_node"](node):
            return False

        if not _is_split(node):
            return False

        ensure(node)

        p = node.parm("negate")
        if p is None:
            return False

        v = 1 if int(p.evalAsInt()) == 0 else 0
        with hou.undos.group("Split: Toggle Invert Selection"):
            p.set(v)
        _apply_color(node)
        return True
    except Exception:
        return False


