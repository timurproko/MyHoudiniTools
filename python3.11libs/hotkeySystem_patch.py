"""Redirect HotkeySystem to this package's hotkeys.csv and restore standard RMB behaviour.

HotkeySystem normally hijacks Network Editor right-click to fire its own action,
which blocks the stock node menu. This patch:
  * Redirects utility_hotkey_system.hotkeysfile to this package's hotkeys.csv.
  * Replaces the upstream flag / nearest-node helpers with versions that open the
    standard node menu on RMB (selectDisplayNearestNodeInEditor).
  * Silences upstream console spam.
  * Suppresses the Ctrl+MMB hotkey that conflicts with the default viewport gesture.
"""

import inspect
import os
import sys


def _package_root():
    for var_name in ("MYHOUDINITOOLS", "MY_HOUDINI_TOOLS", "MYHOUDINITOOLS_PACKAGE", "MY_HOUDINI_TOOLS_PACKAGE"):
        value = os.environ.get(var_name)
        if value:
            return value

    try:
        import hou

        for var_name in ("MYHOUDINITOOLS", "MY_HOUDINI_TOOLS", "MYHOUDINITOOLS_PACKAGE", "MY_HOUDINI_TOOLS_PACKAGE"):
            value = hou.getenv(var_name)
            if value:
                return value
    except Exception:
        pass

    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def _hotkeys_file():
    return os.path.abspath(os.path.join(_package_root(), "hotkeys.csv"))


# ---------------------------------------------------------------------------
# Replacement helpers injected into utility_generic / utility_hotkey_system.
# selectDisplayNearestNodeInEditor is what brings standard RMB back: when the
# upstream hotkey fires on a mousedown RMB event it now opens the stock node
# menu instead of stealing the click.
# ---------------------------------------------------------------------------


def flagSelectNearestNode(uievent, flag, select=0):
    import hou
    from utility_generic import findNearestNode

    with hou.undos.group("Flag Nearest Node"):
        editor = uievent.editor
        nearestNode = findNearestNode(editor)
        if nearestNode:
            nearestNode.setGenericFlag(flag, not nearestNode.isGenericFlagSet(flag))
        if select == 1 and nearestNode:
            nearestNode.setSelected(True, clear_all_selected=True)


def flagSetNearestNode(uievent, flag, select=0):
    """Set a flag ON for the nearest node (no toggle).

    Special case for SOPs: when setting Visible, also set Render.
    """
    import hou
    from utility_generic import findNearestNode

    with hou.undos.group("Set Flag On Nearest Node"):
        editor = uievent.editor
        nearestNode = findNearestNode(editor)
        if nearestNode:
            nearestNode.setGenericFlag(flag, True)
            try:
                is_sop = nearestNode.type().category() == hou.sopNodeTypeCategory()
                if flag == hou.nodeFlag.Visible and is_sop:
                    nearestNode.setRenderFlag(True)
            except Exception:
                pass
        if select == 1 and nearestNode:
            nearestNode.setSelected(True, clear_all_selected=True)


def flagSelectedNodes(uievent, flag):
    import hou

    with hou.undos.group("Flag Selected Nodes"):
        editor = uievent.editor
        if editor.pwd().isEditable():
            selNodes = hou.selectedNodes()
            nodes_to_operate = [n for n in selNodes if not n.isGenericFlagSet(flag)]

            if nodes_to_operate:
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
    """Restore standard RMB behaviour while keeping the upstream LMB behaviour.

    The upstream hotkey is wired to a generic action without access to the
    triggering uievent, so we walk the call stack to find it. If we detect a
    mousedown RMB inside a Network Editor, open the stock node menu; otherwise
    fall back to the previous select / display-flag toggle.
    """
    import hou

    stack = inspect.stack()
    editor = hou.ui.paneTabUnderCursor()
    editortype = editor.type() if editor else None

    for i, frame_info in enumerate(stack[1:], 1):
        try:
            filename = str(frame_info.filename)
            if 'nodegraphhooks' not in filename:
                continue
            for check_idx in range(i + 1, -1, -1):
                if not (0 <= check_idx < len(stack)):
                    continue
                check_frame = stack[check_idx].frame
                if 'uievent' not in check_frame.f_locals:
                    continue
                uievent = check_frame.f_locals['uievent']
                if (
                    getattr(uievent, 'eventtype', None) == 'mousedown'
                    and getattr(getattr(uievent, 'mousestate', None), 'rmb', False)
                ):
                    ev_editor = getattr(uievent, 'editor', None)
                    if ev_editor and ev_editor.type() == hou.paneTabType.NetworkEditor:
                        target = nearestNode
                        if target is None:
                            from utility_generic import findNearestNode
                            target = findNearestNode(ev_editor)
                        if target:
                            ev_editor.openNodeMenu(node=target)
                        return
        except (AttributeError, KeyError, TypeError, IndexError):
            continue

    if editortype == hou.paneTabType.NetworkEditor:
        from utility_generic import findNearestNode, setNodeDisplayFlag, setNodeRenderFlag
        if nearestNode is None:
            nearestNode = findNearestNode(editor)
        if not nearestNode:
            return
        if nearestNode.isSelected():
            if editor.pwd().isEditable():
                with hou.undos.group("Display Nearest Node"):
                    context = nearestNode.type().category().name()
                    setNodeDisplayFlag(nearestNode, context, True)
                    setNodeRenderFlag(nearestNode, context, True)
        else:
            with hou.undos.group("Select Nearest Node"):
                nearestNode.setSelected(True, clear_all_selected=True)


# ---------------------------------------------------------------------------
# Patchers
# ---------------------------------------------------------------------------


def _patch_utility_hotkey_system():
    """Make utility_hotkey_system read this package's hotkeys.csv."""
    try:
        utility_hotkey_system = sys.modules.get("utility_hotkey_system")
        if utility_hotkey_system is None:
            try:
                import utility_hotkey_system as utility_hotkey_system
            except Exception:
                return

        hotkeysfile = _hotkeys_file()
        if not os.path.exists(hotkeysfile):
            return

        already_using_file = os.path.abspath(str(getattr(utility_hotkey_system, "hotkeysfile", ""))) == hotkeysfile
        utility_hotkey_system.hotkeysfile = hotkeysfile
        utility_hotkey_system.showstatus = False

        load_actions = getattr(utility_hotkey_system, "__load_actions", None)
        if callable(load_actions) and not getattr(load_actions, "_mytools_hotkeys_file_guard", False):
            original_load_actions = load_actions

            def load_actions_from_mytools_hotkeys(*args, **kwargs):
                utility_hotkey_system.hotkeysfile = hotkeysfile
                utility_hotkey_system.showstatus = False
                if not os.path.exists(hotkeysfile):
                    return
                try:
                    return original_load_actions()
                finally:
                    utility_hotkey_system.showstatus = False

            load_actions_from_mytools_hotkeys._mytools_hotkeys_file_guard = True
            utility_hotkey_system.__load_actions = load_actions_from_mytools_hotkeys
            load_actions = load_actions_from_mytools_hotkeys

        watcher = getattr(utility_hotkey_system, "fs_watcher", None)
        if watcher is not None:
            try:
                try:
                    watcher.fileChanged.disconnect()
                except Exception:
                    pass
                for path in list(watcher.files()):
                    if os.path.basename(path).lower() == "hotkeys.csv" and os.path.abspath(path) != hotkeysfile:
                        watcher.removePath(path)
                if hotkeysfile not in {os.path.abspath(path) for path in watcher.files()}:
                    watcher.addPath(hotkeysfile)
                if callable(load_actions):
                    watcher.fileChanged.connect(load_actions)
            except Exception:
                pass

        if callable(load_actions) and not already_using_file:
            load_actions()
    except Exception:
        pass


def _patch_utility_generic():
    """Inject RMB-friendly helpers into utility_generic and utility_hotkey_system."""
    try:
        utility_generic = sys.modules.get("utility_generic")
        if utility_generic is None:
            try:
                import utility_generic as utility_generic
            except Exception:
                return

        utility_generic.flagSelectNearestNode = flagSelectNearestNode
        utility_generic.flagSetNearestNode = flagSetNearestNode
        utility_generic.flagSelectedNodes = flagSelectedNodes
        utility_generic.showNodeMenuWithoutSelect = showNodeMenuWithoutSelect
        utility_generic.selectDisplayNearestNodeInEditor = selectDisplayNearestNodeInEditor

        utility_hotkey_system = sys.modules.get("utility_hotkey_system")
        if utility_hotkey_system is not None:
            utility_hotkey_system.flagSelectNearestNode = flagSelectNearestNode
            utility_hotkey_system.flagSetNearestNode = flagSetNearestNode
            utility_hotkey_system.flagSelectedNodes = flagSelectedNodes
            utility_hotkey_system.showNodeMenuWithoutSelect = showNodeMenuWithoutSelect
            utility_hotkey_system.selectDisplayNearestNodeInEditor = selectDisplayNearestNodeInEditor
    except Exception:
        pass


def _patch_nodegraphhooks_ctrl_mmb():
    """Drop Ctrl+MMB mousedown so the default viewport gesture is restored."""
    try:
        try:
            import nodegraphhooks  # noqa: F401
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


_initialized = False


def init():
    global _initialized
    if _initialized:
        return

    _patch_utility_generic()
    _patch_utility_hotkey_system()
    _patch_nodegraphhooks_ctrl_mmb()

    _initialized = True


if __name__ != "__main__":
    init()
