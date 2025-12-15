"""Dispatch system for node hooks."""
import traceback
import hou
import importlib
import pkgutil


_NODEHOOKS_CACHE_KEY = "_MYTOOLS_NODEHOOK_MODULES"


def _debug_enabled():
    try:
        return int(str(hou.getenv("MYTOOLS_DEBUG_NODEHOOKS") or "0").strip() or "0") == 1
    except Exception:
        return False


def _discover_hook_modules():
    """Discover all hook modules in nodes.nodehooks package."""
    try:
        from nodes import nodehooks
        
        modules = []
        for importer, modname, ispkg in pkgutil.iter_modules(nodehooks.__path__, nodehooks.__name__ + "."):
            if not ispkg and not modname.endswith('._utils'):
                modules.append(modname)
        
        modules.sort()
        return modules
    except ImportError:
        if _debug_enabled():
            print("[MYTOOLS][nodehook_dispatch] Could not import nodes.nodehooks")
        return []
    except Exception:
        if _debug_enabled():
            print("[MYTOOLS][nodehook_dispatch] Error discovering hooks\n%s" % traceback.format_exc())
        return []


def _load_hooks():
    """Load all hook modules."""
    hooks = []
    for module_name in _discover_hook_modules():
        try:
            m = importlib.import_module(module_name)
            hooks.append(m)
        except Exception:
            if _debug_enabled():
                print("[MYTOOLS][nodehook_dispatch] Failed loading %s\n%s" % (module_name, traceback.format_exc()))

    try:
        hooks.sort(key=lambda m: (int(getattr(m, "PRIORITY", 100)), getattr(m, "__file__", "")))
    except Exception:
        pass

    return hooks


def _hooks():
    """Get cached hooks or load them."""
    try:
        cache = getattr(hou.session, _NODEHOOKS_CACHE_KEY, None)
        if cache is None:
            cache = _load_hooks()
            setattr(hou.session, _NODEHOOKS_CACHE_KEY, cache)
        return cache
    except Exception:
        return _load_hooks()


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    """Handle Ctrl+LMB events by dispatching to registered hooks."""
    eff_ctx = ctx
    try:
        if isinstance(ctx, dict) and "is_flag_click" in ctx and callable(ctx["is_flag_click"]):
            _orig_is_flag_click = ctx["is_flag_click"]

            def _is_flag_click_wrapped(ev):
                try:
                    return (not allow_flag_click) and bool(_orig_is_flag_click(ev))
                except Exception:
                    return False

            eff_ctx = dict(ctx)
            eff_ctx["is_flag_click"] = _is_flag_click_wrapped
    except Exception:
        eff_ctx = ctx

    for m in _hooks():
        fn = getattr(m, "handle_ctrl_lmb", None)
        if fn is None:
            continue
        try:
            if fn(uievent, eff_ctx, allow_flag_click=allow_flag_click):
                return True
        except Exception:
            if _debug_enabled():
                print("[MYTOOLS][nodehook_dispatch] Error in %s.handle_ctrl_lmb\n%s" % (getattr(m, "__file__", "<module>"), traceback.format_exc()))
    return False


def ensure_on_mousedown(uievent, ctx):
    """Ensure hooks are installed on mousedown events."""
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

