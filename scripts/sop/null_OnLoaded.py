import hou
import traceback
import sys
import os

try:
    try:
        import constants
    except ImportError:
        constants = None
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
                                break
                            except ImportError:
                                pass

    if constants is None:
        raise SystemExit

    me = kwargs.get("node")
    if me is None:
        raise SystemExit

    if me.type().name() != "null":
        raise SystemExit

    if not me.name().upper().startswith(constants.CTRL_BASE_NAME.upper()):
        raise SystemExit

    inactive_color = constants.CTRL_COLOR_INACTIVE
    active_color = constants.CTRL_COLOR_ACTIVE

    active_ctrl_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
    current_path = me.path()
    is_active_ctrl = (active_ctrl_path and current_path == active_ctrl_path)

    if is_active_ctrl:
        me.setColor(active_color)
    else:
        me.setColor(inactive_color)

except SystemExit:
    pass
except:
    print(traceback.format_exc())

