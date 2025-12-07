import hou
import traceback
def color_changed(node, event_type, **kwargs):
    parm_tuple = kwargs['parm_tuple']
    if parm_tuple is not None:
        # print(parm_tuple.name())
        if parm_tuple.name() == "color":
            # the color parm was just modified
            color = parm_tuple.eval()
            hcolor = hou.Color(color)
            try:
                node.setColor(hcolor)
            except:
                # the node is probably locked. just ignore it.
                pass
try:
    me = kwargs['node']
    if me is not None:
        # print("creating callback")
        me.addEventCallback((hou.nodeEventType.ParmTupleChanged, ), color_changed)
except:
    print(traceback.format_exc())