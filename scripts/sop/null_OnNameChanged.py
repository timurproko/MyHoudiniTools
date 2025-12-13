import hou
import traceback
import hou_module_loader

def _load_constants():
    try:
        return hou_module_loader.load_from_hou_path(
            "scripts/sop/constants/null.py",
            "_mytools_sop_constants",
        )
    except Exception:
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


def _set_node_color(node, color):
    try:
        node.setColor(color)
    except:
        pass


def _check_active_ctrl_exists(constants):
    try:
        active_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
        if not active_path.strip():
            return
        active_node = hou.node(active_path)
        if active_node is None:
            hou.putenv(constants.ENV_CTRL_NODE, "")
            try:
                if hasattr(hou, "session") and hasattr(hou.session, "_CTRL_NODE_SID"):
                    hou.session._CTRL_NODE_SID = None
            except:
                pass
            return

        try:
            if hasattr(hou, "session"):
                hou.session._CTRL_NODE_SID = active_node.sessionId()
        except:
            pass
    except:
        pass


def _update_active_ctrl_if_renamed(constants, node, old_name):
    try:
        active_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
        if not active_path.strip():
            return
        try:
            active_sid = None
            if hasattr(hou, "session"):
                active_sid = getattr(hou.session, "_CTRL_NODE_SID", None)
            if active_sid is not None and node.sessionId() == active_sid:
                hou.putenv(constants.ENV_CTRL_NODE, node.path())
        except:
            pass
    except:
        pass


def _looks_like_houdini_internal_original_name(name):
    try:
        u = (name or "").upper()
        return ("ORIGINAL" in u) and ("_OF_" in u)
    except:
        return False


def _apply_ctrl_rename_rules(node, constants, old_name):
    ctrl_base = (constants.CTRL_BASE_NAME or "CTRL").upper()

    new_name = (node.name() or "").strip()

    if _looks_like_houdini_internal_original_name(new_name) or _looks_like_houdini_internal_original_name(old_name):
        return False

    old_upper = (old_name or "").upper()
    was_ctrl = (len(old_upper) >= 4 and old_upper[:4] == ctrl_base)

    if not was_ctrl:
        return False

    new_upper = new_name.upper()

    if len(new_upper) >= 4 and new_upper[:4] == ctrl_base:
        return True

    if not new_name:
        target = ctrl_base
    else:
        target = f"{ctrl_base}_{new_name}"

    if target != node.name():
        node.setName(target, unique_name=True)

    return True


try:
    constants = _load_constants()
    if constants is None:
        raise SystemExit

    me = kwargs.get("node")
    if me is None:
        raise SystemExit

    if me.type().name() != "null":
        raise SystemExit

    old_name = kwargs.get("old_name", "") or ""

    if not hasattr(hou, "session"):
        raise SystemExit
    if getattr(hou.session, "_CTRL_RENAME_GUARD", False):
        raise SystemExit

    setattr(hou.session, "_CTRL_RENAME_GUARD", True)
    try:
        handled = _apply_ctrl_rename_rules(me, constants, old_name)
        if not handled:
            raise SystemExit

        def _apply_after():
            _update_active_ctrl_if_renamed(constants, me, old_name)
            _check_active_ctrl_exists(constants)

            active_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
            is_active = (active_path and me.path() == active_path)

            if is_active:
                _set_node_color(me, constants.CTRL_COLOR_ACTIVE)
            else:
                _set_node_color(me, constants.CTRL_COLOR_INACTIVE)

        _defer(_apply_after)

    finally:
        setattr(hou.session, "_CTRL_RENAME_GUARD", False)

except SystemExit:
    pass
except:
    print(traceback.format_exc())
