import hou
import inspect


def handle_ctrl_lmb_base(uievent, ctx, allow_flag_click, node_action_callback):
    """
    Base handler for Ctrl+LMB events that extracts common logic.
    
    Args:
        uievent: The UI event object
        ctx: Context dictionary with helper functions
        allow_flag_click: Whether flag clicks are allowed
        node_action_callback: Callback function(node, uievent=None) -> bool that performs the action
                             Can accept either (node) or (node, uievent)
                             Returns True if action was performed, False otherwise
    
    Returns:
        bool: True if event was handled, False otherwise
    """
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

        # Check if callback accepts uievent as second parameter
        sig = inspect.signature(node_action_callback)
        param_count = len(sig.parameters)
        if param_count >= 2:
            return node_action_callback(node, uievent)
        else:
            return node_action_callback(node)
    except Exception:
        return False


def press_button_for_node_types(node, node_types, parm_name):
    """
    Press a button parameter for nodes matching specified types.
    
    Args:
        node: The node to check
        node_types: String or tuple/list of strings for node type names to match
        parm_name: Name of the button parameter to press
    
    Returns:
        bool: True if button was pressed, False otherwise
    """
    try:
        if not node or not isinstance(node, hou.Node):
            return False

        node_type_name = node.type().name()
        if isinstance(node_types, str):
            node_types = (node_types,)
        
        if node_type_name not in node_types:
            return False

        parm = node.parm(parm_name)
        if parm is None:
            return False

        parm.pressButton()
        return True
    except Exception:
        return False

