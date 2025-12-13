import hou


def _cycle_switch_node_input(node):
    if not node or not isinstance(node, hou.Node):
        return False

    node_type = (node.type().name() or "").lower()
    if "switch" not in node_type:
        return False

    input_parm = None
    for parm_name in ("input", "index", "switch"):
        p = node.parm(parm_name)
        if p is not None:
            input_parm = p
            break

    if input_parm is None:
        for p in node.parms():
            try:
                if p.parmTemplate().dataType() == hou.parmData.Int:
                    n = (p.name() or "").lower()
                    if "input" in n or "index" in n:
                        input_parm = p
                        break
            except Exception:
                continue

    if input_parm is None:
        return False

    try:
        current_input = int(input_parm.evalAsInt())
    except Exception:
        return False

    connected = []
    for i in range(64):
        try:
            if node.input(i) is not None:
                connected.append(i)
        except IndexError:
            break
        except Exception:
            continue

    if len(connected) < 2:
        return False

    connected.sort()

    try:
        if current_input in connected:
            idx = connected.index(current_input)
            next_input = connected[(idx + 1) % len(connected)]
        else:
            next_input = connected[0]
    except Exception:
        next_input = connected[0]

    try:
        with hou.undos.group("Cycle Switch Input"):
            input_parm.set(next_input)
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

        return _cycle_switch_node_input(node)
    except Exception:
        return False


