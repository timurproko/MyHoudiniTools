import hou


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

        if not _is_vex_wrangle(node):
            return False

        import hou_module_loader

        vex_wrangle = hou_module_loader.load_from_hou_path(
            "scripts/sop/scripts/vex_wrangle.py",
            "_mytools_sop_vex_wrangle",
        )
        vex_wrangle.show_parms(node)
        return True
    except Exception:
        return False
