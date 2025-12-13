import hou
import traceback
import sys
import os


def _import_constants():
    try:
        import constants
        return constants
    except ImportError:
        pass

    # fallback: scan HOUDINI_USER_PREF_DIR/packages/**/python3.11libs
    houdini_pref_dir = hou.getenv("HOUDINI_USER_PREF_DIR")
    if houdini_pref_dir:
        packages_dir = os.path.join(houdini_pref_dir, "packages")
        if os.path.exists(packages_dir):
            for item in os.listdir(packages_dir):
                item_path = os.path.join(packages_dir, item)
                if os.path.isdir(item_path):
                    libs_dir = os.path.join(item_path, "python3.11libs")
                    if os.path.exists(libs_dir) and libs_dir not in sys.path:
                        sys.path.insert(0, libs_dir)
                        try:
                            import constants
                            return constants
                        except ImportError:
                            pass
    return None


def _defer(fn):
    """Run after Houdini finishes rename/duplicate UI updates."""
    try:
        if hasattr(hou, "ui") and hou.ui is not None:
            try:
                import hdefereval
                hdefereval.executeDeferred(fn)
                return
            except ImportError:
                pass

            holder = {"cb": None}

            def _cb():
                try:
                    fn()
                finally:
                    try:
                        hou.ui.removeEventLoopCallback(holder["cb"])
                    except:
                        pass

            holder["cb"] = _cb
            hou.ui.addEventLoopCallback(_cb)
        else:
            fn()
    except:
        # never hard fail callbacks
        pass


def _refresh_active_ctrl_env(constants):
    """
    If ENV_CTRL_NODE_ID exists, find that node by session id and refresh ENV_CTRL_NODE path.
    Also clears env if the node no longer exists.
    """
    try:
        sid_str = hou.getenv(constants.ENV_CTRL_NODE_ID) or ""
        if not sid_str.strip():
            return

        try:
            sid = int(sid_str)
        except:
            return

        node = hou.nodeBySessionId(sid)
        if node is None:
            # active node disappeared; clear env
            hou.putenv(constants.ENV_CTRL_NODE, "")
            hou.putenv(constants.ENV_CTRL_NODE_ID, "")
            return

        # update path to the new name/path
        hou.putenv(constants.ENV_CTRL_NODE, node.path())
    except:
        pass


def _set_node_color(node, color):
    try:
        node.setColor(color)
    except:
        pass


try:
    constants = _import_constants()
    if constants is None:
        raise SystemExit

    me = kwargs.get("node")
    if me is None:
        raise SystemExit

    # only CTRL nulls
    if me.type().name() != "null":
        raise SystemExit

    if not me.name().upper().startswith(constants.CTRL_BASE_NAME.upper()):
        raise SystemExit

    inactive_color = constants.CTRL_COLOR_INACTIVE
    active_color = constants.CTRL_COLOR_ACTIVE

    def _apply():
        # First: refresh env path from stable id (handles rename of active node)
        _refresh_active_ctrl_env(constants)

        active_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
        is_active = (active_path and me.path() == active_path)

        if is_active:
            _set_node_color(me, active_color)
        else:
            _set_node_color(me, inactive_color)

    _defer(_apply)

except SystemExit:
    pass
except:
    print(traceback.format_exc())

