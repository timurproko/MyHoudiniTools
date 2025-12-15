import hou
import hou_module_loader

_utils = hou_module_loader.load_from_hou_path(
    "scripts/sop/nodehooks/_utils.py",
    "_mytools_nodehooks_utils",
)


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    def action(node):
        return _utils.press_button_for_node_types(node, ("file", "filecache"), "reload")
    
    return _utils.handle_ctrl_lmb_base(uievent, ctx, allow_flag_click, action)

