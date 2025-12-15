import hou

import hou_module_loader

_env = hou_module_loader.load_from_hou_path(
    "scripts/sop/constants/null.py",
    "_mytools_sop_constants",
)

ENV_CTRL_NODE = _env.ENV_CTRL_NODE
CTRL_BASE_NAME = _env.CTRL_BASE_NAME
CTRL_COLOR_ACTIVE = hou.Color(_env.CTRL_COLOR_ACTIVE)
CTRL_COLOR_INACTIVE = hou.Color(_env.CTRL_COLOR_INACTIVE)


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

        if node.type().name() != "null":
            return False

        node_name = node.name() or ""
        if not node_name.upper().startswith(CTRL_BASE_NAME.upper()):
            return False

        current_ctrl_path = hou.getenv(ENV_CTRL_NODE)
        if current_ctrl_path and node.path() == current_ctrl_path:
            return False

        node_path = node.path()
        with hou.undos.group("Set CTRL Node"):
            hou.hscript("set -g {} = {}".format(ENV_CTRL_NODE, node_path))
            try:
                if hasattr(hou, "session"):
                    hou.session._CTRL_NODE_SID = node.sessionId()
            except Exception:
                pass

        for n in hou.node("/").allSubChildren():
            if n.name().startswith(CTRL_BASE_NAME) and n.path() != node_path:
                n.setColor(CTRL_COLOR_INACTIVE)
            elif n.name().startswith(CTRL_BASE_NAME) and n.path() == node_path:
                n.setColor(CTRL_COLOR_ACTIVE)

        try:
            uievent.editor.setCurrentNode(node)
            uievent.editor.update()
        except Exception:
            pass

        return True
    except Exception:
        return False


