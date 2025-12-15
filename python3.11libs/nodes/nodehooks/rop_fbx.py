import hou
from .. import nodehook_utils as _utils


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    def action(node):
        return _utils.press_button_for_node_types(node, ("rop_fbx", "unity_output_geometry"), "execute")
    
    return _utils.handle_ctrl_lmb_base(uievent, ctx, allow_flag_click, action)

