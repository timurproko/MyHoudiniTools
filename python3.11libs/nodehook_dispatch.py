import traceback
import hou
import os
import re

import hou_module_loader


_NODEHOOKS_DIR_REL = "scripts/sop/nodehooks"
_NODEHOOKS_CACHE_KEY = "_MYTOOLS_NODEHOOK_MODULES"


def _debug_enabled():
    try:
        return int(str(hou.getenv("MYTOOLS_DEBUG_NODEHOOKS") or "0").strip() or "0") == 1
    except Exception:
        return False


def _sanitize_module_suffix(name: str) -> str:
    try:
        return re.sub(r"[^0-9a-zA-Z_]+", "_", name).strip("_").lower() or "hook"
    except Exception:
        return "hook"


def _discover_hook_relpaths():
    try:
        houdini_path = hou.getenv("HOUDINI_PATH") or ""
        search_roots = []
        for part in houdini_path.split(os.pathsep):
            part = (part or "").strip()
            if not part or part == "&":
                continue
            try:
                part = hou.expandString(part)
            except Exception:
                pass
            search_roots.append(part)

        base_dirs = []
        for root in search_roots:
            try:
                candidate = os.path.join(root, _NODEHOOKS_DIR_REL)
                if os.path.isdir(candidate):
                    base_dirs.append(candidate)
            except Exception:
                continue

        if not base_dirs:
            if _debug_enabled():
                print("[MYTOOLS][nodehook_dispatch] No nodehooks dir found under HOUDINI_PATH for %s" % _NODEHOOKS_DIR_REL)
            return []

        relpaths = []
        seen = set()
        for base_dir in base_dirs:
            for fname in os.listdir(base_dir):
                if not fname.endswith(".py"):
                    continue
                if fname.startswith("_"):
                    continue
                if fname == "__init__.py":
                    continue
                rel = f"{_NODEHOOKS_DIR_REL}/{fname}"
                if rel in seen:
                    continue
                seen.add(rel)
                relpaths.append(rel)

        relpaths.sort()
        return relpaths
    except Exception:
        return []


def _load_hooks():
    hooks = []
    for rel_path in _discover_hook_relpaths():
        try:
            base = os.path.basename(rel_path)
            stem = os.path.splitext(base)[0]
            mod_name = f"_mytools_hook_{_sanitize_module_suffix(stem)}"
            m = hou_module_loader.load_from_hou_path(rel_path, mod_name)
            hooks.append(m)
        except Exception:
            if _debug_enabled():
                print("[MYTOOLS][nodehook_dispatch] Failed loading %s (%s)\n%s" % (rel_path, mod_name, traceback.format_exc()))

    try:
        hooks.sort(key=lambda m: (int(getattr(m, "PRIORITY", 100)), getattr(m, "__file__", "")))
    except Exception:
        pass

    return hooks


def _hooks():
    try:
        cache = getattr(hou.session, _NODEHOOKS_CACHE_KEY, None)
        if cache is None:
            cache = _load_hooks()
            setattr(hou.session, _NODEHOOKS_CACHE_KEY, cache)
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

