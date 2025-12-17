import hou
from .. import nodehook_utils as _utils


def _is_vex_wrangle(node: hou.Node) -> bool:
    try:
        if not node or not isinstance(node, hou.Node):
            return False
        if node.type().category().name() != "Sop":
            return False
        tname = (node.type().name() or "").lower()
        return tname == "vex_wrangle" or tname.startswith("vex_wrangle::")
    except Exception:
        return False


def _has_spare_parms(node: hou.Node) -> bool:
    try:
        if not node or not isinstance(node, hou.Node):
            return False
        sp = node.spareParms()
        return bool(sp) and len(sp) > 0
    except Exception:
        return False


def _vex_wrangle_action(node):
    if not _is_vex_wrangle(node):
        return False

    from ..scripts import vex_wrangle
    vex_wrangle.edit_code(node)
    return True


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    return _utils.handle_ctrl_lmb_base(uievent, ctx, allow_flag_click, _vex_wrangle_action)

