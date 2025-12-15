import random
import hou
from .. import nodehook_utils as _utils


def _is_color_sop(node: hou.Node) -> bool:
    try:
        if not node or not isinstance(node, hou.Node):
            return False
        if node.type().category().name() != "Sop":
            return False
        tname = (node.type().name() or "").lower()
        return tname == "color" or tname.startswith("color::")
    except Exception:
        return False


def randomConstantColor(node: hou.Node) -> bool:
    try:
        if not _is_color_sop(node):
            return False

        parm = node.parmTuple("color")
        if parm is None:
            return False

        rgb = (random.random(), random.random(), random.random())
        with hou.undos.group("Random Color"):
            parm.set(rgb)
            try:
                node.setColor(hou.Color(rgb))
            except Exception:
                pass

        return True
    except Exception:
        return False


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    return _utils.handle_ctrl_lmb_base(uievent, ctx, allow_flag_click, randomConstantColor)


