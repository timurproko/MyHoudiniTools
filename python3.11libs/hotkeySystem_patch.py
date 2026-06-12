"""Redirect HotkeySystem to this package's hotkeys.csv only."""

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


def init():
    _patch_utility_hotkey_system()


if __name__ != "__main__":
    init()
