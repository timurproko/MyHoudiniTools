import os, hou, toolutils, time, hdefereval, re
last_index = -1


def getSelectedNode():
    if not hou.selectedNodes():
        return None
    selectedNode = hou.selectedNodes()[0]
    if selectedNode.type().category().name() != 'Vop':
        return None
    # Not do anything if the selected node is a print node
    # if selectedNode.type().name() == 'print':
    #     return None
    if selectedNode.type().name() == 'geometryvopoutput':
        return None
    return selectedNode



def isNodesExists(selectedNode):
    for node in selectedNode.parent().children():
        if node.type().name() == 'print':
            return True
    return False



def deleteNodes(selectedNode):
    if selectedNode.type().name() == 'print':
        selectedNode.destroy()
        return
    for node in selectedNode.parent().children():
        if node.type().name() == 'print':
            node.destroy()



def getNodePath():
    node = getSelectedNode()
    path = node.parent().path()
    nodePath = hou.node(path)
    return nodePath



def createPrintNode(selectedNode, outputIndex):
    vop_contexts = ['attribvop', 'popvop']
    path = getNodePath()
    if any(vop in path.path() for vop in vop_contexts):
        printNode = path.createNode('print', 'console.log')
        printNode.parm('output').set(1)
        printNode.setInput(0, selectedNode, outputIndex)
        printNode.moveToGoodPosition(relative_to_inputs=True, move_inputs=False, move_outputs=True, move_unconnected=True)



def openFile(filePath):
    home = hou.homeHoudiniDirectory()
    file = home+filePath
    os.startfile(file, 'open')



def toggle_stowbars_original(hidemainmenu=False):
    # Toggle the global "minimized stowbar" state in the UI.
    b = hou.ui.hideAllMinimizedStowbars()
    b = not b

    for p in hou.ui.panes():
        p.setShowPaneTabs(not b)
    for p in hou.ui.paneTabs():
        if p.type()!=hou.paneTabType.NetworkEditor:
            p.setShowNetworkControls(not b)

        if p.type()==hou.paneTabType.NetworkEditor:
            p.setPref('showmenu',['0','1'][not b])
        elif p.type()==hou.paneTabType.SceneViewer:
            p.showDisplayOptionsBar(not b)
            p.showOperationBar(not b)
            p.showSelectionBar(not b)
            if p.includeColorCorrectionBar():
                p.showColorCorrectionBar(not b)
            if p.includeMemoryBar():
                p.showMemoryBar(not b)
    hou.ui.curDesktop().shelfDock().show(not b)
    if hidemainmenu:
        hou.setPreference('showmenu.val',['0','1'][not b])
    hou.ui.setHideAllMinimizedStowbars(b)



def toggle_fullscreen():
    tab = hou.ui.paneTabUnderCursor()
    if tab == None or tab.type() == hou.paneTabType.NetworkEditor:
        return
    pane = hou.ui.paneUnderCursor()
    b = pane.isMaximized()
    b = not b
    pane = None
    paneTabs = hou.ui.paneTabs()
    for p in paneTabs:
        if p.type() == hou.paneTabType.SceneViewer or p.type() == hou.paneTabType.CompositorViewer or p.type() == hou.paneTabType.ChannelViewer:
            pane = p.pane()
            break
    if pane is None:
        return
    for p in paneTabs:
        if p.type() == hou.paneTabType.SceneViewer:
            p.showDisplayOptionsBar(not b)
            p.showSelectionBar(not b)
            if p.includeMemoryBar():
                p.showMemoryBar(not b)
            if p.isShowingNetworkControls():
                toggle_ui_network(0)
    pane.showPaneTabs(not b)
    pane.setIsMaximized(b)
    hou.setPreference('showmenu.val', ['0', '1'][not b])
    # toggle_shelf(0)
    toggle_stowbars(0)



def toggle_stowbars(b = -1):
    if b == -1:
        b = hou.ui.hideAllMinimizedStowbars()
        hou.ui.setHideAllMinimizedStowbars(b)
    if b == 0:
        hou.ui.setHideAllMinimizedStowbars(1)
    if b == 1:
        hou.ui.setHideAllMinimizedStowbars(0)
    else:
        return



def toggle_shelf(b = -1):
    if b == -1:
        if hou.getenv('shelf_tab_val') == '0':
            hou.ui.curDesktop().shelfDock().show(1)
            hou.hscript("set -g shelf_tab_val = '1'")
        else:
            hou.ui.curDesktop().shelfDock().show(0)
            hou.hscript("set -g shelf_tab_val = '0'")
    else:
        hou.ui.curDesktop().shelfDock().show(b)
        if b == 0:
            hou.hscript("set -g shelf_tab_val = '1'")
        if b == 1:
            hou.hscript("set -g shelf_tab_val = '0'")
        else:
            return



def toggle_menu():
    current_val = hou.getPreference('showmenu.val')
    if current_val == '0':
        hou.setPreference('showmenu.val',['0','1'][1])
    else:
        hou.setPreference('showmenu.val',['0','1'][0])



def toggle_bars():
    paneTab = hou.ui.paneTabUnderCursor()
    if paneTab:
        if paneTab.type() == hou.paneTabType.Parm:
            current_val = hou.getenv("asset_bar_val", "0")
            if current_val == '0':
                hide_asset_def_toolbar()
            else:
                show_asset_def_toolbar()

        elif paneTab.type() == hou.paneTabType.NetworkEditor:
            current_val = paneTab.getPref('showmenu')
            if current_val == '0':
                paneTab.setPref('showmenu', '1')
            elif current_val == '1':
                paneTab.setPref('showmenu', '0')

        elif paneTab.type() == hou.paneTabType.SceneViewer:
            toggle_viewport_toolbars(paneTab)


def toggle_toolbar(toolbar_name, state=-1):
    """
    Toggles the visibility of a specified toolbar in the Scene Viewer pane tab.

    :param toolbar_name: Name of the toolbar to toggle ('selection', 'operation', or 'displayOptions').
    :param state: -1 to toggle, 0 to hide, 1 to show.
    """
    pane_tab = hou.ui.paneTabUnderCursor()
    if pane_tab and pane_tab.type() == hou.paneTabType.SceneViewer:
        toggle_methods = {
            "selection": (pane_tab.isShowingSelectionBar, pane_tab.showSelectionBar),
            "operation": (pane_tab.isShowingOperationBar, pane_tab.showOperationBar),
            "displayOptions": (pane_tab.isShowingDisplayOptionsBar, pane_tab.showDisplayOptionsBar),
        }
        if toolbar_name in toggle_methods:
            current_state, toggle_method = toggle_methods[toolbar_name]
            new_state = not current_state() if state == -1 else bool(state)
            toggle_method(new_state)



def show_asset_def_toolbar():
    hou.hscript("set -g asset_bar_val = '0'")
    hou.hscript("varchange asset_bar_val")
    def asset_bar_all():
        hou.setPreference("parmdialog.asset_bar.val", "0")
    import hdefereval
    hdefereval.executeDeferred(asset_bar_all)



def show_asset_def_toolbar_when_needed():
    hou.hscript("set -g asset_bar_val = '1'")
    hou.hscript("varchange asset_bar_val")
    def asset_bar_multi():
        hou.setPreference("parmdialog.asset_bar.val", "1")
    import hdefereval
    hdefereval.executeDeferred(asset_bar_multi)



def show_asset_def_toolbar_current_def():
    hou.hscript("set -g asset_bar_val = '2'")
    hou.hscript("varchange asset_bar_val")
    def asset_bar_current():
        hou.setPreference("parmdialog.asset_bar.val", "2")
    import hdefereval
    hdefereval.executeDeferred(asset_bar_current)



def hide_asset_def_toolbar():
    hou.hscript("set -g asset_bar_val = '3'")
    hou.hscript("varchange asset_bar_val")
    def asset_bar_hide():
        hou.setPreference("parmdialog.asset_bar.val", "3")
    import hdefereval
    hdefereval.executeDeferred(asset_bar_hide)



def toggle_pin():
    paneTab = hou.ui.paneTabUnderCursor()
    if paneTab:
            if paneTab.hasNetworkControls() == True:
                    b = paneTab.isPin()
                    b = not b
                    paneTab.setPin(b)



def toggle_bg():
    paneTabs = hou.ui.curDesktop().paneTabs()
    for paneTab in paneTabs:
        if paneTab.type() == hou.paneTabType.SceneViewer:

            # Get colors from current color scheme
            sv = toolutils.sceneViewer()
            viewports = sv.viewports()
            for cv in viewports:
                st = cv.settings()
                color = st.colorScheme()
                color_name = str(color).split('.')[-1]

                # Define a dictionary of color names and their corresponding values
                color_dict = {
                    'Dark':  hou.viewportColorScheme.Dark,
                    'Grey':  hou.viewportColorScheme.Grey,
                    'Light': hou.viewportColorScheme.Light,
                }

                # Get the next color name
                next_color_name = list(color_dict.keys())[(list(color_dict.keys()).index(color_name) + 1) % len(color_dict)]

                # Set the color scheme to the next color
                st.setColorScheme(color_dict[next_color_name])



def set_display_material(intensity, dir, defmatdiff, defmatspec, defmatamb, defmatemit):
    paneTabs = hou.ui.curDesktop().paneTabs()
    for paneTab in paneTabs:
        if paneTab.type() == hou.paneTabType.SceneViewer:
            sv = toolutils.sceneViewer()
            viewports = sv.viewports()
            for cv in viewports:
                st = cv.settings()
                st.setUVMapTexture(uv)
                st.setUVMapScale(scale)
                st.setHeadlightIntensity(intensity)
                st.setHeadlightDirection(dir)
                st.setDefaultMaterialDiffuse(defmatdiff)
                st.setDefaultMaterialSpecular(defmatspec)
                st.setDefaultMaterialAmbient(defmatamb)
                st.setDefaultMaterialEmission(defmatemit)



def set_display_uv(filepath, scale):
    paneTabs = hou.ui.curDesktop().paneTabs()
    for paneTab in paneTabs:
        if paneTab.type() == hou.paneTabType.SceneViewer:
            sv = toolutils.sceneViewer()
            viewports = sv.viewports()
            for cv in viewports:
                st = cv.settings()
                st.setUVMapTexture(filepath)
                st.setUVMapScale(scale)



def set_display_matcap(filepath):
    paneTabs = hou.ui.curDesktop().paneTabs()
    for paneTab in paneTabs:
        if paneTab.type() == hou.paneTabType.SceneViewer:
            sv = toolutils.sceneViewer()
            viewports = sv.viewports()
            for cv in viewports:
                st = cv.settings()
                st.setDefaultMaterialMatCapFile(filepath)



def toggle_matcaps_in_directory(directory):
    global last_index
    exr_files = [f for f in os.listdir(directory) if f.lower().endswith('.exr')]
    exr_files.sort()

    if len(exr_files) == 0:
        print("No .exr files found in the directory.")
        return

    last_index = (last_index + 1) % len(exr_files)
    filepath = os.path.join(directory, exr_files[last_index])
    filename = os.path.basename(filepath)

    set_display_matcap(filepath)
    hou.ui.setStatusMessage(f"Matcap set to {filename}")



def preview_output():
    if not hou.selectedNodes():
        # print ("No selected node")
        return
    curnode = hou.selectedNodes()[0]
    
    if curnode.type().category().name() not in ['Sop', 'Vop', 'Dop', 'Lop', 'Chop'] or curnode.type().name() == 'subnetconnector': 
        return
    result = None
    if curnode.type().name() == 'bind' and curnode.parm("exportparm") and curnode.parm("exportparm").eval() == 1: 
        return

    if curnode.type().name() in ['mtlxstandard_surface', 'mtlxsurface']: 
        for node in curnode.parent().children():
            if node.type().name() == 'subnetconnector' and node.parm("parmtype").eval() == 24 or node.type().name() == 'mtlxsurfacematerial':
                result = node
                break

    if curnode.type().name() == 'mtlxdisplacement': 
        for node in curnode.parent().children():
            if node.type().name() == 'subnetconnector' and node.parm("parmtype").eval() == 25:
                result = node
                break
            if node.type().name() == 'mtlxsurfacematerial':
                node.setInput(1, curnode, 0)
                break

    if curnode.type().name() == 'mtlxsurfacematerial': 
        for node in curnode.parent().children():
            if node.type().name() == 'suboutput':
                result = node
                break

    if curnode.type().name() not in ['mtlxstandard_surface', 'mtlxdisplacement', 'mtlxsurfacematerial', 'mtlxsurface', 'output']:
        for node in curnode.parent().children():
            if node.type().name() == 'bind' and node.parm("exportparm") and node.parm("exportparm").eval() == 1:
                result = node
                break
            elif node.type().name() in ['geometryvopoutput', 'volumevopoutput', 'output', 'mtlxstandard_surface']:
                result = node
    
    if result:
        if result.inputConnections():
            # Disconnect the input
            for input in result.inputs():
                result.setInput(0, None)
        else:
            # Connect to curnode
            result.setNextInput(curnode, 0)



def preview_color():
    if not hou.selectedNodes():
        return
    curnode=hou.selectedNodes()[0]
    if  curnode.type().category().name()!='Vop': 
        return
    if  curnode.type().name()=='geometryvopoutput': 
        return
    result = None
    for node in curnode.parent().children():
        if node.type().name() == "redshift_material" or node.type().name() == "redshift_usd_material":
            result = node
            result.setInput(0,curnode,0)
        if node.type().name() == "mtlxstandard_surface":
            result = node
            result.setInput(1,curnode,0)
        if node.type().name() == "geometryvopoutput":
            result = node
            result.setInput(3,curnode,0)



def review_redshift():
    # Check if a node is selected
    if not hou.selectedNodes():
        print("No selected node")
        return

    # Iterate over the selected nodes
    for curnode in hou.selectedNodes():

        # Check if the selected node is a redshift_material node
        if curnode.type().name() == "redshift_material":

            # Set the node's color to orange
            curnode.setColor(hou.Color((0.99, 0.66, 0)))

            # Iterate over all nodes with the same name in the same context
            for node in curnode.parent().children():
                if node.type().name() == "redshift_material" and node != curnode:

                    # Set the color of all other redshift_material nodes to grey
                    node.setColor(hou.Color((0.8, 0.8, 0.8)))
        else:

            # Check if the selected node is a Vop node
            if not curnode or curnode.type().category().name() != 'Vop': 
                print("No Shop or Mat selected!")
                continue

            # Find the redshift_material node with the color (0.99, 0.66, 0)
            result = None
            for node in curnode.parent().children():
                if node.type().name() == "redshift_material" and node.color() == hou.Color((0.99, 0.66, 0)):
                    result = node
                    break

            # If no redshift_material node with the correct color was found,
            # find any redshift_material node and set its color to (0.99, 0.66, 0)
            if not result:
                for node in curnode.parent().children():
                    if node.type().name() == "redshift_material":
                        result = node
                        result.setColor(hou.Color((0.99, 0.66, 0)))
                        break

            # Check if a redshift_material node with the correct color was found
            if result:

                # Check the type of the selected node
                if curnode.type().name() == "redshift::Volume":

                    # Connect to pin 4 of the redshift_material node
                    result.setInput(4, curnode, 0)
                elif curnode.type().name() in ["redshift::Displacement", "redshift::DisplacementBlender"]:

                    # Connect to pin 1 of the redshift_material node
                    result.setInput(1, curnode, 0)
                elif curnode.type().name() in ["redshift::BumpMap", "redshift::NormalMap", "redshift::BumpBlender"]:

                    # Connect to pin 2 of the redshift_material node
                    result.setInput(2, curnode, 0)
                elif curnode.type().name() in ["redshift::PhysicalSky", "redshift::Environment"]:

                    # Connect to pin 2 of the redshift_material node
                    result.setInput(3, curnode, 0)
                else:

                    # Connect to pin 0 of the redshift_material node in all other cases
                    result.setInput(0, curnode, 0)
            else:
                print("No redshift_material node with the color (0.99, 0.66, 0) found")



def preview_console():
    node = getSelectedNode()
    if node is None:
        return
    if isNodesExists(node):
        deleteNodes(node)
        return
    createPrintNode(node, 0)



def preview_uv():
    selNodes = hou.selectedNodes()
    quickshade = None
    for curnode in selNodes:
            if curnode.type().name() == 'uvquickshade':
                    quickshade=curnode
                    break
    if quickshade:
            file = quickshade.parm('texture').evalAsString()
    else:
            file=hou.ui.selectFile(file_type=hou.fileType.Image)
    scene_viewer = toolutils.sceneViewer()
    vs = scene_viewer.curViewport().settings()
    vs.backgroundImage(hou.viewportBGImageView.UV, 0).setImageFile(file)



def switch_to_pane(paneType, showNetworkControls=0):
    """Switch the pane under the cursor to a specified type."""
    pane = hou.ui.paneUnderCursor()
    if pane:
        paneTab = pane.currentTab()
        if paneTab:
            try:
                paneTab.setType(paneType)
                paneTab = pane.currentTab()
                paneTab.showNetworkControls(showNetworkControls)
                paneTab.setPin(0)

                if paneTab.type() == hou.paneTabType.NetworkEditor:
                    if hasattr(paneTab, "setPref"):
                        paneTab.setPref('showmenu', '0')
                elif paneTab.type() == hou.paneTabType.SceneGraphTree:
                    paneTab.setSplitPosition(-1)

            except hou.ObjectWasDeleted:
                pass



def switch_to_pane_toggleViewers():
    """Toggle between Scene Viewer, Channel Viewer, and Compositor Viewer."""
    # Try to get the pane under the cursor
    paneTab = hou.ui.paneTabUnderCursor()

    if not paneTab:
        # Fallback to the active tab of the pane under the cursor
        pane = hou.ui.paneUnderCursor()
        if pane:
            paneTab = pane.currentTab()

    if not paneTab:
        hou.ui.displayMessage("No valid pane under cursor.")
        return

    # Define the pane types to toggle between
    pane_types = [
        hou.paneTabType.SceneViewer,
        hou.paneTabType.ChannelViewer,
        hou.paneTabType.CompositorViewer,
    ]

    # Get the current pane type
    current_type = paneTab.type()

    # Find the next pane type in the sequence
    try:
        current_index = pane_types.index(current_type)
    except ValueError:
        # If the current pane type is not in the list, default to the first
        next_type = pane_types[0]
    else:
        # Cycle to the next type
        next_type = pane_types[(current_index + 1) % len(pane_types)]

    # Switch to the next pane type
    switch_to_pane(next_type)



def switch_to_pythonPane(pythonPaneType, showNetworkControls=1):
    paneTab = hou.ui.paneTabUnderCursor()
    if paneTab:
        paneTab = paneTab.setType(hou.paneTabType.PythonPanel)
        # paneTab.setActiveInterface(hou.pypanel.interfaces()[pythonPaneType])
        paneTab.setActiveInterface(hou.pypanel.interfaceByName(pythonPaneType))
        paneTab.showNetworkControls(showNetworkControls)



def switch_to_tab(tabIndex, isDetailsView=False):
    pane = hou.ui.paneUnderCursor()
    paneTab = hou.ui.paneTabUnderCursor()

    if isDetailsView:
        # Operate on DetailsView
        if paneTab and paneTab.type() == hou.paneTabType.DetailsView:
            if tabIndex == 0:
                paneTab.setAttribType(hou.attribType.Point)
            elif tabIndex == 1:
                paneTab.setAttribType(hou.attribType.Vertex)
            elif tabIndex == 2:
                paneTab.setAttribType(hou.attribType.Prim)
            elif tabIndex == 3:
                paneTab.setAttribType(hou.attribType.Global)
    else:
        # Operate on regular tabs
        if pane:
            tabs = pane.tabs()
            if tabIndex < len(tabs):
                tabs[tabIndex].setIsCurrentTab()



def switch_next_tab(isDetailsView=False, direction=1):
    pane = hou.ui.paneUnderCursor()
    paneTab = hou.ui.paneTabUnderCursor()

    if isDetailsView:
        # Operate on DetailsView
        if paneTab and paneTab.type() == hou.paneTabType.DetailsView:
            # Cycle through attribute types in DetailsView
            current_type = paneTab.attribType()
            if current_type == hou.attribType.Point:
                next_type = hou.attribType.Vertex
            elif current_type == hou.attribType.Vertex:
                next_type = hou.attribType.Prim
            elif current_type == hou.attribType.Prim:
                next_type = hou.attribType.Global
            else:
                next_type = hou.attribType.Point
            paneTab.setAttribType(next_type)
    else:
        # Operate on regular tabs
        if pane:
            tabs = pane.tabs()
            current_tab = pane.currentTab()
            if current_tab:
                current_index = tabs.index(current_tab)
                # Compute the next index based on direction
                next_index = (current_index + direction) % len(tabs)
                tabs[next_index].setIsCurrentTab()



def change_node_color():
    sel = hou.selectedItems()
    if len(sel) <= 0:
        pass
    else:
        last_item = sel[-1]
        cl = last_item.color()
        color = hou.ui.selectColor(cl)
        try:
            import pyperclip
        except ImportError:
            pass
        else:
            rgb_color = last_item.color().rgb()
            r = "{:x}".format(int(rgb_color[0] * 255))
            g = "{:x}".format(int(rgb_color[1] * 255))
            b = "{:x}".format(int(rgb_color[2] * 255))
            hex_color = r+g+b
            hex_color = hex_color.upper()
            pyperclip.copy(hex_color)
        for item in sel:
            if color != None:
                item.setColor(color)



def setNodeAsSelected(node=None):
    if not node:
        return
    node.setSelected(True)
    editors = [pane for pane in hou.ui.paneTabs() if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab()]
    if not editors:
        return
    for pane in editors:
        if pane.linkGroup() == hou.paneLinkType.FollowSelection:
            if pane.currentNode() != node and not pane.isPin():
                pane.setCurrentNode(node)
            return
    editors[0].setCurrentNode(node)



def create_obj_merge(nodes=None, name=None):
    outprefix = 'OUT_'
    inprefix = 'IN_'
    color = hou.Color([0, 0, 0])

    if nodes is None:
        nodes = hou.selectedNodes()
    
    if not nodes:
        return
    
    if nodes[0].type().category().name() not in ['Sop']: 
        return

    for node in nodes:
        name = re.sub('[^0-9a-zA-Z\\\\.]', '_', node.name())
        o = 0

        n = node.parent().createNode('null', outprefix + re.sub('[^0-9a-zA-Z\\\\.]', '_', name), run_init_scripts=False, load_contents=True, exact_type_name=True)
        n.setUserData('nodeshape', 'circle')
        n.setInput(0, node, o)
        n.moveToGoodPosition()
        pos = n.position()
        o += 1
        setNodeAsSelected(n)

        m = node.parent().createNode('object_merge')
        relative_path = m.relativePathTo(n)
        m.setParms({'objpath1': relative_path, 'xformtype': 'none'})
        m.setPosition([pos[0], pos[1] - 1])

        n.setColor(color)
        m.setColor(color)



def set_playback_frame(frame=None):
    if not frame:
        frame = hou.playbar.frameRange()[0]
    hou.setFrame(frame)



def toggle_sim():
    mode = hou.simulationEnabled()
    if mode == 0:
            hou.setSimulationEnabled(1)
            toggle_axiom_sim(1)
            set_playback_frame()
    elif mode == 1:
            hou.setSimulationEnabled(0)
            toggle_axiom_sim(0)
            



AXIOM_SOP_TYPE = hou.nodeType(hou.sopNodeTypeCategory(), "axiom_solver::3.2")
def is_axiom_node(node):
    return node.type() == AXIOM_SOP_TYPE



def toggle_axiom_sim(value = None):
    viewer = hou.ui.curDesktop().paneTabOfType(hou.paneTabType.SceneViewer)
    pwd = viewer.pwd()

    pwds = []
    if pwd.childTypeCategory() == hou.sopNodeTypeCategory() and pwd.numItems(hou.networkItemType.Node):
        pwds = [ pwd ]
    else:
        pwds = [ pwd for pwd in hou.selectedNodes() if pwd.type().name() == "geo" and pwd.numItems(hou.networkItemType.Node) ]
    
    with hou.RedrawBlock() as rb:
        for pwd in pwds:
            for node in pwd.children()[::-1]:
                if is_axiom_node(node):
                    if value is None:
                        value = 0 if node.evalParm("enableSimulation") else 1

                    node.parm("enableSimulation").set(value)

def ctrl_select():
    ctrl_path = hou.getenv('ctrl_node')
    if not ctrl_path:
        return

    ctrl_node = hou.node(ctrl_path)
    if not ctrl_node:
        return

    ctx = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    if ctx:
        for n in ctx.pwd().children():
            n.setSelected(False)

    ctrl_node.setSelected(not ctrl_node.isSelected(), clear_all_selected=True)




def open_floating_pane(type, network = 0, pos = (), size = ()):
    paneTab = hou.ui.paneTabUnderCursor()
    paneTab = hou.ui.curDesktop().createFloatingPaneTab(type, pos, size)
    if not network:
        toggle_ui_network(paneTab, 0)



def toggle_ui_network(paneTab = None, b = -1):
    if not paneTab:
        paneTab = hou.ui.paneTabUnderCursor()
    if paneTab:
            if b == -1:
                if paneTab.hasNetworkControls() == True:
                        b = paneTab.isShowingNetworkControls()
                        b = not b
                        paneTab.showNetworkControls(b)
            if b == 0:
                paneTab.showNetworkControls(0)
            if b == 1:
                paneTab.showNetworkControls(1)



def toggle_ui_desktops():
    toggle_desktops()
    toggle_stowbars(1)
    toggle_stowbars(0)
    update_keymap()



def toggle_desktops():
        desktops_dict = {desktop.name(): desktop for desktop in hou.ui.desktops()}
        desktop_names = list(desktops_dict.keys())

        current_desktop = hou.ui.curDesktop()
        current_desktop_name = current_desktop.name()

        current_index = desktop_names.index(current_desktop_name)

        next_index = (current_index + 1) % len(desktop_names)
        next_desktop_name = desktop_names[next_index]
        desktops_dict[next_desktop_name].setAsCurrent()



def update_keymap():
    _current_desktop = hou.ui.curDesktop().name()
    _current_keymap = hou.hotkeys.currentKeymap()

    houdini_keymap = "Houdini"
    modeler_keymap = "Modeler"

    def switch_keymap(target_keymap_name):
        if _current_keymap != target_keymap_name:
            hou.hotkeys.loadKeymap(target_keymap_name)

    if "Houdini" in _current_desktop:
        switch_keymap(houdini_keymap)
    elif "Modeler" in _current_desktop:
        switch_keymap(modeler_keymap)



def open_keymap_manager():
    from hotkeys_prototype import mainwidget
    from modeler import utils

    _current_desktop = hou.ui.curDesktop().name()
    dialog = mainwidget.showHotkeyManagerWindow()
    dialog.hotkeyManager.key_pane.hide()
    HOUDINI_VERSION = hou.applicationVersionString()

    def switch_keymap_modeler():
        try:
            dialog.hotkeyManager.command_search.setText("Modeler")
        except AttributeError:
            dialog.hotkeyManager.search.setText("Modeler")

        splitter = dialog.findChild(utils.qtw.QSplitter)
        splitter.widget(0).hide()
        dialog.setWindowTitle("Modeler Hotkeys (" + utils.MODELER_VERSION + ")")

    def switch_keymap_houdini():          
        splitter = dialog.findChild(utils.qtw.QSplitter)
        splitter.widget(0).hide()
        dialog.setWindowTitle("Houdini Hotkeys (" + HOUDINI_VERSION + ")")

    if "Houdini" in _current_desktop:
        switch_keymap_houdini()
    elif "Modeler" in _current_desktop:
        switch_keymap_modeler()



def get_scene_viewer_under_cursor():
    """Helper function to get the Scene Viewer under the cursor."""
    pane = hou.ui.paneTabUnderCursor()
    if pane and pane.type() == hou.paneTabType.SceneViewer:
        return pane
    return None



def toggle_shading_mode():
    # Get the Scene Viewer under the cursor
    viewer = get_scene_viewer_under_cursor()
    if not viewer:
        hou.ui.displayMessage("No Scene Viewer under cursor.")
        return

    # Get the current viewport and its settings
    viewport = viewer.curViewport()
    settings = viewport.settings()

    # List of display sets to modify (object and geometry levels)
    display_sets = [
        settings.displaySet(hou.displaySetType.DisplayModel),  # Geometry level
        settings.displaySet(hou.displaySetType.SceneObject)   # Object level
    ]

    # Define two sets of modes to toggle between
    modes_set_1 = [
        hou.glShadingType.WireBoundingBox,
        hou.glShadingType.WireGhost,
        hou.glShadingType.HiddenLineGhost,
        hou.glShadingType.Flat,
        hou.glShadingType.Smooth,
        hou.glShadingType.MatCap
    ]

    modes_set_2 = [
        hou.glShadingType.ShadedBoundingBox,
        hou.glShadingType.Wire,
        hou.glShadingType.HiddenLineInvisible,
        hou.glShadingType.FlatWire,
        hou.glShadingType.SmoothWire,
        hou.glShadingType.MatCapWire
    ]

    # Loop through each display set and toggle shading mode
    for display_set in display_sets:
        current_mode = display_set.shadedMode()

        # Check if current mode belongs to set 1 or set 2
        if current_mode in modes_set_1:
            mode_set = modes_set_1
        elif current_mode in modes_set_2:
            mode_set = modes_set_2
        else:
            # If current mode doesn't belong to either set, default to set 1
            mode_set = modes_set_1

        # Determine the next mode in the corresponding set
        next_mode_index = (mode_set.index(current_mode) + 1) % len(mode_set)
        next_mode = mode_set[next_mode_index]

        # Set the new shading mode for the display set
        display_set.setShadedMode(next_mode)



def toggle_shading_mode_pair():
    # Get the Scene Viewer under the cursor
    viewer = get_scene_viewer_under_cursor()
    if not viewer:
        hou.ui.displayMessage("No Scene Viewer under cursor.")
        return

    # Get the current viewport and its settings
    viewport = viewer.curViewport()
    settings = viewport.settings()

    # List of display sets to modify (object and geometry levels)
    display_sets = [
        settings.displaySet(hou.displaySetType.DisplayModel),  # Geometry level
        settings.displaySet(hou.displaySetType.SceneObject)   # Object level
    ]

    # Define pairs for toggling
    shading_pairs = [
        (hou.glShadingType.WireBoundingBox, hou.glShadingType.ShadedBoundingBox),
        (hou.glShadingType.WireGhost, hou.glShadingType.Wire),
        (hou.glShadingType.HiddenLineGhost, hou.glShadingType.HiddenLineInvisible),
        (hou.glShadingType.Flat, hou.glShadingType.FlatWire),
        (hou.glShadingType.Smooth, hou.glShadingType.SmoothWire),
        (hou.glShadingType.MatCap, hou.glShadingType.MatCapWire)
    ]

    # Loop through each display set and toggle shading mode
    for display_set in display_sets:
        # Check the current shading mode
        current_mode = display_set.shadedMode()

        # Check each pair and toggle if current_mode matches one of the pair members
        for mode_a, mode_b in shading_pairs:
            if current_mode == mode_a:
                display_set.setShadedMode(mode_b)
                break
            elif current_mode == mode_b:
                display_set.setShadedMode(mode_a)
                break



def convert_hda_to_subnet():
    # Get selected nodes
    selected_nodes = hou.selectedNodes()
    
    # Check if exactly one node is selected and it's an HDA
    if len(selected_nodes) != 1:
        print("Error: Please select exactly one HDA node.")
        return
    hda_node = selected_nodes[0]
    if not hda_node.type().definition():
        print("Error: Selected node is not an HDA.")
        return
    
    try:
        # Store parent and original position
        parent = hda_node.parent()
        position = hda_node.position()
        
        # Allow editing of contents (unlock HDA)
        if not hda_node.isEditable():
            hda_node.allowEditingOfContents()
        
        # Create a new subnet to hold extracted contents
        subnet = parent.createNode("subnet", hda_node.name() + "_subnet")
        
        # Manually extract contents by copying nodes from inside the HDA
        internal_nodes = hda_node.children()
        if not internal_nodes:
            print("Warning: HDA contains no nodes to extract.")
            subnet.destroy()
            return
        
        # Record original positions and copy nodes to the subnet
        node_map = {}  # Map original nodes to their copies
        node_positions = {}  # Map original nodes to their positions
        for node in internal_nodes:
            node_positions[node] = node.position()  # Store original position
            new_node = subnet.copyItems([node])[0]
            node_map[node] = new_node
        
        # Set positions of copied nodes to match original layout
        for orig_node, new_node in node_map.items():
            if orig_node in node_positions:
                new_node.setPosition(node_positions[orig_node])
        
        # Reconnect nodes inside the subnet to preserve internal wiring
        for orig_node, new_node in node_map.items():
            for i, input_node in enumerate(orig_node.inputs()):
                if input_node in node_map:
                    new_node.setInput(i, node_map[input_node])
        
        # Copy parameter interface
        parm_templates = hda_node.parmTemplateGroup().entries()
        new_parm_group = hou.ParmTemplateGroup()
        for parm_template in parm_templates:
            new_parm_group.append(parm_template)
        subnet.setParmTemplateGroup(new_parm_group)
        
        # Match parameter values
        for parm in hda_node.parms():
            parm_name = parm.name()
            subnet_parm = subnet.parm(parm_name)
            if subnet_parm:
                try:
                    subnet_parm.set(parm.eval())
                except:
                    pass  # Skip if parameter types mismatch
        
        # Position the subnet where the HDA was
        subnet.setPosition(position)
        
        # Connect subnet to the same inputs and outputs as the HDA
        for i, input_node in enumerate(hda_node.inputs()):
            subnet.setInput(i, input_node)
        for conn in hda_node.outputConnections():
            output_node = conn.outputNode()
            input_index = conn.inputIndex()
            output_node.setInput(input_index, subnet, conn.outputIndex())
        
        # Delete the original HDA
        hda_node.destroy()
        
        # Select the new subnet
        subnet.setSelected(True)
        
        print(f"HDA '{subnet.name()}' converted to subnet successfully!")
        
    except Exception as e:
        print(f"Error converting HDA to subnet: {str(e)}")
        if subnet:
            subnet.destroy()  # Clean up if subnet was created