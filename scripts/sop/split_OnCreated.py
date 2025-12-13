import hou_module_loader

_split = hou_module_loader.load_from_hou_path(
    "scripts/sop/scripts/split.py",
    "_mytools_sop_split_script",
)

try:
    _split.ensure_installed(kwargs.get("node"))
except Exception:
    pass
