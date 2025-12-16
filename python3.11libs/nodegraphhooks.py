from __future__ import print_function
import hou
import os
import sys
import math
import importlib
import nodegraph
import nodegraphprefs as prefs
import nodegraphutils as utils
import nodegraphview as view
from collections import defaultdict
from canvaseventtypes import *
from PySide6 import QtCore, QtWidgets, QtGui


_utility_ui = None
_utility_generic = None
_utility_hotkey_system = None
this = sys.modules[__name__]
currentdir = os.path.dirname(os.path.realpath(__file__))
fs_watcher = QtCore.QFileSystemWatcher()


try:
    import utility_ui as _utility_ui
except Exception:
    _utility_ui = None


def storeVisibleBounds(*_args, **_kwargs):
    """No-op fallback when HotkeySystem is not available."""
    try:
        if _utility_ui and hasattr(_utility_ui, "storeVisibleBounds"):
            return _utility_ui.storeVisibleBounds(*_args, **_kwargs)
    except Exception:
        pass
    return None


try:
    import utility_generic as _utility_generic
except Exception:
    _utility_generic = None

def _getUnshiftedKey_fallback(key, _modifierstate):
    return key

def _showNodeMenuNearestNodeInEditor_fallback():
    try:
        editor = hou.ui.paneTabUnderCursor()
        if not editor or editor.type() != hou.paneTabType.NetworkEditor:
            return
        n = findNearestNode(editor)
        if n:
            editor.openNodeMenu(node=n)
    except Exception:
        pass

def _selectDisplayNearestNodeInEditor_fallback(nearestNode=None):
    try:
        editor = hou.ui.paneTabUnderCursor()
        if not editor or editor.type() != hou.paneTabType.NetworkEditor:
            return
        if nearestNode is None:
            nearestNode = findNearestNode(editor)
        if nearestNode and isinstance(nearestNode, hou.Node):
            nearestNode.setSelected(True, clear_all_selected=True)
    except Exception:
        pass

class _UtilityGenericProxy(object):
    def getUnshiftedKey(self, key, modifierstate):
        if _utility_generic and hasattr(_utility_generic, "getUnshiftedKey"):
            try:
                return _utility_generic.getUnshiftedKey(key, modifierstate)
            except Exception:
                pass
        return _getUnshiftedKey_fallback(key, modifierstate)

    def showNodeMenuNearestNodeInEditor(self):
        if _utility_generic and hasattr(_utility_generic, "showNodeMenuNearestNodeInEditor"):
            try:
                return _utility_generic.showNodeMenuNearestNodeInEditor()
            except Exception:
                pass
        return _showNodeMenuNearestNodeInEditor_fallback()

    def selectDisplayNearestNodeInEditor(self, nearestNode=None):
        if _utility_generic and hasattr(_utility_generic, "selectDisplayNearestNodeInEditor"):
            try:
                return _utility_generic.selectDisplayNearestNodeInEditor(nearestNode=nearestNode)
            except Exception:
                pass
        return _selectDisplayNearestNodeInEditor_fallback(nearestNode=nearestNode)

utility_generic = _UtilityGenericProxy()


try:
    import utility_hotkey_system as _utility_hotkey_system
except Exception:
    _utility_hotkey_system = None

import nodegraphbase as base
import nodegraphstates as states
from nodes import nodehook_dispatch


class PendingAction(object):
    def __init__(self):
        self.editor_updates = utils.EditorUpdates()

    def completeAction(self, uievent):
        return False


class PendingDelayedAction(PendingAction):
    def __init__(self, editor, delay):
        PendingAction.__init__(self)
        self.timerid = editor.scheduleTimerEvent(delay)
        self.editor = editor
        self.delay = delay

    def runDelayedAction(self):
        pass

    def completeAction(self, uievent):
        if isinstance(uievent, TimerEvent):
            if uievent.timerid == self.timerid:
                self.runDelayedAction()
                return True
        return False


class PendingTextChangeAction(PendingAction):
    def __init__(self, item, valueid):
        PendingAction.__init__(self)
        self.item = item
        self.valueid = valueid

    def completeAction(self, uievent):
        if self.valueid == 0:
            return True

        if isinstance(uievent, ValueEvent):
            if uievent.valueid == self.valueid:
                if isinstance(self.item, hou.Node):
                    if uievent.value != self.item.name():
                        if uievent.value:
                            try:
                                self.item.setName(uievent.value, True)
                            except hou.OperationFailed:
                                hou.ui.displayMessage(
                                    "Can't name a node \"%s\"" % uievent.value,
                                    buttons=("OK",),
                                    severity=hou.severityType.Warning,
                                    help=(
                                        "You can only use letters, numbers, "
                                        "dots (.), dashes (-), and underscores "
                                        "(_). The name must not start with a "
                                        "dot or dash, and must contain at "
                                        "least one letter or underscore."
                                    ),
                                )
                                return False
                        else:
                            self.item.setName(self.item.type().name(), True)

                elif isinstance(self.item, hou.NetworkBox):
                    if uievent.value != self.item.comment():
                        self.item.setComment(uievent.value)

                elif isinstance(self.item, hou.StickyNote):
                    if uievent.value != self.item.text():
                        self.item.setText(uievent.value)

                return True

        elif isinstance(uievent, MouseEvent):
            if uievent.eventtype == 'mousewheel':
                uievent.editor.closeTextEditor(self.valueid, apply_changes=True)

        return False


class EventHandler(object):
    def __init__(self, start_uievent):
        self.start_uievent = start_uievent
        self.editor_updates = utils.EditorUpdates()

    def handleEvent(self, uievent, pending_actions):
        return None

    def getPrompt(self, uievent):
        return None


class ItemEventHandler(EventHandler):
    def __init__(self, start_uievent):
        EventHandler.__init__(self, start_uievent)
        self.item = start_uievent.selected.item

    def handleEvent(self, uievent, pending_actions):
        return None


def isPanEvent(uievent):
    if os.environ.get('HOUDINI_MMB_PAN', '1') == '0':
        return uievent.mousestate.rmb
    return uievent.mousestate.mmb


def areBoundsEqual(bounds1, bounds2, tolerance=1e-5):
    min1 = bounds1.min()
    max1 = bounds1.max()
    min2 = bounds2.min()
    max2 = bounds2.max()

    return (
        abs(min1.x() - min2.x()) < tolerance and
        abs(min1.y() - min2.y()) < tolerance and
        abs(max1.x() - max2.x()) < tolerance and
        abs(max1.y() - max2.y()) < tolerance
    )


class ViewPanHandler(EventHandler):
    def __init__(self, start_uievent):
        EventHandler.__init__(self, start_uievent)
        self.startbounds = start_uievent.editor.visibleBounds()
        self.olddefaultcursor = start_uievent.editor.defaultCursor()
        self.start_uievent.editor.setDefaultCursor(utils.theCursorPan)
        storeVisibleBounds(self.start_uievent.editor, operation_type='pan')

    def handleEvent(self, uievent, pending_actions):
        if uievent.eventtype == 'mousedrag':
            dist = uievent.mousestartpos - uievent.mousepos
            dist = uievent.editor.sizeFromScreen(dist)
            bounds = hou.BoundingRect(self.startbounds)
            bounds.translate(dist)
            uievent.editor.setVisibleBounds(bounds)
            return self

        elif uievent.eventtype == 'mouseup':
            self.start_uievent.editor.setDefaultCursor(self.olddefaultcursor)
            storeVisibleBounds(self.start_uievent.editor, operation_type='pan', force_store=True)
            return None

        return self


def isScaleEvent(uievent):
    if os.environ.get('HOUDINI_MMB_PAN', '1') == '0':
        return uievent.mousestate.mmb
    return uievent.mousestate.rmb


class ViewScaleHandler(EventHandler):
    def __init__(self, start_uievent):
        EventHandler.__init__(self, start_uievent)
        editor = start_uievent.editor
        self.startbounds = editor.visibleBounds()
        self.olddefaultcursor = start_uievent.editor.defaultCursor()
        self.startpos = editor.posFromScreen(start_uievent.mousepos)
        self.start_uievent.editor.setDefaultCursor(utils.theCursorScale)
        storeVisibleBounds(self.start_uievent.editor, operation_type='zoom')

    def handleEvent(self, uievent, pending_actions):
        if uievent.eventtype == 'mousedrag':
            if self.start_uievent.modifierstate.ctrl:
                endpos = uievent.mousepos
                endpos = uievent.editor.screenBounds().closestPoint(endpos)
                endpos = uievent.editor.posFromScreen(endpos)
                rect = hou.BoundingRect(self.startpos, endpos)
                pickbox = hou.NetworkShapeBox(
                    rect, hou.ui.colorFromName('GraphPickFill'), 0.3, True, False
                )
                pickboxborder = hou.NetworkShapeBox(
                    rect, hou.ui.colorFromName('GraphPickFill'), 0.8, False, False
                )
                self.editor_updates.setOverlayShapes([pickbox, pickboxborder])

            else:
                dist = uievent.mousestartpos - uievent.mousepos
                view.scaleAroundMouse(
                    uievent.editor,
                    self.startpos,
                    math.pow(utils.getScaleStep(), (dist[0] + dist[1]) / 25.0),
                    self.startbounds
                )
                return self

        elif uievent.eventtype == 'mouseup':
            if self.start_uievent.modifierstate.ctrl:
                endpos = uievent.mousepos
                endpos = uievent.editor.screenBounds().closestPoint(endpos)
                endpos = uievent.editor.posFromScreen(endpos)

                if self.startpos.x() != endpos.x() and self.startpos.y() != endpos.y():
                    rect = hou.BoundingRect(self.startpos, endpos)
                    view.createUndoQuickMark(uievent.editor)
                    uievent.editor.setVisibleBounds(
                        rect,
                        utils.getViewUpdateTime(uievent.editor),
                        utils.getDefaultScale(),
                        True
                    )

            self.start_uievent.editor.setDefaultCursor(self.olddefaultcursor)
            storeVisibleBounds(self.start_uievent.editor, operation_type='zoom', force_store=True)
            return None

        return self


class OverviewMouseHandler(EventHandler):
    def handleEvent(self, uievent, pending_actions):
        if uievent.eventtype == 'mousedrag' or uievent.eventtype == 'mousedown':
            if uievent.mousestate.lmb:
                if uievent.selected.name == 'overviewborder':
                    zeropos = hou.Vector2(0, 0)
                    mousepos = hou.Vector2(max(0, uievent.mousepos.x()),
                                           max(0, uievent.mousepos.y()))
                    screen_bounds = hou.BoundingRect(zeropos, mousepos)
                    prefs.setOverviewBounds(uievent.editor, screen_bounds)

                else:
                    new_center = uievent.editor.overviewPosFromScreen(uievent.mousepos)
                    bounds = uievent.editor.visibleBounds()
                    bounds.translate(new_center - bounds.center())
                    uievent.editor.setVisibleBounds(bounds)

                return self

            elif isPanEvent(uievent):
                handler = ViewPanHandler(uievent)
                return handler.handleEvent(uievent, pending_actions)

            elif isScaleEvent(uievent):
                handler = ViewScaleHandler(uievent)
                return handler.handleEvent(uievent, pending_actions)

        elif uievent.eventtype == 'mouseup':
            storeVisibleBounds(self.start_uievent.editor, operation_type='overview', force_store=True)
            return None

        return self


def _isNonNodeThing(x):
    return isinstance(x, (hou.NodeConnection, hou.NetworkDot, hou.NetworkBox,
                          hou.OpSubnetIndirectInput, hou.StickyNote))

def findNearestNode(editor):
    try:
        pos = editor.cursorPosition()
        currentPath = editor.pwd().path()
        nodes = hou.node(currentPath).children()

        nearest = None
        best = 1e18

        for n in nodes:
            try:
                p = n.position()
                s = n.size()
                c = p + (s * 0.5)
                d = c.distanceTo(pos)
                if d < best:
                    best = d
                    nearest = n
            except Exception:
                continue

        return nearest
    except Exception:
        return None


def __reload_pythonlibs(showstatus=True):
    if showstatus:
        print("Reloading hotkey system...")
    importlib.reload(this)
    try:
        if _utility_hotkey_system:
            importlib.reload(_utility_hotkey_system)
    except Exception:
        pass

fs_watcher.addPath(os.path.join(currentdir, "nodegraphhooks.py"))
try:
    _uhs_path = os.path.join(currentdir, "utility_hotkey_system.py")
    if os.path.exists(_uhs_path):
        fs_watcher.addPath(_uhs_path)
except Exception:
    pass
fs_watcher.fileChanged.connect(__reload_pythonlibs)

def _shouldBlockNodeFlagClickOnCtrlLMB(uievent):
    try:
        if uievent.eventtype != 'mousedown':
            return False
        if not uievent.mousestate.lmb:
            return False
        if not uievent.modifierstate.ctrl:
            return False

        sel = getattr(uievent, "selected", None)
        if not sel:
            return False

        sel_item = getattr(sel, "item", None)
        if not isinstance(sel_item, hou.Node):
            return False

        sel_name = getattr(sel, "name", None)
        if not isinstance(sel_name, str) or not sel_name:
            return False

        n = sel_name.lower()

        return "flag" in n
    except Exception:
        return False


def _getNodeUnderMouseFromUIEvent(uievent):
    try:
        if hasattr(uievent, 'curitem') and isinstance(uievent.curitem, hou.Node):
            return uievent.curitem
    except Exception:
        pass

    try:
        sel = getattr(uievent, 'selected', None)
        if sel and isinstance(getattr(sel, 'item', None), hou.Node):
            return sel.item
    except Exception:
        pass

    try:
        return findNearestNode(uievent.editor)
    except Exception:
        return None


def _toggleNodeSelection(node):
    try:
        if not node or not isinstance(node, hou.Node):
            return False
        node.setSelected(not node.isSelected(), clear_all_selected=False)
        return True
    except Exception:
        return False


def _shouldBlockDiveOnCtrlLMBDown(uievent):
    try:
        if uievent.eventtype != 'mousedown':
            return False
        if not uievent.mousestate.lmb:
            return False
        if not uievent.modifierstate.ctrl:
            return False
        if uievent.modifierstate.shift or uievent.modifierstate.alt:
            return False

        if _shouldBlockNodeFlagClickOnCtrlLMB(uievent):
            return False

        node = _getNodeUnderMouseFromUIEvent(uievent)
        if not node or _isNonNodeThing(node):
            return False

        return True
    except Exception:
        return False


def createEventHandler(uievent, pending_actions):
    if not isinstance(uievent.editor, hou.NetworkEditor):
        return None, False

    ctx = {
        "get_node_under_mouse": _getNodeUnderMouseFromUIEvent,
        "is_non_node": _isNonNodeThing,
        "is_flag_click": _shouldBlockNodeFlagClickOnCtrlLMB,
        "find_nearest_node": findNearestNode,
    }

    nodehook_dispatch.ensure_on_mousedown(uievent, ctx)

    if nodehook_dispatch.handle_ctrl_lmb(uievent, ctx, allow_flag_click=False):
        return None, True

    if _shouldBlockNodeFlagClickOnCtrlLMB(uievent):
        nodehook_dispatch.handle_ctrl_lmb(uievent, ctx, allow_flag_click=True)
        return None, True

    if _shouldBlockDiveOnCtrlLMBDown(uievent):
        return None, True


    use_custom_mouse_actions = False
    try:
        if _utility_ui and hasattr(_utility_ui, "getSessionVariable"):
            use_custom_mouse_actions = bool(_utility_ui.getSessionVariable("UseCustomMouseActions"))
    except Exception:
        use_custom_mouse_actions = False

    if use_custom_mouse_actions and uievent.eventtype == 'mousedown':
        if uievent.mousestate.rmb:
            node = uievent.selected.item
            if (
                node
                and not isinstance(node, hou.NodeConnection)
                and not isinstance(node, hou.NetworkDot)
                and not isinstance(node, hou.NetworkBox)
                and not isinstance(node, hou.OpSubnetIndirectInput)
                and not isinstance(node, hou.StickyNote)
            ):
                category = node.type().category().name()
                if category in hou.nodeTypeCategories().keys() and category != "Vop":
                    if uievent.modifierstate.alt:
                        utility_generic.showNodeMenuNearestNodeInEditor()
                    else:
                        utility_generic.selectDisplayNearestNodeInEditor(nearestNode=node)

                    return None, True

        elif uievent.mousestate.mmb:
            if uievent.modifierstate.shift:
                try:
                    if _utility_ui and hasattr(_utility_ui, "diveInsideNearestNode"):
                        _utility_ui.diveInsideNearestNode()
                        return None, True
                except Exception:
                    pass
            elif uievent.modifierstate.ctrl:
                try:
                    if _utility_ui and hasattr(_utility_ui, "jumpUpOneLevel"):
                        _utility_ui.jumpUpOneLevel()
                        return None, True
                except Exception:
                    pass

    if isinstance(uievent, KeyboardEvent):
        key = utility_generic.getUnshiftedKey(uievent.key, uievent.modifierstate)

        if hasattr(hou.session, "useVolatileSpaceToToggleNetworkEditor") and hou.session.useVolatileSpaceToToggleNetworkEditor:
            spaceKeyDown = uievent.editor.isVolatileHotkeyDown('h.pane.wsheet.view_mode')
            hou.session.spaceKeyIsDown = spaceKeyDown
            if spaceKeyDown:
                return None, True

        if uievent.eventtype == 'keyhit':
            try:
                if _utility_hotkey_system and hasattr(_utility_hotkey_system, "invokeActionFromKey"):
                    return _utility_hotkey_system.invokeActionFromKey(uievent)
            except Exception:
                pass

    return None, False
