import hou
import hou_module_loader

_env = hou_module_loader.load_from_hou_path(
    "scripts/sop/constants/null.py",
    "_mytools_sop_constants",
)

_utils = hou_module_loader.load_from_hou_path(
    "scripts/sop/nodehooks/_utils.py",
    "_mytools_nodehooks_utils",
)

ENV_CTRL_NODE = _env.ENV_CTRL_NODE
CTRL_BASE_NAME = _env.CTRL_BASE_NAME
CTRL_COLOR_ACTIVE = hou.Color(_env.CTRL_COLOR_ACTIVE)
CTRL_COLOR_INACTIVE = hou.Color(_env.CTRL_COLOR_INACTIVE)


def _set_ctrl_node(node, uievent=None):
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
        try:
            hou.putenv(ENV_CTRL_NODE, node_path)
        except Exception:
            pass
        try:
            hou.hscript("set -g {} = {}".format(ENV_CTRL_NODE, node_path))
        except Exception:
            pass
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
        if uievent and hasattr(uievent, 'editor'):
            uievent.editor.setCurrentNode(node)
            uievent.editor.update()
    except Exception:
        pass

    return True


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    return _utils.handle_ctrl_lmb_base(uievent, ctx, allow_flag_click, _set_ctrl_node)


