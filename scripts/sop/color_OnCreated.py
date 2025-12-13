import hou_module_loader

_color = hou_module_loader.load_from_hou_path(
    "scripts/sop/scripts/color.py",
    "_mytools_sop_color_script",
)

try:
    _color.ensure_installed(kwargs.get("node"))
except Exception:
    pass