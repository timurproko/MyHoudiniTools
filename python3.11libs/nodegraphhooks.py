"""
Custom Node Graph Behaviors
Handles custom mouse/keyboard interactions in the network editor
"""

import hou
import nodegraph
import sys
import os
from canvaseventtypes import *


def findNearestNode(editor):
    """Find the nearest node to the cursor position"""
    try:
        pos = editor.cursorPosition()
        currentPath = editor.pwd().path()
        
        nodes = hou.node(currentPath).children()
        nearestNode = None
        dist = 999999999.0
        
        for node in nodes:
            try:
                node_bounds = node.position()
                node_size = node.size()
                node_center = node_bounds + (node_size * 0.5)
                d = node_center.distanceTo(pos)
                if d < dist:
                    nearestNode = node
                    dist = d
            except:
                continue
        
        return nearestNode
    except:
        return None


def cycleSwitchNodeInput(node):
    if not node:
        return False
    
    node_type = node.type().name().lower()
    if 'switch' not in node_type:
        return False
    
    input_parm = None
    for parm_name in ['input', 'index', 'switch']:
        parm = node.parm(parm_name)
        if parm:
            input_parm = parm
            break
    
    if not input_parm:
        for parm in node.parms():
            try:
                if parm.parmTemplate().dataType() == hou.parmData.Int:
                    parm_name_lower = parm.name().lower()
                    if 'input' in parm_name_lower or 'index' in parm_name_lower:
                        input_parm = parm
                        break
            except:
                continue
    
    if not input_parm:
        return False
    
    try:
        current_input = input_parm.evalAsInt()
    except:
        return False
    
    connected_inputs = []
    
    for i in range(20):
        try:
            input_node = node.input(i)
            if input_node is not None:
                connected_inputs.append(i)
        except IndexError:
            continue
        except:
            continue
    
    if len(connected_inputs) < 2:
        return False
    
    connected_inputs.sort()
    
    try:
        if current_input in connected_inputs:
            current_idx = connected_inputs.index(current_input)
            next_idx = (current_idx + 1) % len(connected_inputs)
            next_input = connected_inputs[next_idx]
        else:
            next_input = connected_inputs[0]
    except:
        next_input = connected_inputs[0]
    
    try:
        with hou.undos.group("Cycle Switch Input"):
            input_parm.set(next_input)
        return True
    except:
        return False


def createEventHandler(uievent, pending_actions):
    if not isinstance(uievent.editor, hou.NetworkEditor):
        return None, False
    
    if uievent.eventtype == 'mousedown' and uievent.mousestate.lmb:
        if uievent.modifierstate.ctrl and not uievent.modifierstate.shift and not uievent.modifierstate.alt:
            node = None
            
            if hasattr(uievent, 'curitem'):
                try:
                    item = uievent.curitem
                    if isinstance(item, hou.Node):
                        node = item
                except:
                    pass
            
            if not node and hasattr(uievent, 'selected') and uievent.selected:
                try:
                    item = uievent.selected.item
                    if isinstance(item, hou.Node):
                        node = item
                except:
                    pass
            
            if not node or not isinstance(node, hou.Node):
                node = findNearestNode(uievent.editor)
            
            if (node 
                and isinstance(node, hou.Node)
                and not isinstance(node, hou.NetworkDot)
                and not isinstance(node, hou.NetworkBox)
                and not isinstance(node, hou.OpSubnetIndirectInput)
                and not isinstance(node, hou.StickyNote)):
                
                if cycleSwitchNodeInput(node):
                    return None, True
    
    return None, False


_original_createEventHandler = None
_original_handleEventCoroutine = None
_installed = False


def _installEventHandler():
    """Install our custom event handler into nodegraph module"""
    global _original_createEventHandler, _installed
    
    if _installed:
        return
    
    try:
        if hasattr(nodegraph, 'createEventHandler'):
            existing = nodegraph.createEventHandler
            
            if not (hasattr(existing, '__name__') and existing.__name__ == '_wrapped_createEventHandler'):
                _original_createEventHandler = existing
                
                def _wrapped_createEventHandler(uievent, pending_actions):
                    handler, suppress = createEventHandler(uievent, pending_actions)
                    
                    if suppress:
                        return handler, suppress
                    
                    if _original_createEventHandler:
                        try:
                            result = _original_createEventHandler(uievent, pending_actions)
                            return result
                        except Exception:
                            pass
                    
                    return handler, suppress
                
                nodegraph.createEventHandler = _wrapped_createEventHandler
                _installed = True
        else:
            nodegraph.createEventHandler = createEventHandler
            _installed = True
        
    except Exception as e:
        pass


def _uninstallEventHandler():
    global _original_createEventHandler, _installed
    
    if _original_createEventHandler and _installed:
        nodegraph.createEventHandler = _original_createEventHandler
        _installed = False


if hou.isUIAvailable():
    try:
        import hdefereval
        hdefereval.executeDeferred(_installEventHandler)
    except Exception:
        pass

