import hou
from .. import nodehook_utils as _utils

_last_clicked_node = None


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


def _has_spare_parms(node: hou.Node) -> bool:
    try:
        if not node or not isinstance(node, hou.Node):
            return False
        sp = node.spareParms()
        return bool(sp) and len(sp) > 0
    except Exception:
        return False


def _vex_wrangle_action(node):
    global _last_clicked_node
    
    if not _is_vex_wrangle(node):
        return False

    is_same_node = _last_clicked_node is not None and _last_clicked_node.path() == node.path()
    
    if not is_same_node:
        _last_clicked_node = node
        from ..scripts import vex_wrangle
        vex_wrangle.edit_code(node)
        return True
    
    desktop = hou.ui.curDesktop()
    vsc_tab_active = False
    for pane in desktop.panes():
        current_tab = pane.currentTab()
        if current_tab and current_tab.type() == hou.paneTabType.PythonPanel:
            if current_tab.name() == "Visual Studio Code":
                vsc_tab_active = True
                break
    
    from ..scripts import vex_wrangle
    
    if vsc_tab_active:
        node.setSelected(True, clear_all_selected=True)
        parm_pane = hou.ui.paneTabOfType(hou.paneTabType.Parm)
        if parm_pane:
            parm_pane.setIsCurrentTab()
    else:
        vex_wrangle.edit_code(node)
    
    return True


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    return _utils.handle_ctrl_lmb_base(uievent, ctx, allow_flag_click, _vex_wrangle_action)

