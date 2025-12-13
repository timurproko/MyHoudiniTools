import hou_module_loader

_null = hou_module_loader.load_from_hou_path(
    "scripts/sop/scripts/null.py",
    "_mytools_sop_null_script",
)

try:
    _null.on_created(kwargs)
except Exception:
    pass
