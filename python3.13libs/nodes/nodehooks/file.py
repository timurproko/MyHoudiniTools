import hou
from .. import nodehook_utils as _utils


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    def action(node):
        return _utils.press_button_for_node_types(node, ("file", "filecache"), "reload")
    
    return _utils.handle_ctrl_lmb_base(uievent, ctx, allow_flag_click, action)

