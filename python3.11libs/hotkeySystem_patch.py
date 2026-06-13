"""Redirect HotkeySystem to this package's hotkeys.csv and inject local flag helpers."""

import os
import sys


def _hotkeys_file():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "hotkeys.csv"))


# ---------------------------------------------------------------------------
# Replacement helpers injected into utility_generic / utility_hotkey_system.
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


def flagSetNearestNodeExclusive(uievent, flag, select=0):
    """Turn flag OFF on every sibling, then ON on the nearest node."""
    import hou
    from utility_generic import findNearestNode

    with hou.undos.group("Set Flag Exclusive On Nearest Node"):
        editor = uievent.editor
        nearestNode = findNearestNode(editor)
        if not nearestNode:
            return
        parent = nearestNode.parent()
        if parent:
            for child in parent.children():
                if child is not nearestNode and child.isGenericFlagSet(flag):
                    child.setGenericFlag(flag, False)
        nearestNode.setGenericFlag(flag, True)
        if select == 1:
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

        utility_hotkey_system.hotkeysfile = hotkeysfile
        utility_hotkey_system.showstatus = False

        load_actions = getattr(utility_hotkey_system, "__load_actions", None)
        if callable(load_actions):
            load_actions()
    except Exception:
        pass


def _patch_utility_generic():
    """Inject helper overrides into utility_generic and utility_hotkey_system."""
    try:
        utility_generic = sys.modules.get("utility_generic")
        if utility_generic is None:
            try:
                import utility_generic as utility_generic
            except Exception:
                return

        utility_generic.flagSelectNearestNode = flagSelectNearestNode
        utility_generic.flagSetNearestNode = flagSetNearestNode
        utility_generic.flagSetNearestNodeExclusive = flagSetNearestNodeExclusive

        utility_hotkey_system = sys.modules.get("utility_hotkey_system")
        if utility_hotkey_system is not None:
            utility_hotkey_system.flagSelectNearestNode = flagSelectNearestNode
            utility_hotkey_system.flagSetNearestNode = flagSetNearestNode
            utility_hotkey_system.flagSetNearestNodeExclusive = flagSetNearestNodeExclusive
    except Exception:
        pass


_initialized = False


def init():
    global _initialized
    if _initialized:
        return

    _patch_utility_generic()
    _patch_utility_hotkey_system()

    _initialized = True


if __name__ != "__main__":
    init()
