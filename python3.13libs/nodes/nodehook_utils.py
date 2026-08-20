import hou
import inspect


def handle_ctrl_lmb_base(uievent, ctx, allow_flag_click, node_action_callback):
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

        sig = inspect.signature(node_action_callback)
        param_count = len(sig.parameters)
        if param_count >= 2:
            return node_action_callback(node, uievent)
        else:
            return node_action_callback(node)
    except Exception:
        return False


def press_button_for_node_types(node, node_types, parm_name):
    try:
        if not node or not isinstance(node, hou.Node):
            return False

        node_type_name = node.type().name()
        if isinstance(node_types, str):
            node_types = (node_types,)
        
        if node_type_name not in node_types:
            return False

        parm = node.parm(parm_name)
        if parm is None:
            return False

        parm.pressButton()
        return True
    except Exception:
        return False

