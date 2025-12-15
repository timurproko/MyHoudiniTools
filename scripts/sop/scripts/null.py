import hou
import hou_module_loader
import mytools


def _load_constants():
    try:
        return hou_module_loader.load_from_hou_path(
            "scripts/sop/constants/null.py",
            "_mytools_sop_constants",
        )
    except Exception:
        return None


def _check_active_ctrl_exists(constants):
    try:
        active_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
        if not active_path.strip():
            return

        node = hou.node(active_path)
        if node is None:
            hou.putenv(constants.ENV_CTRL_NODE, "")
            try:
                if hasattr(hou, "session") and hasattr(hou.session, "_CTRL_NODE_SID"):
                    hou.session._CTRL_NODE_SID = None
            except Exception:
                pass
        else:
            try:
                if hasattr(hou, "session"):
                    hou.session._CTRL_NODE_SID = node.sessionId()
            except Exception:
                pass
    except Exception:
        pass


def _apply_active_color(node, constants):
    try:
        _check_active_ctrl_exists(constants)

        active_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
        is_active = False
        if active_path:
            try:
                active_node = hou.node(active_path)
                if active_node is not None:
                    is_active = (active_node.sessionId() == node.sessionId())
                else:
                    is_active = (node.path() == active_path)
            except Exception:
                is_active = (node.path() == active_path)

        if is_active:
            mytools.set_node_color(node, constants.CTRL_COLOR_ACTIVE)
        else:
            mytools.set_node_color(node, constants.CTRL_COLOR_INACTIVE)
    except Exception:
        pass


def _looks_like_houdini_internal_original_name(name):
    try:
        u = (name or "").upper()
        return ("ORIGINAL" in u) and ("_OF_" in u)
    except Exception:
        return False


def _apply_ctrl_rename_rules(node, constants, old_name):
    try:
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
    except Exception:
        return False


def _update_active_ctrl_if_renamed(constants, node):
    try:
        active_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
        if not active_path.strip():
            return
        active_sid = None
        try:
            if hasattr(hou, "session"):
                active_sid = getattr(hou.session, "_CTRL_NODE_SID", None)
        except Exception:
            active_sid = None

        if active_sid is not None and node.sessionId() == active_sid:
            hou.putenv(constants.ENV_CTRL_NODE, node.path())
    except Exception:
        pass


def on_created(kwargs):
    try:
        constants = _load_constants()
        if constants is None:
            return

        node = (kwargs or {}).get("node")
        if node is None or node.type().name() != "null":
            return

        if not (node.name() or "").upper().startswith((constants.CTRL_BASE_NAME or "").upper()):
            return

        mytools.defer(lambda: _apply_active_color(node, constants))
    except Exception:
        pass


def on_loaded(kwargs):
    return on_created(kwargs)


def on_name_changed(kwargs):
    try:
        constants = _load_constants()
        if constants is None:
            return

        node = (kwargs or {}).get("node")
        if node is None or node.type().name() != "null":
            return

        old_name = (kwargs or {}).get("old_name", "") or ""

        if not hasattr(hou, "session"):
            return
        if getattr(hou.session, "_CTRL_RENAME_GUARD", False):
            return

        setattr(hou.session, "_CTRL_RENAME_GUARD", True)
        try:
            handled = _apply_ctrl_rename_rules(node, constants, old_name)
            if not handled:
                return

            def _apply_after():
                _update_active_ctrl_if_renamed(constants, node)
                _apply_active_color(node, constants)

            mytools.defer(_apply_after)
        finally:
            setattr(hou.session, "_CTRL_RENAME_GUARD", False)
    except Exception:
        pass


