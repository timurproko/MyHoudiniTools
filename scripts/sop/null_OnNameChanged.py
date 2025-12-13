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
        pass


def _check_active_ctrl_exists(constants):
    try:
        active_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
        if not active_path.strip():
            return

        node = hou.node(active_path)
        if node is None:
            hou.putenv(constants.ENV_CTRL_NODE, "")
    except:
        pass


def _update_active_ctrl_if_renamed(constants, renamed_node):
    try:
        active_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
        if not active_path.strip():
            return

        old_node = hou.node(active_path)
        
        if old_node is not None:
            if old_node.sessionId() == renamed_node.sessionId():
                hou.putenv(constants.ENV_CTRL_NODE, renamed_node.path())
        else:
            try:
                stored_parent_path = "/".join(active_path.split("/")[:-1])
                renamed_parent_path = renamed_node.parent().path()
                
                if stored_parent_path == renamed_parent_path:
                    hou.putenv(constants.ENV_CTRL_NODE, renamed_node.path())
            except:
                pass
    except:
        pass


def _set_node_color(node, color):
    try:
        node.setColor(color)
    except:
        pass


def _is_ctrl_node(node, constants):
    try:
        active_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
        if active_path:
            active_node = hou.node(active_path)
            if active_node is not None and active_node.sessionId() == node.sessionId():
                return True
            try:
                stored_parent_path = "/".join(active_path.split("/")[:-1])
                node_parent_path = node.parent().path()
                if stored_parent_path == node_parent_path:
                    stored_name = active_path.split("/")[-1]
                    if stored_name.upper().startswith(constants.CTRL_BASE_NAME.upper()):
                        return True
            except:
                pass
        
        node_color = node.color()
        inactive_color = constants.CTRL_COLOR_INACTIVE
        active_color = constants.CTRL_COLOR_ACTIVE
        
        def colors_match(c1, c2, tolerance=0.01):
            return (abs(c1.rgb()[0] - c2.rgb()[0]) < tolerance and
                    abs(c1.rgb()[1] - c2.rgb()[1]) < tolerance and
                    abs(c1.rgb()[2] - c2.rgb()[2]) < tolerance)
        
        if colors_match(node_color, inactive_color) or colors_match(node_color, active_color):
            return True
            
        return False
    except:
        return False


def _validate_ctrl_name(node, constants):
    try:
        current_name = node.name()
        ctrl_base = constants.CTRL_BASE_NAME.upper()
        
        if not current_name or not current_name.strip():
            node.setName(ctrl_base)
            return
        
        current_upper = current_name.upper()
        
        partial_matches = [ctrl_base[:i] for i in range(1, len(ctrl_base) + 1)]
        if current_upper in partial_matches:
            if current_name != ctrl_base:
                node.setName(ctrl_base)
            return
        
        if current_upper.startswith(ctrl_base):
            return
        
        new_name = f"{ctrl_base}_{current_name}"
        node.setName(new_name)
    except:
        pass


try:
    constants = _import_constants()
    if constants is None:
        raise SystemExit

    me = kwargs.get("node")
    if me is None:
        raise SystemExit

    if me.type().name() != "null":
        raise SystemExit

    current_name = me.name()
    ctrl_base = constants.CTRL_BASE_NAME.upper()
    current_name_upper = current_name.upper()
    
    if "ORIGINAL" in current_name_upper and "_OF_" in current_name_upper:
        raise SystemExit
    
    name_starts_with_ctrl = current_name_upper.startswith(ctrl_base)
    is_confirmed_ctrl_node = _is_ctrl_node(me, constants)
    
    if not name_starts_with_ctrl and not is_confirmed_ctrl_node:
        raise SystemExit

    _validate_ctrl_name(me, constants)

    final_name_upper = me.name().upper()
    if not final_name_upper.startswith(ctrl_base):
        raise SystemExit

    inactive_color = constants.CTRL_COLOR_INACTIVE
    active_color = constants.CTRL_COLOR_ACTIVE

    def _apply():
        _update_active_ctrl_if_renamed(constants, me)
        _check_active_ctrl_exists(constants)

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

