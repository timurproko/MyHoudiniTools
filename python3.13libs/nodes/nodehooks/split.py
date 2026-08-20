import hou
import traceback
from ..scripts import split as _split
from .. import nodehook_utils as _utils


def _debug_enabled():
    try:
        return int(str(hou.getenv("MYTOOLS_DEBUG_SPLIT_COLOR") or "0").strip() or "0") == 1
    except Exception:
        return False


def ensure(node):
    try:
        _split.ensure_installed(node)
    except Exception:
        if _debug_enabled():
            print(traceback.format_exc())


def _split_action(node):
    if not _split.is_split(node):
        return False
    ensure(node)
    return bool(_split.toggle_negate(node))


def handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
    return _utils.handle_ctrl_lmb_base(uievent, ctx, allow_flag_click, _split_action)


