import hou


def _resolve_node(node=None, kwargs=None):
    if node is not None:
        return node
    if isinstance(kwargs, dict):
        n = kwargs.get("node")
        if n is not None:
            return n
    try:
        return hou.node(hou.pwd().path())
    except Exception:
        return None



def visualize_marker():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_marker'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName(node.name())
    vis.setLabel(node.name().title().replace("_"," "))
    vis.setParm('style', 0)
    vis.setParm('fontsize', 2)
    vis.setParm('attrib', 'P')



def visualize_color():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_color'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName(node.name())
    vis.setLabel(node.name().title().replace("_"," "))
    vis.setParm('attrib', 'N')



def visualize_tag():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_tag'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName(node.name())
    vis.setLabel(node.name().title().replace("_"," "))
    vis.setParm('textsource', 2)
    vis.setParm('placement', 2)



def visualize_points():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_marker'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('points')
    vis.setLabel('points')
    vis.setParm('style', 2)
    vis.setParm('attrib', 'P')
    vis.setParm('pointsize', '3')
    vis.setParm('markercolorr', '0')
    vis.setParm('markercolorg', '1')
    vis.setParm('markercolorb', '1')
    vis.setParm('markercolora', '1')
    vis.setParm('trailr', '0')
    vis.setParm('trailg', '1')
    vis.setParm('trailb', '1')
    vis.setParm('traila', '0.5')



def visualize_axes():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_marker'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('orient')
    vis.setLabel('orient')
    vis.setParm('style', 5)
    vis.setParm('attrib', 'orient')



def visualize_ptnum():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_marker'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('ptnum')
    vis.setLabel('ptnum')
    vis.setParm('style', 1)
    vis.setParm('class', 1)
    vis.setParm('fontsize', 3)
    vis.setParm('textcolorr', '0')
    vis.setParm('textcolorg', '1')
    vis.setParm('textcolorb', '1')



def visualize_primnum():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_marker'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('primnum')
    vis.setLabel('primnum')
    vis.setParm('style', 1)
    vis.setParm('class', 2)
    vis.setParm('fontsize', 3)
    vis.setParm('textcolorr', '0')
    vis.setParm('textcolorg', '1')
    vis.setParm('textcolorb', '1')



def visualize_vertexnum():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_marker'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('vertexnum')
    vis.setLabel('vertexnum')
    vis.setParm('style', 1)
    vis.setParm('class', 0)
    vis.setParm('fontsize', 3)
    vis.setParm('textcolorr', '0.5')
    vis.setParm('textcolorg', '0')
    vis.setParm('textcolorb', '1')



def visualize_pw():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_marker'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('point_weight')
    vis.setLabel('point_weight')
    vis.setParm('style', 0)
    vis.setParm('class', 1)
    vis.setParm('attrib', 'Pw')
    vis.setParm('fontsize', 3)
    vis.setParm('textcolorr', '0.25')
    vis.setParm('textcolorg', '0.75')
    vis.setParm('textcolorb', '0.75')



def visualize_p():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_marker'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('P')
    vis.setLabel('P')
    vis.setParm('style', 4)
    vis.setParm('attrib', 'P')
    vis.setParm('lengthscale', '1')
    vis.setParm('markercolorr', '1')
    vis.setParm('markercolorg', '1')
    vis.setParm('markercolorb', '0')
    vis.setParm('markercolora', '1')



def visualize_n():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_marker'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('N')
    vis.setLabel('N')
    vis.setParm('style', 4)
    vis.setParm('attrib', 'N')
    vis.setParm('lengthscale', '0.25')
    vis.setParm('markercolorr', '0')
    vis.setParm('markercolorg', '0')
    vis.setParm('markercolorb', '1')
    vis.setParm('markercolora', '1')



def visualize_up():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_marker'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('up')
    vis.setLabel('up')
    vis.setParm('style', 4)
    vis.setParm('attrib', 'up')
    vis.setParm('lengthscale', '0.25')
    vis.setParm('markercolorr', '1')
    vis.setParm('markercolorg', '1')
    vis.setParm('markercolorb', '0')
    vis.setParm('markercolora', '1')



def visualize_v():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_marker'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('v')
    vis.setLabel('v')
    vis.setParm('style', 3)
    vis.setParm('attrib', 'v')
    vis.setParm('lengthscale', '0.25')
    vis.setParm('normalize', 0)
    vis.setParm('markercolorr', '0')
    vis.setParm('markercolorg', '1')
    vis.setParm('markercolorb', '1')
    vis.setParm('markercolora', '1')



def visualize_uv():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_color'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('uv')
    vis.setLabel('uv')
    vis.setParm('attrib', 'uv')



def visualize_mask():
    node = hou.node(hou.pwd().path())
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_color'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('mask')
    vis.setLabel('mask')
    vis.setParm('attrib', 'mask')
    vis.setParm('colortype', 1)



def visualize_gradient(node=None, kwargs=None):
    node = _resolve_node(node=node, kwargs=kwargs)
    if node is None:
        return
    
    vis = hou.viewportVisualizers.createVisualizer(hou.viewportVisualizers.type('vis_color'), 
        hou.viewportVisualizerCategory.Node, 
        node)
    vis.setIsActive(True, None)
    vis.setIsActiveWhenTemplated(True)
    vis.setName('gradient')
    vis.setLabel('gradient')
    vis.setParm('attrib', 'gradient')
    vis.setParm('colortype', 1)
