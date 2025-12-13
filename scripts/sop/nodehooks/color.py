import random
import hou


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

        node = ctx["get_node_under_mouse"](uievent) or ctx["find_nearest_node"](uievent.editor)
        if not node or ctx["is_non_node"](node):
            return False

        return randomConstantColor(node)
    except Exception:
        return False


