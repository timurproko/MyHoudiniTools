import hou
import inspect
import sys


def flagSelectNearestNode(uievent, flag, select=0):
    from utility_generic import findNearestNode

    with hou.undos.group("Flag Nearest Node"):
        editor = uievent.editor
        nearestNode = findNearestNode(editor)
        if nearestNode:
            nearestNode.setGenericFlag(flag, not nearestNode.isGenericFlagSet(flag))
        if select == 1:
            nearestNode.setSelected(True, clear_all_selected=True)


def flagSelectedNodes(uievent, flag):
    with hou.undos.group("Flag Selected Nodes"):
        editor = uievent.editor
        if editor.pwd().isEditable():
            selNodes = hou.selectedNodes()
            nodes_to_operate = []
            for n in selNodes:
                if not n.isGenericFlagSet(flag):
                    nodes_to_operate.append(n)

            if len(nodes_to_operate) > 0:
                for n in nodes_to_operate:
                    n.setGenericFlag(flag, True)
            else:
                for n in selNodes:
                    n.setGenericFlag(flag, not n.isGenericFlagSet(flag))


def showNodeMenuWithoutSelect(uievent, nearestNode=None):
    from utility_generic import findNearestNode

    editor = uievent.editor

    if nearestNode is None:
        nearestNode = findNearestNode(editor)
    
    if nearestNode:
        editor.openNodeMenu(node=nearestNode)


def selectDisplayNearestNodeInEditor(nearestNode=None):
    stack = inspect.stack()
    editor = hou.ui.paneTabUnderCursor()
    editortype = editor.type()

    for i, frame_info in enumerate(stack[1:], 1):
        try:
            frame = frame_info.frame
            filename = str(frame_info.filename)
            code_context = frame_info.code_context[0] if frame_info.code_context else ""
            
            if 'nodegraphhooks' in filename:
                for check_idx in range(i+1, -1, -1):
                    if 0 <= check_idx < len(stack):
                        check_frame_info = stack[check_idx]
                        check_frame = check_frame_info.frame
                        if 'uievent' in check_frame.f_locals:
                            uievent = check_frame.f_locals['uievent']
                            if (hasattr(uievent, 'mousestate') and 
                                hasattr(uievent.mousestate, 'rmb') and 
                                uievent.mousestate.rmb and
                                hasattr(uievent, 'eventtype') and
                                uievent.eventtype == 'mousedown'):
                                editor = uievent.editor
                                if editor and editor.type() == hou.paneTabType.NetworkEditor:
                                    if nearestNode:
                                        editor.openNodeMenu(node=nearestNode)
                                        return
                                    else:
                                        from utility_generic import findNearestNode
                                        nearestNode = findNearestNode(editor)
                                        if nearestNode:
                                            editor.openNodeMenu(node=nearestNode)
                                            return
        except (AttributeError, KeyError, TypeError, IndexError):
            continue
    
    if editortype == hou.paneTabType.NetworkEditor:
        from utility_generic import findNearestNode, setNodeDisplayFlag, setNodeRenderFlag
        if nearestNode is None:
            nearestNode = findNearestNode(editor)
        if nearestNode:
            if nearestNode.isSelected():
                if editor.pwd().isEditable():
                    with hou.undos.group("Display Nearest Node"):
                        context = nearestNode.type().category().name() 
                        setNodeDisplayFlag(nearestNode, context, True)
                        setNodeRenderFlag(nearestNode, context, True)
            else:
                with hou.undos.group("Select Nearest Node"):
                    nearestNode.setSelected(True, clear_all_selected=True)


def _patch_utility_generic():
    if 'utility_generic' in sys.modules:
        utility_generic = sys.modules['utility_generic']
        if hasattr(sys.modules[__name__], 'flagSelectNearestNode'):
            utility_generic.flagSelectNearestNode = flagSelectNearestNode
        if hasattr(sys.modules[__name__], 'flagSelectedNodes'):
            utility_generic.flagSelectedNodes = flagSelectedNodes
        if hasattr(sys.modules[__name__], 'showNodeMenuWithoutSelect'):
            utility_generic.showNodeMenuWithoutSelect = showNodeMenuWithoutSelect
        if hasattr(sys.modules[__name__], 'selectDisplayNearestNodeInEditor'):
            utility_generic.selectDisplayNearestNodeInEditor = selectDisplayNearestNodeInEditor
        
        if 'utility_hotkey_system' in sys.modules:
            utility_hotkey_system = sys.modules['utility_hotkey_system']
            if hasattr(sys.modules[__name__], 'flagSelectNearestNode'):
                utility_hotkey_system.flagSelectNearestNode = flagSelectNearestNode
            if hasattr(sys.modules[__name__], 'flagSelectedNodes'):
                utility_hotkey_system.flagSelectedNodes = flagSelectedNodes
            if hasattr(sys.modules[__name__], 'showNodeMenuWithoutSelect'):
                utility_hotkey_system.showNodeMenuWithoutSelect = showNodeMenuWithoutSelect
            if hasattr(sys.modules[__name__], 'selectDisplayNearestNodeInEditor'):
                utility_hotkey_system.selectDisplayNearestNodeInEditor = selectDisplayNearestNodeInEditor


_initialized = False


def init():
    global _initialized
    
    if _initialized:
        return
    
    try:
        import utility_generic
        _patch_utility_generic()
    except ImportError:
        pass
    except Exception as e:
        pass
    
    _initialized = True


if __name__ != '__main__':
    init()