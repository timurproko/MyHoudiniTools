# Houdini Tool Development Guide

**For AI Assistants and Developers**

This guide provides best practices and patterns for writing effective, clean, and modular Python tools for Houdini. Follow these guidelines to create robust, maintainable, and performant tools that integrate seamlessly with Houdini workflows.

## Table of Contents

1. [Core Principles](#core-principles)
2. [Code Organization](#code-organization)
3. [Houdini API Best Practices](#houdini-api-best-practices)
4. [Common Patterns](#common-patterns)
5. [Error Handling & Robustness](#error-handling--robustness)
6. [Performance Considerations](#performance-considerations)
7. [API References](#api-references)

---

## Core Principles

### 1. **Modularity**
- Break functionality into small, focused functions
- Separate concerns: UI logic, node operations, data processing
- Create reusable utility functions for common operations
- Use modules to group related functionality

### 2. **Robustness**
- Always handle exceptions gracefully
- Validate inputs before operations
- Handle edge cases (deleted nodes, empty selections, etc.)
- Assume nodes/objects may be deleted at any time

### 3. **Non-Blocking Operations**
- Use deferred execution (`hdefereval`, `hou.ui.addEventLoopCallback`) for UI updates
- Don't perform long operations on the main thread
- Provide immediate feedback to users when possible

### 4. **Houdini Integration**
- Respect Houdini's undo system
- Use proper HOM (Houdini Object Model) API calls
- Follow Houdini naming conventions
- Support Houdini's session state management

---

## Code Organization

### File Structure

```
python3.11libs/
├── mytools.py              # Core utility functions
├── parms.py                # Parameter-related utilities
├── nodegraphhooks.py       # Network editor hooks
└── nodes/
    ├── constants/          # Node-specific constants
    ├── nodehooks/          # Node event handlers
    └── scripts/            # Node callback scripts
```

### Module Organization Pattern

```python
# Example: mytools.py structure
import hou
import toolutils
import hdefereval

# Module-level constants (UPPERCASE)
_DESKTOP_CACHE_KEY = "_mytools_desktop_cache"
_AXIOM_SOP_TYPE = hou.nodeType(hou.sopNodeTypeCategory(), "axiom_solver::3.2")

# Module-level state (prefixed with _)
_last_matcap_index = -1
_asset_bar_sync_cb = None

# Public utility functions
def get_desktop_by_name(name):
    """Get desktop object by name from cache."""
    # Implementation...
    pass

# Private helper functions (prefixed with _)
def _shading_mode_sets_from_pairs(pairs):
    """Extract shading mode sets from pairs."""
    return [a for (a, _b) in pairs], [b for (_a, b) in pairs]
```

### Constants Management

```python
# Use a constants module for node-specific values
# Example: nodes/constants/null.py
ENV_CTRL_NODE = "CTRL_NODE"
CTRL_BASE_NAME = "CTRL"
CTRL_COLOR_ACTIVE = (0.99, 0.66, 0)
CTRL_COLOR_INACTIVE = (0.8, 0.8, 0.8)
```

---

## Houdini API Best Practices

### Node Operations

**✅ DO:**
```python
def safe_node_operation(node):
    """Safe node operations with validation."""
    if not node or not node.isValid():
        return None
    
    try:
        # Always check if node still exists
        path = node.path()  # This will fail if node was deleted
        # Perform operation
        return node.evalParm("parmname")
    except hou.ObjectWasDeleted:
        return None
    except Exception as e:
        hou.ui.displayMessage(f"Error: {e}")
        return None
```

**❌ DON'T:**
```python
def unsafe_node_operation(node):
    """Unsafe - assumes node exists."""
    # Don't assume node persists
    value = node.evalParm("parmname")  # May fail if deleted
    node.setColor(hou.Color(1, 0, 0))  # No error handling
```

### Selection Handling

**✅ DO:**
```python
def get_selected_nodes(category=None):
    """Get selected nodes with optional category filter."""
    selected = hou.selectedNodes()
    if not selected:
        return []
    
    if category:
        return [n for n in selected if n.type().category().name() == category]
    return selected

# Usage
selected_sops = get_selected_nodes(category='Sop')
if not selected_sops:
    hou.ui.displayMessage("Please select at least one SOP node.")
    return
```

**❌ DON'T:**
```python
# Don't assume selection exists
node = hou.selectedNodes()[0]  # IndexError if empty
if node.type().category().name() == 'Sop':  # No validation
    # ...
```

### Parameter Access

**✅ DO:**
```python
def get_parm_value(node, parm_name, default=None):
    """Safely get parameter value with fallback."""
    try:
        parm = node.parm(parm_name)
        if parm:
            return parm.eval()
    except (AttributeError, hou.OperationFailed):
        pass
    return default

# Set parameters safely
def set_parm_safe(node, parm_name, value):
    """Safely set parameter value."""
    try:
        parm = node.parm(parm_name)
        if parm:
            parm.set(value)
            return True
    except (hou.OperationFailed, hou.ObjectWasDeleted):
        pass
    return False
```

### Session State Management

**✅ DO:**
```python
# Use hou.session for persistent state
_SESSION_KEY = "_mytools_cache"

def get_session_cache():
    """Get or create session cache."""
    try:
        cache = getattr(hou.session, _SESSION_KEY, None)
        if cache is None:
            cache = {}
            setattr(hou.session, _SESSION_KEY, cache)
        return cache
    except Exception:
        return {}

# Use hou.getenv/hou.putenv for environment variables
CTRL_NODE_ENV = "CTRL_NODE"

def get_ctrl_node_path():
    """Get control node path from environment."""
    return hou.getenv(CTRL_NODE_ENV) or ""
```

---

## Common Patterns

### Deferred Execution

Use when UI updates need to happen after current operation completes:

```python
import hdefereval
import mytools

def update_ui_deferred():
    """Update UI on next event loop cycle."""
    def _update():
        node = hou.selectedNodes()[0]
        node.setColor(hou.Color(1, 0, 0))
    
    # Preferred method
    try:
        hdefereval.executeDeferred(_update)
    except Exception:
        # Fallback
        mytools.defer(_update)
```

### Undo Blocking

Use `hou.RedrawBlock` and `hou.UndoGroup` for batch operations:

```python
def batch_node_operations(nodes):
    """Perform multiple operations atomically."""
    with hou.RedrawBlock() as rb:
        with hou.UndoGroup("Batch Operation"):
            for node in nodes:
                if node.isValid():
                    # Multiple operations
                    node.setColor(hou.Color(1, 0, 0))
                    node.setDisplayFlag(True)
```

### Node Creation Pattern

```python
def create_node_safe(parent, node_type, name=None, **kwargs):
    """Safely create a node with error handling."""
    try:
        node = parent.createNode(node_type, name, **kwargs)
        node.moveToGoodPosition()
        return node
    except hou.OperationFailed as e:
        hou.ui.displayMessage(f"Failed to create node: {e}")
        return None
```

### Viewport Operations

```python
def get_scene_viewer():
    """Get current scene viewer safely."""
    try:
        # Try under cursor first
        pane_tab = hou.ui.paneTabUnderCursor()
        if pane_tab and pane_tab.type() == hou.paneTabType.SceneViewer:
            return pane_tab
        
        # Fallback to any scene viewer
        return hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
    except Exception:
        return None

def update_viewport_settings(callback):
    """Update viewport settings for all scene viewers."""
    for pane_tab in hou.ui.paneTabs():
        if pane_tab.type() == hou.paneTabType.SceneViewer:
            viewport = pane_tab.curViewport()
            settings = viewport.settings()
            callback(settings)
```

### Event Loop Callbacks

```python
_callback_id = None

def start_periodic_update():
    """Start periodic UI update."""
    global _callback_id
    
    def _update():
        # Update logic
        sync_ui_state()
    
    if _callback_id is None:
        _callback_id = hou.ui.addEventLoopCallback(_update)

def stop_periodic_update():
    """Stop periodic UI update."""
    global _callback_id
    if _callback_id:
        hou.ui.removeEventLoopCallback(_callback_id)
        _callback_id = None
```

---

## Error Handling & Robustness

### Exception Handling Pattern

```python
def robust_operation(node):
    """Robust operation with comprehensive error handling."""
    try:
        # Validate input
        if not node or not node.isValid():
            return False
        
        # Check if still exists
        path = node.path()
        
        # Perform operation
        result = node.evalParm("parmname")
        return result
        
    except hou.ObjectWasDeleted:
        # Node was deleted during operation
        return None
    except hou.OperationFailed as e:
        # Houdini-specific operation failure
        print(f"Operation failed: {e}")
        return None
    except AttributeError:
        # Attribute doesn't exist
        return None
    except Exception as e:
        # Unexpected error - log but don't crash
        print(f"Unexpected error in robust_operation: {e}")
        return None
```

### Node Validation Helper

```python
def validate_node(node, required_category=None, required_type=None):
    """Validate node exists and meets requirements."""
    if not node:
        return False, "No node provided"
    
    try:
        # Check if node still exists
        _ = node.path()
    except hou.ObjectWasDeleted:
        return False, "Node was deleted"
    
    if required_category:
        if node.type().category().name() != required_category:
            return False, f"Node must be {required_category}"
    
    if required_type:
        if node.type().name() != required_type:
            return False, f"Node must be {required_type}"
    
    return True, None
```

### Safe Iteration

```python
def safe_iterate_nodes(nodes):
    """Safely iterate nodes that may be deleted."""
    valid_nodes = []
    for node in nodes:
        try:
            # Verify node still exists
            _ = node.path()
            valid_nodes.append(node)
        except hou.ObjectWasDeleted:
            continue
    
    return valid_nodes
```

---

## Performance Considerations

### Batch Operations

**✅ DO:**
```python
# Batch parameter updates
def set_multiple_parms(node, parm_dict):
    """Set multiple parameters efficiently."""
    with hou.RedrawBlock():
        for name, value in parm_dict.items():
            parm = node.parm(name)
            if parm:
                parm.set(value)
```

**❌ DON'T:**
```python
# Don't update UI for each parameter
for name, value in parm_dict.items():
    parm = node.parm(name)
    if parm:
        parm.set(value)  # Triggers UI update each time
```

### Caching

```python
_DESKTOP_CACHE = None

def get_desktop_names_cached():
    """Get desktop names with caching."""
    global _DESKTOP_CACHE
    
    if _DESKTOP_CACHE is None:
        try:
            _DESKTOP_CACHE = [d.name() for d in hou.ui.desktops()]
        except Exception:
            _DESKTOP_CACHE = []
    
    return _DESKTOP_CACHE
```

### Lazy Evaluation

```python
def get_node_type_lazy(node_type_name, category):
    """Lazy evaluation of node type."""
    cache_key = f"_node_type_{category}_{node_type_name}"
    node_type = getattr(hou.session, cache_key, None)
    
    if node_type is None:
        try:
            node_type = hou.nodeType(
                getattr(hou, f"{category.lower()}NodeTypeCategory")(),
                node_type_name
            )
            setattr(hou.session, cache_key, node_type)
        except Exception:
            return None
    
    return node_type
```

---

## API References

### Essential Houdini API Documentation

1. **HOM (Houdini Object Model) API Reference**
   - **URL**: https://www.sidefx.com/docs/houdini/hom/hou/index.html
   - **Key Modules**:
     - `hou.Node` - Node operations
     - `hou.Parm` - Parameter access
     - `hou.Geometry` - Geometry operations
     - `hou.ui` - UI operations
     - `hou.NodeType` - Node type information

2. **HScript Commands Reference**
   - **URL**: https://www.sidefx.com/docs/houdini/commands/index.html
   - **Use for**: Command-line operations, advanced system access
   - **Access via**: `hou.hscript()` function

### Commonly Used API Classes

#### Node Operations
```python
# Get nodes
hou.selectedNodes()                    # Selected nodes
hou.node("/obj/geo1")                  # Get node by path
node.children()                        # Child nodes
node.inputs()                          # Input connections
node.outputConnections()               # Output connections

# Node properties
node.path()                            # Full path
node.name()                            # Node name
node.type()                            # NodeType object
node.type().name()                     # Type name
node.type().category().name()          # Category name

# Node state
node.isValid()                         # Check if node exists
node.isDisplayFlagSet()                # Display flag
node.isRenderFlagSet()                 # Render flag
```

#### Parameter Operations
```python
# Get parameters
node.parm("parmname")                  # Get Parm object
node.parmTuple("parmname")             # Get ParmTuple
node.parms()                           # All parameters

# Parameter values
parm.eval()                            # Evaluate (with expressions)
parm.evalAsString()                    # Evaluate as string
parm.rawValue()                        # Raw value (no expressions)

# Set parameters
parm.set(value)                        # Set value
parm.setExpression(expr)               # Set expression
```

#### Geometry Operations
```python
# Get geometry
geo = node.geometry()                  # Cook and get geometry

# Iterate geometry
for prim in geo.prims():               # Primitives
    pass
for point in geo.points():             # Points
    pass
for vertex in geo.vertices():          # Vertices
    pass

# Attributes
point.attribValue("Cd")                # Get attribute
geo.pointFloatAttribValues("P")        # Get all values efficiently
```

#### UI Operations
```python
# Desktop and panes
hou.ui.curDesktop()                    # Current desktop
hou.ui.desktops()                      # All desktops
hou.ui.paneTabUnderCursor()            # Pane tab under cursor
hou.ui.paneTabOfType(type)             # Get pane by type

# Selection
hou.selectedNodes()                    # Selected nodes
node.setSelected(True)                 # Select node

# Messages
hou.ui.displayMessage("Message")       # Display message
hou.ui.statusMessage("Status")         # Status bar message
```

### Tool Script Context

When writing tool scripts (shelf tools, menu items), use the `kwargs` pattern:

```python
def tool_script(kwargs):
    """Tool script entry point."""
    # Common kwargs:
    node = kwargs.get("node")          # Current node (if any)
    nodes = kwargs.get("nodes", [])    # Selected nodes
    parms = kwargs.get("parms", [])    # Parameters (if from parm menu)
    
    # Validate context
    selected = hou.selectedNodes()
    if not selected:
        hou.ui.displayMessage("Please select a node.")
        return
    
    # Tool logic
    process_nodes(selected)
```

---

## Examples from Codebase

### Pattern: Session State with Cache

```python
# From mytools.py
_DESKTOP_CACHE_KEY = "_mytools_desktop_cache"

def build_desktop_cache():
    """Build desktop cache at startup."""
    try:
        desktops = list(hou.ui.desktops())
        desktop_map = {d.name(): d for d in desktops}
        desktop_names = list(desktop_map.keys())
        setattr(hou.session, _DESKTOP_CACHE_KEY, {
            "names": desktop_names,
            "map": desktop_map
        })
    except Exception:
        setattr(hou.session, _DESKTOP_CACHE_KEY, {"names": [], "map": {}})
```

### Pattern: Safe Deferred Execution

```python
# From mytools.py
def defer(fn):
    """Execute fn on next UI cycle safely."""
    try:
        if hasattr(hou, "ui") and hou.ui is not None:
            try:
                import hdefereval
                hdefereval.executeDeferred(fn)
                return
            except Exception:
                pass
            
            # Fallback to event loop callback
            holder = {"cb": None}
            def _cb():
                try:
                    fn()
                finally:
                    try:
                        hou.ui.removeEventLoopCallback(holder["cb"])
                    except Exception:
                        pass
            holder["cb"] = _cb
            hou.ui.addEventLoopCallback(_cb)
        else:
            fn()
    except Exception:
        pass
```

### Pattern: Node Event Handler

```python
# From nodes/scripts/null.py
def on_created(kwargs):
    """Handle node creation event."""
    try:
        constants = _load_constants()
        if constants is None:
            return
        
        node = (kwargs or {}).get("node")
        if node is None or node.type().name() != "null":
            return
        
        if not (node.name() or "").upper().startswith((constants.CTRL_BASE_NAME or "").upper()):
            return
        
        # Defer UI update
        mytools.defer(lambda: _apply_active_color(node, constants))
    except Exception:
        pass
```

---

## Checklist for New Tools

When creating a new Houdini tool, ensure:

- [ ] Input validation (nodes exist, correct type, etc.)
- [ ] Exception handling (especially `hou.ObjectWasDeleted`)
- [ ] Undo support (use `hou.UndoGroup` for batch operations)
- [ ] UI updates deferred when appropriate
- [ ] Redraw blocking for batch operations
- [ ] User feedback (status messages, error dialogs)
- [ ] Documentation (docstrings, comments for complex logic)
- [ ] Session state management (if needed)
- [ ] Performance considerations (caching, batching)
- [ ] Tested with edge cases (deleted nodes, empty selection, etc.)

---

## Additional Resources

- **Houdini Python Examples**: Check `$HFS/houdini/python3.11libs/` for official examples
- **Houdini Forums**: https://www.sidefx.com/forum/ - Community support
- **Houdini Docs**: https://www.sidefx.com/docs/ - Comprehensive documentation
- **Codebase Patterns**: Reference existing code in `python3.11libs/` and `scripts/` for established patterns

---

**Last Updated**: Based on Houdini 21.0 API
**Maintainer**: Senior Python & Houdini Technical Director

