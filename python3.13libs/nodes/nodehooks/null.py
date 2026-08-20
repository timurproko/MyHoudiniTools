import hou
from ..constants import null as _env
from .. import nodehook_utils as _utils


def _set_ctrl_node(node, uievent=None):
    if node.type().name() != "null":
        return False

    node_name = node.name() or ""
    if not node_name.upper().startswith(_env.CTRL_BASE_NAME.upper()):
        return False

    current_ctrl_path = hou.getenv(_env.ENV_CTRL_NODE)
    if current_ctrl_path and node.path() == current_ctrl_path:
        return False

    node_path = node.path()
    with hou.undos.group("Set CTRL Node"):
        try:
            hou.putenv(_env.ENV_CTRL_NODE, node_path)
        except Exception:
            pass
        try:
            hou.hscript("set -g {} = {}".format(_env.ENV_CTRL_NODE, node_path))
        except Exception:
            pass
        try:
            if hasattr(hou, "session"):
                hou.session._CTRL_NODE_SID = node.sessionId()
        except Exception:
            pass

    for n in hou.node("/").allSubChildren():
        if n.name().startswith(_env.CTRL_BASE_NAME) and n.path() != node_path:
            n.setColor(hou.Color(_env.CTRL_COLOR_INACTIVE))
        elif n.name().startswith(_env.CTRL_BASE_NAME) and n.path() == node_path:
            n.setColor(hou.Color(_env.CTRL_COLOR_ACTIVE))

    try:
        if uievent and hasattr(uievent, 'editor'):
            uievent.editor.setCurrentNode(node)
            uievent.editor.update()
    except Exception:
        pass

    return True


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    return _utils.handle_ctrl_lmb_base(uievent, ctx, allow_flag_click, _set_ctrl_node)


