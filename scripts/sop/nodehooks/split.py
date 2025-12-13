import hou
import traceback
import hou_module_loader

_split = hou_module_loader.load_from_hou_path(
    "scripts/sop/scripts/split.py",
    "_mytools_sop_split_script",
)


def _debug_enabled():
    try:
        return int(str(hou.getenv("MYTOOLS_DEBUG_SPLIT_COLOR") or "0").strip() or "0") == 1
    except Exception:
        return False


def ensure(node):
    try:
        _split.ensure_installed(node)
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

        if not _split.is_split(node):
            return False

        ensure(node)
        return bool(_split.toggle_negate(node))
    except Exception:
        return False


