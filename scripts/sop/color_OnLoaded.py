import hou
import traceback
def color_changed(node, event_type, **kwargs):
    parm_tuple = kwargs['parm_tuple']
    if parm_tuple is not None:
        if parm_tuple.name() == "color":
            color = parm_tuple.eval()
            hcolor = hou.Color(color)
            try:
                node.setColor(hcolor)
            except:
                pass
try:
    me = kwargs['node']
    if me is not None:
        me.addEventCallback((hou.nodeEventType.ParmTupleChanged, ), color_changed)
except:
    print(traceback.format_exc())