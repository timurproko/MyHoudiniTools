import sys
import importlib.util
import hou


def load_from_hou_path(relative_path, module_name):
    path = hou.findFile(relative_path)
    if not path:
        raise ImportError("Could not resolve %s via hou.findFile" % relative_path)

    mod = sys.modules.get(module_name)
    if mod is None or getattr(mod, "__file__", None) != path:
        spec = importlib.util.spec_from_file_location(module_name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        sys.modules[module_name] = mod

    return mod


