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

        node_type_name = node.type().name()
        if node_type_name not in ("file", "filecache"):
            return False

        reload_parm = node.parm("reload")
        if reload_parm is None:
            return False

        try:
            reload_parm.pressButton()
            return True
        except Exception:
            return False

    except Exception:
        return False

