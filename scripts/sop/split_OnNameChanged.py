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
        v = hou.getenv("MYTOOLS_DEBUG_SPLIT_COLOR")
        return int(str(v).strip() or "0") == 1
    except:
        return False


def _is_valid_node(node):
    try:
        if node is None:
            return False
        _ = node.type()
        return True
    except:
        return False


def _is_split(node):
    try:
        tname = node.type().name() or ""
        base = tname.split("::", 1)[0]
        return base == "split"
    except:
        return False


def _registry():
    try:
        reg = getattr(hou.session, "_MYTOOLS_SPLIT_NEGATE_COLOR_SIDS", None)
        if reg is None:
            reg = set()
            setattr(hou.session, "_MYTOOLS_SPLIT_NEGATE_COLOR_SIDS", reg)
        return reg
    except:
        return set()


def _apply(node):
    try:
        if not _is_valid_node(node) or not _is_split(node):
            return
        p = node.parm("negate")
        if p is None:
            return
        is_negated = bool(p.evalAsInt())
        node.setColor(NEGATE_ON_COLOR if is_negated else NEGATE_OFF_COLOR)
    except:
        if _debug_enabled():
            print(traceback.format_exc())


def _negate_changed(node, event_type, **kwargs):
    try:
        parm_tuple = kwargs.get("parm_tuple")
        if parm_tuple is None or parm_tuple.name() != "negate":
            return
        _apply(node)
    except:
        if _debug_enabled():
            print(traceback.format_exc())


def _ensure(node):
    try:
        if not _is_valid_node(node) or not _is_split(node):
            return
        sid = node.sessionId()
        reg = _registry()
        if sid not in reg:
            node.addEventCallback((hou.nodeEventType.ParmTupleChanged,), _negate_changed)
            reg.add(sid)
        _apply(node)
    except:
        if _debug_enabled():
            print(traceback.format_exc())


try:
    _ensure(kwargs.get("node"))
except:
    if _debug_enabled():
        print(traceback.format_exc())


