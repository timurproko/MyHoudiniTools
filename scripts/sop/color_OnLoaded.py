import hou
import traceback
import math


# ------------------------------------------------------------
# Config
# ------------------------------------------------------------
UI_GAMMA = 2.2          # Houdini UI gamma approximation
UI_BRIGHTNESS = 0.85    # Additional dampening to counter UI boost


# ------------------------------------------------------------
# Color conversion
# ------------------------------------------------------------
def linear_to_ui_color(rgb):
    """
    Convert linear RGB (parm color) to a node-graph-friendly color.
    """
    try:
        return hou.Color(tuple(
            pow(max(c, 0.0), 1.0 / UI_GAMMA) * UI_BRIGHTNESS
            for c in rgb
        ))
    except Exception:
        return hou.Color((0.5, 0.5, 0.5))


# ------------------------------------------------------------
# Callback
# ------------------------------------------------------------
def _on_parm_changed(**cb_kwargs):
    try:
        node = cb_kwargs.get("node")
        parm_tuple = cb_kwargs.get("parm_tuple")

        if node is None or parm_tuple is None:
            return

        if parm_tuple.name() != "color":
            return

        rgb = parm_tuple.eval()
        node.setColor(linear_to_ui_color(rgb))

    except Exception:
        print(traceback.format_exc())


# ------------------------------------------------------------
# Register callback (safe, idempotent)
# ------------------------------------------------------------
try:
    node = kwargs.get("node")
    if node is not None:
        node.addEventCallback(
            (hou.nodeEventType.ParmTupleChanged,),
            _on_parm_changed
        )
except Exception:
    print(traceback.format_exc())
