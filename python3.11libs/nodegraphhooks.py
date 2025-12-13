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
from utility_ui import storeVisibleBounds

import utility_ui
import utility_generic
import utility_hotkey_system

from PySide6 import QtCore, QtWidgets, QtGui
import nodegraphbase as base
import nodegraphstates as states
from constants import CTRL_BASE_NAME, CTRL_COLOR_ACTIVE, CTRL_COLOR_INACTIVE, ENV_CTRL_NODE, ENV_CTRL_NODE_ID


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


def cycleSwitchNodeInput(node):
    if not node or not isinstance(node, hou.Node):
        return False

    node_type = node.type().name().lower()
    if 'switch' not in node_type:
        return False

    input_parm = None
    for parm_name in ('input', 'index', 'switch'):
        p = node.parm(parm_name)
        if p is not None:
            input_parm = p
            break

    if input_parm is None:
        for p in node.parms():
            try:
                if p.parmTemplate().dataType() == hou.parmData.Int:
                    n = p.name().lower()
                    if 'input' in n or 'index' in n:
                        input_parm = p
                        break
            except Exception:
                continue

    if input_parm is None:
        return False

    try:
        current_input = int(input_parm.evalAsInt())
    except Exception:
        return False

    connected = []
    for i in range(64):
        try:
            if node.input(i) is not None:
                connected.append(i)
        except IndexError:
            break
        except Exception:
            continue

    if len(connected) < 2:
        return False

    connected.sort()

    try:
        if current_input in connected:
            idx = connected.index(current_input)
            next_input = connected[(idx + 1) % len(connected)]
        else:
            next_input = connected[0]
    except Exception:
        next_input = connected[0]

    try:
        with hou.undos.group("Cycle Switch Input"):
            input_parm.set(next_input)
        return True
    except Exception:
        return False


def _maybeCycleSwitchOnCtrlLMB(uievent):
    try:
        if uievent.eventtype != 'mousedown':
            return False
        if not uievent.mousestate.lmb:
            return False

        if not uievent.modifierstate.ctrl:
            return False
        if uievent.modifierstate.shift or uievent.modifierstate.alt:
            return False

        node = None

        try:
            if hasattr(uievent, 'curitem') and isinstance(uievent.curitem, hou.Node):
                node = uievent.curitem
        except Exception:
            pass

        if node is None:
            try:
                if hasattr(uievent, 'selected') and uievent.selected and isinstance(uievent.selected.item, hou.Node):
                    node = uievent.selected.item
            except Exception:
                pass

        if node is None:
            node = findNearestNode(uievent.editor)

        if not node or _isNonNodeThing(node):
            return False

        return cycleSwitchNodeInput(node)
    except Exception:
        return False


def _maybeSetCtrlNodeOnCtrlLMB(uievent):
    try:
        if uievent.eventtype != 'mousedown':
            return False
        if not uievent.mousestate.lmb:
            return False

        if not uievent.modifierstate.ctrl:
            return False
        if uievent.modifierstate.shift or uievent.modifierstate.alt:
            return False

        node = None

        try:
            if hasattr(uievent, 'curitem') and isinstance(uievent.curitem, hou.Node):
                node = uievent.curitem
        except Exception:
            pass

        if node is None:
            try:
                if hasattr(uievent, 'selected') and uievent.selected and isinstance(uievent.selected.item, hou.Node):
                    node = uievent.selected.item
            except Exception:
                pass

        if node is None:
            node = findNearestNode(uievent.editor)

        if not node or _isNonNodeThing(node):
            return False

        if node.type().name() != "null":
            return False

        node_name = node.name()
        if not node_name.upper().startswith(CTRL_BASE_NAME.upper()):
            return False

        current_ctrl_path = hou.getenv(ENV_CTRL_NODE)
        if current_ctrl_path and node.path() == current_ctrl_path:
            return False

        try:
            node_path = node.path()
            node_session_id = str(node.sessionId())
            hou.hscript("set -g {} = {}".format(ENV_CTRL_NODE, node_path))
            hou.hscript("set -g {} = {}".format(ENV_CTRL_NODE_ID, node_session_id))
            
            for n in hou.node("/").allSubChildren():
                if n.name().startswith(CTRL_BASE_NAME) and n.path() != node_path:
                    n.setColor(CTRL_COLOR_INACTIVE)
                elif n.name().startswith(CTRL_BASE_NAME) and n.path() == node_path:
                    n.setColor(CTRL_COLOR_ACTIVE)
            
            try:
                uievent.editor.setCurrentNode(node)
                uievent.editor.update()
            except Exception:
                pass
            
            return True
        except Exception:
            return False

    except Exception:
        return False


this = sys.modules[__name__]
currentdir = os.path.dirname(os.path.realpath(__file__))

def __reload_pythonlibs(showstatus=True):
    if showstatus:
        print("Reloading hotkey system...")
    importlib.reload(this)
    importlib.reload(utility_hotkey_system)

fs_watcher = QtCore.QFileSystemWatcher()
fs_watcher.addPath(os.path.join(currentdir, "nodegraphhooks.py"))
fs_watcher.addPath(os.path.join(currentdir, "utility_hotkey_system.py"))
fs_watcher.fileChanged.connect(__reload_pythonlibs)


def createEventHandler(uievent, pending_actions):
    if not isinstance(uievent.editor, hou.NetworkEditor):
        return None, False

    ctrl_node_set = _maybeSetCtrlNodeOnCtrlLMB(uievent)
    if not ctrl_node_set:
        _maybeCycleSwitchOnCtrlLMB(uievent)

    if utility_ui.getSessionVariable("UseCustomMouseActions") and uievent.eventtype == 'mousedown':
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
                utility_ui.diveInsideNearestNode()
                return None, True
            elif uievent.modifierstate.ctrl:
                utility_ui.jumpUpOneLevel()
                return None, True

    if isinstance(uievent, KeyboardEvent):
        key = utility_generic.getUnshiftedKey(uievent.key, uievent.modifierstate)

        if hasattr(hou.session, "useVolatileSpaceToToggleNetworkEditor") and hou.session.useVolatileSpaceToToggleNetworkEditor:
            spaceKeyDown = uievent.editor.isVolatileHotkeyDown('h.pane.wsheet.view_mode')
            hou.session.spaceKeyIsDown = spaceKeyDown
            if spaceKeyDown:
                return None, True

        if uievent.eventtype == 'keyhit':
            return utility_hotkey_system.invokeActionFromKey(uievent)

    return None, False
