import hou
import inspect
import os
import sys


def _mytools_hotkeys_file():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hotkeys.csv"))


def _patch_utility_hotkey_system():
    """Make HotkeySystem read MyHoudiniTools/hotkeys.csv.

    HotkeySystem's utility_hotkey_system.py normally resolves hotkeys.csv next to
    the HotkeySystem package.  This patch keeps using the upstream package code,
    but redirects its module-level hotkeysfile variable and file watcher to the
    hotkeys.csv that lives in MyHoudiniTools.
    """
    try:
        utility_hotkey_system = sys.modules.get("utility_hotkey_system")
        if utility_hotkey_system is None:
            try:
                import utility_hotkey_system as utility_hotkey_system
            except Exception:
                return

        hotkeysfile = _mytools_hotkeys_file()
        if not os.path.exists(hotkeysfile):
            return

        # Suppress upstream console spam.  utility_hotkey_system.__load_actions
        # prints "Reloading hotkeys..." whenever module global showstatus is True.
        # Keep it False permanently, including watcher-triggered reloads.
        utility_hotkey_system.showstatus = False

        old_hotkeysfile = getattr(utility_hotkey_system, "hotkeysfile", None)
        already_patched = os.path.abspath(str(old_hotkeysfile)) == hotkeysfile and getattr(
            utility_hotkey_system, "_mytools_patched_hotkeysfile", False
        )

        utility_hotkey_system.hotkeysfile = hotkeysfile

        load_actions = getattr(utility_hotkey_system, "__load_actions", None)
        if callable(load_actions) and not getattr(load_actions, "_mytools_quiet", False):
            original_load_actions = load_actions

            def quiet_load_actions(*args, **kwargs):
                utility_hotkey_system.showstatus = False
                try:
                    return original_load_actions(*args, **kwargs)
                finally:
                    utility_hotkey_system.showstatus = False

            quiet_load_actions._mytools_quiet = True
            utility_hotkey_system.__load_actions = quiet_load_actions
            load_actions = quiet_load_actions

        watcher = getattr(utility_hotkey_system, "fs_watcher", None)
        if watcher is not None:
            try:
                try:
                    watcher.fileChanged.disconnect()
                except Exception:
                    pass
                for path in list(watcher.files()):
                    if os.path.basename(path).lower() == "hotkeys.csv":
                        watcher.removePath(path)
                watcher.addPath(hotkeysfile)
                if callable(load_actions):
                    watcher.fileChanged.connect(load_actions)
            except Exception:
                pass

        if callable(load_actions) and not already_patched:
            load_actions()

        utility_hotkey_system.showstatus = False
        utility_hotkey_system._mytools_patched_hotkeysfile = True
    except Exception:
        pass


def _patch_nodegraphhooks_ctrl_mmb():
    try:
        try:
            import nodegraphhooks
        except Exception:
            return

        m = sys.modules.get("nodegraphhooks")
        if not m:
            return

        orig = getattr(m, "createEventHandler", None)
        if not callable(orig):
            return

        if getattr(orig, "_mytools_patched_ctrl_mmb", False):
            return
        if hasattr(m, "_mytools_orig_createEventHandler"):
            return

        returns_tuple = False
        try:
            src = inspect.getsource(orig) or ""
            returns_tuple = ("return None, False" in src) or ("return None, True" in src)
        except Exception:
            returns_tuple = False

        def _is_ctrl_mmb_down(uievent):
            try:
                if getattr(uievent, "eventtype", None) != "mousedown":
                    return False
                ms = getattr(uievent, "mousestate", None)
                mods = getattr(uievent, "modifierstate", None)
                return bool(getattr(ms, "mmb", False) and getattr(mods, "ctrl", False))
            except Exception:
                return False

        def createEventHandler(uievent, pending_actions):
            if _is_ctrl_mmb_down(uievent):
                return (None, False) if returns_tuple else None
            return orig(uievent, pending_actions)

        createEventHandler._mytools_patched_ctrl_mmb = True
        m._mytools_orig_createEventHandler = orig
        m.createEventHandler = createEventHandler
    except Exception:
        pass


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
            _patch_utility_hotkey_system()


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

    _patch_utility_hotkey_system()
    _patch_nodegraphhooks_ctrl_mmb()
    
    _initialized = True


if __name__ != '__main__':
    init()