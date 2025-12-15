import hou


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

        if node.type().name() != "rop_fbx":
            return False

        execute_parm = node.parm("execute")
        if execute_parm is None:
            return False

        try:
            execute_parm.pressButton()
            return True
        except Exception:
            return False

    except Exception:
        return False

