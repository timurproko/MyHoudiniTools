import hou
import traceback
import sys
import os

try:
    try:
        import parms
    except ImportError:
        parms = None
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
                                import parms
                                break
                            except ImportError:
                                pass

    me = kwargs.get("node")
    if me is None:
        raise SystemExit

    if me.type().name() != "null":
        raise SystemExit

    ctrl_base = (parms.CTRL_BASE_NAME if parms else "CTRL")
    if not me.name().upper().startswith(ctrl_base.upper()):
        raise SystemExit

    inactive_color = (parms.CTRL_COLOR_INACTIVE if parms else hou.Color((0.996, 0.682, 0.682)))
    active_color = (parms.CTRL_COLOR_ACTIVE if parms else hou.Color((0.8, 0.2, 0.2)))

    active_ctrl_path = hou.getenv("ctrl_node") or ""
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

