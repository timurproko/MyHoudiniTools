"""Clear the stale Scene Viewer prompt drawn inside the viewport at startup.

Houdini 22 can initially draw the current viewer-state help at the bottom of
the viewport even when prompts are configured to use the main status bar.  A
normal UI interaction corrects the routing.  This patch only clears that stale
startup copy; later viewer-state prompts continue to behave normally.

Disable with ``MYTOOLS_CLEAR_STARTUP_VIEWPORT_PROMPT=0``.
"""

from __future__ import annotations

import os

import hou
from hutil.PySide import QtCore


_ENABLED_ENV = "MYTOOLS_CLEAR_STARTUP_VIEWPORT_PROMPT"
_INSTALLED_ATTR = "_mytools_viewport_startup_prompt_patch"


def _env_bool(name: str, default: bool = True) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value not in {"0", "false", "False", "no", "No", "off", "Off"}


def _clear_prompts() -> None:
    for pane in hou.ui.paneTabs():
        if not isinstance(pane, hou.SceneViewer):
            continue
        try:
            pane.clearPromptMessage()
            viewport = pane.curViewport()
            if viewport is not None:
                viewport.draw()
        except Exception:
            pass


def install() -> None:
    """Clear initial prompts after the desktop and viewer state initialize."""
    if not _env_bool(_ENABLED_ENV, True):
        return
    if getattr(hou.session, _INSTALLED_ATTR, False):
        return

    setattr(hou.session, _INSTALLED_ATTR, True)
    QtCore.QTimer.singleShot(0, _clear_prompts)
    QtCore.QTimer.singleShot(500, _clear_prompts)
