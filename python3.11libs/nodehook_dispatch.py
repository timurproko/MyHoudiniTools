import traceback
import hou

import hou_module_loader


_HOOK_SPECS = (
    ("_mytools_hook_split", "scripts/sop/nodehooks/split.py"),
    ("_mytools_hook_switch", "scripts/sop/nodehooks/switch.py"),
    ("_mytools_hook_null", "scripts/sop/nodehooks/null.py"),
)


def _debug_enabled():
    try:
        return int(str(hou.getenv("MYTOOLS_DEBUG_NODEHOOKS") or "0").strip() or "0") == 1
    except Exception:
        return False


def _load_hooks():
    hooks = []
    for mod_name, rel_path in _HOOK_SPECS:
        try:
            m = hou_module_loader.load_from_hou_path(rel_path, mod_name)
            hooks.append(m)
        except Exception:
            if _debug_enabled():
                print("[MYTOOLS][nodehook_dispatch] Failed loading %s (%s)\n%s" % (rel_path, mod_name, traceback.format_exc()))
    return hooks


def _hooks():
    try:
        cache = getattr(hou.session, "_MYTOOLS_NODEHOOK_MODULES", None)
        if cache is None:
            cache = _load_hooks()
            setattr(hou.session, "_MYTOOLS_NODEHOOK_MODULES", cache)
        return cache
    except Exception:
        return _load_hooks()


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    for m in _hooks():
        fn = getattr(m, "handle_ctrl_lmb", None)
        if fn is None:
            continue
        try:
            if fn(uievent, ctx, allow_flag_click=allow_flag_click):
                return True
        except Exception:
            if _debug_enabled():
                print("[MYTOOLS][nodehook_dispatch] Error in %s.handle_ctrl_lmb\n%s" % (getattr(m, "__file__", "<module>"), traceback.format_exc()))
    return False


def ensure_on_mousedown(uievent, ctx):
    """
    Give hooks a chance to attach node-level callbacks when the user clicks a node.
    This is used to support cases where SOP event scripts don't fire (e.g. versioned op types).
    """
    try:
        if uievent.eventtype != "mousedown":
            return
        if not uievent.mousestate.lmb:
            return

        node = ctx["get_node_under_mouse"](uievent) or ctx["find_nearest_node"](uievent.editor)
        if not node or ctx["is_non_node"](node):
            return

        for m in _hooks():
            fn = getattr(m, "ensure", None)
            if fn is None:
                continue
            try:
                fn(node)
            except Exception:
                if _debug_enabled():
                    print("[MYTOOLS][nodehook_dispatch] Error in %s.ensure\n%s" % (getattr(m, "__file__", "<module>"), traceback.format_exc()))
    except Exception:
        if _debug_enabled():
            print("[MYTOOLS][nodehook_dispatch] Error in ensure_on_mousedown\n%s" % traceback.format_exc())

