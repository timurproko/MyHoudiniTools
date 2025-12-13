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
            except:
                pass
        else:
            try:
                if hasattr(hou, "session"):
                    hou.session._CTRL_NODE_SID = node.sessionId()
            except:
                pass
    except:
        pass


def _set_node_color(node, color):
    try:
        node.setColor(color)
    except:
        pass


try:
    constants = _load_constants()
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

    def _apply():
        _check_active_ctrl_exists(constants)

        active_path = hou.getenv(constants.ENV_CTRL_NODE) or ""
        is_active = False
        if active_path:
            try:
                active_node = hou.node(active_path)
                if active_node is not None:
                    is_active = (active_node.sessionId() == me.sessionId())
                else:
                    is_active = (me.path() == active_path)
            except:
                is_active = (me.path() == active_path)

        if is_active:
            _set_node_color(me, active_color)
        else:
            _set_node_color(me, inactive_color)

    _defer(_apply)

except SystemExit:
    pass
except:
    print(traceback.format_exc())
