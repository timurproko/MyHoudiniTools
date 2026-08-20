"""Hide Houdini's Network Editor center overlay text via its theme color.

Houdini uses ``GraphOverlayCenterText`` for messages such as "Empty Network"
and "Contents Not Loaded".  This patch keeps that color synchronized with the
active ``GraphBackground`` color so the shared center overlay is invisible.

Disable with ``MYTOOLS_HIDE_NETWORK_CENTER_TEXT=0``.
"""

from __future__ import annotations

import os

import hou
from hutil.PySide import QtCore, QtGui


_ENABLED_ENV = "MYTOOLS_HIDE_NETWORK_CENTER_TEXT"
_MANAGER_ATTR = "_mytools_networkeditor_overlay_color_patch"
_BACKGROUND_PROPERTY = "pluto_hcs_GraphBackground"
_TEXT_PROPERTY = "pluto_hcs_GraphOverlayCenterText"


def _env_bool(name: str, default: bool = True) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value not in {"0", "false", "False", "no", "No", "off", "Off"}


class _OverlayColorManager(QtCore.QObject):
    def __init__(self, app: QtCore.QCoreApplication):
        super().__init__(app)
        self._app = app
        self._original_text_color = app.property(_TEXT_PROPERTY)
        self._apply_queued = False
        app.installEventFilter(self)
        self.apply()

    def _background_color(self):
        color = self._app.property(_BACKGROUND_PROPERTY)
        if isinstance(color, QtGui.QColor) and color.isValid():
            return QtGui.QColor(color)

        try:
            color = hou.qt.getColor("GraphBackground")
        except Exception:
            return None
        if color is None or not color.isValid():
            return None
        return QtGui.QColor(color)

    def _queue_apply(self):
        if self._apply_queued:
            return
        self._apply_queued = True
        QtCore.QTimer.singleShot(0, self._apply_deferred)

    def _apply_deferred(self):
        self._apply_queued = False
        self.apply()

    def apply(self):
        background = self._background_color()
        if background is None:
            return

        self._app.setProperty(_TEXT_PROPERTY, background)
        for pane in hou.ui.paneTabs():
            if isinstance(pane, hou.NetworkEditor):
                try:
                    pane.redraw()
                except Exception:
                    pass

    def eventFilter(self, watched, event):
        if watched is self._app:
            event_type = event.type()
            if event_type == QtCore.QEvent.DynamicPropertyChange:
                if bytes(event.propertyName()) == _BACKGROUND_PROPERTY.encode("ascii"):
                    self._queue_apply()
            elif event_type in {
                QtCore.QEvent.ApplicationPaletteChange,
                QtCore.QEvent.StyleChange,
                QtCore.QEvent.ThemeChange,
            }:
                self._queue_apply()
        return False

    def uninstall(self):
        self._app.removeEventFilter(self)
        self._app.setProperty(_TEXT_PROPERTY, self._original_text_color)
        for pane in hou.ui.paneTabs():
            if isinstance(pane, hou.NetworkEditor):
                try:
                    pane.redraw()
                except Exception:
                    pass
        self.deleteLater()


def install():
    """Install the color synchronization once per Houdini session."""
    if not _env_bool(_ENABLED_ENV, True):
        uninstall()
        return None

    existing = getattr(hou.session, _MANAGER_ATTR, None)
    if existing is not None:
        try:
            existing.apply()
            return existing
        except RuntimeError:
            pass

    app = QtCore.QCoreApplication.instance()
    if app is None:
        return None

    manager = _OverlayColorManager(app)
    setattr(hou.session, _MANAGER_ATTR, manager)
    return manager


def uninstall():
    """Restore the previous center-overlay color and remove the patch."""
    manager = getattr(hou.session, _MANAGER_ATTR, None)
    if manager is None:
        return
    try:
        manager.uninstall()
    finally:
        try:
            delattr(hou.session, _MANAGER_ATTR)
        except AttributeError:
            pass
