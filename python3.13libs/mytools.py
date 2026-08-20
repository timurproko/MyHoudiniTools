import os, hou, toolutils, re


_last_matcap_index = -1
_asset_bar_sync_cb = None
_asset_bar_sync_last = None


_DESKTOP_CACHE_KEY = "_mytools_desktop_cache"
_AXIOM_SOP_TYPE = hou.nodeType(hou.sopNodeTypeCategory(), "axiom_solver::3.2")
_BOUNDING_BOX_SHADING_PAIR = (hou.glShadingType.WireBoundingBox, hou.glShadingType.ShadedBoundingBox)
_SHADING_MODE_PAIRS = [
    (hou.glShadingType.Wire, hou.glShadingType.WireGhost),
    (hou.glShadingType.HiddenLineInvisible, hou.glShadingType.HiddenLineGhost),
    (hou.glShadingType.Flat, hou.glShadingType.FlatWire),
    (hou.glShadingType.Smooth, hou.glShadingType.SmoothWire),
    (hou.glShadingType.MatCap, hou.glShadingType.MatCapWire),
]


def _scene_viewer_viewports():
    try:
        return toolutils.sceneViewer().viewports()
    except Exception:
        return []


def _build_desktop_cache_lazy():
    try:
        cache = getattr(hou.session, _DESKTOP_CACHE_KEY, None)
        if cache and cache.get("names") and cache.get("map"):
            return cache
    except Exception:
        pass

    try:
        desktops = list(hou.ui.desktops())
        desktop_map = {d.name(): d for d in desktops}
        desktop_names = list(desktop_map.keys())
        cache = {
            "names": desktop_names,
            "map": desktop_map
        }
        setattr(hou.session, _DESKTOP_CACHE_KEY, cache)
        return cache
    except Exception:
        cache = {"names": [], "map": {}}
        setattr(hou.session, _DESKTOP_CACHE_KEY, cache)
        return cache


def build_desktop_cache():
    _build_desktop_cache_lazy()


def get_desktop_names():
    cache = _build_desktop_cache_lazy()
    return cache.get("names", [])


def get_desktop_by_name(name):
    cache = _build_desktop_cache_lazy()
    return cache.get("map", {}).get(name)


def encode_rgb(rgb):
    return ",".join(str(float(x)) for x in rgb[:3])


def decode_rgb(s):
    parts = [p.strip() for p in (s or "").split(",")]
    if len(parts) < 3:
        raise ValueError("Invalid rgb string")
    return (float(parts[0]), float(parts[1]), float(parts[2]))


def find_folders_recursive(entry, found_folders, target_names=None, target_labels=None):
    if target_names is None:
        target_names = []
    if target_labels is None:
        target_labels = []

    if isinstance(entry, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
        entry_name = entry.name()
        entry_label = (entry.label() or "").lower()

        matches = False
        if target_names:
            for target_name in target_names:
                if entry_name.startswith(target_name) or entry_name == target_name:
                    matches = True
                    break
        if not matches and target_labels:
            for target_label in target_labels:
                if target_label in entry_label:
                    matches = True
                    break

        if matches:
            found_folders.append(entry)

        for sub_entry in entry.parmTemplates():
            find_folders_recursive(sub_entry, found_folders, target_names, target_labels)


def remove_c_like_comments(text):
    def replacer(match):
        s = match.group(0)
        if s.startswith("/"):
            return " "
        return s

    pattern = re.compile(
        r"//.*?$|/\*.*?\*/|\'(?:\\\\.|[^\\\\\'])*\'|\"(?:\\\\.|[^\\\\\"])*\"",
        re.DOTALL | re.MULTILINE,
    )
    return re.sub(pattern, replacer, text)


def session_set(key):
    try:
        reg = getattr(hou.session, key, None)
        if isinstance(reg, set):
            return reg
        reg = set()
        setattr(hou.session, key, reg)
        return reg
    except Exception:
        return set()


def defer(fn):
    try:
        if hasattr(hou, "ui") and hou.ui is not None:
            try:
                import hdefereval
                hdefereval.executeDeferred(fn)
                return
            except Exception:
                pass

            holder = {"cb": None}

            def deferred_callback():
                try:
                    fn()
                finally:
                    try:
                        hou.ui.removeEventLoopCallback(holder["cb"])
                    except Exception:
                        pass

            holder["cb"] = deferred_callback
            hou.ui.addEventLoopCallback(deferred_callback)
        else:
            fn()
    except Exception:
        pass


def set_node_color(node, color):
    try:
        if isinstance(color, hou.Color):
            node.setColor(color)
        else:
            node.setColor(hou.Color(color))
    except Exception:
        pass


def getSelectedNode():
    if not hou.selectedNodes():
        return None
    selectedNode = hou.selectedNodes()[0]
    if selectedNode.type().category().name() != 'Vop':
        return None
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


def package_folder():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))


def package_file(filePath):
    filePath = hou.text.expandString(str(filePath))
    normalized = filePath.replace("\\", "/")
    package_name = os.path.basename(package_folder())
    package_prefix = f"/packages/{package_name}/"
    package_index = normalized.lower().find(package_prefix.lower())
    if package_index != -1:
        filePath = normalized[package_index + len(package_prefix):]

    if os.path.isabs(filePath):
        return filePath

    return os.path.join(package_folder(), filePath)


def openFile(filePath):
    os.startfile(package_file(filePath), 'open')


def toggle_stowbars_original(hidemainmenu=False):
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
            current_val = get_asset_def_toolbar_state()
            if current_val == '0':
                set_asset_def_toolbar_state("3")
            else:
                set_asset_def_toolbar_state("0")

        elif paneTab.type() == hou.paneTabType.NetworkEditor:
            current_val = paneTab.getPref('showmenu')
            if current_val == '0':
                paneTab.setPref('showmenu', '1')
            elif current_val == '1':
                paneTab.setPref('showmenu', '0')

        elif paneTab.type() == hou.paneTabType.SceneViewer:
            toggle_viewport_toolbars(paneTab)


def toggle_toolbar(toolbar_name, state=-1):
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


def get_asset_def_toolbar_state():
    state = hou.getPreference('parmdialog.asset_bar.val')

    if state is None or state == '':
        state = '1'
        hou.setPreference('parmdialog.asset_bar.val', state)

    return str(state).strip()


def sync_asset_bar_menu_global(force: bool = False):
    global _asset_bar_sync_last

    try:
        state = get_asset_def_toolbar_state()
        current_global = None
        try:
            out, _err = hou.hscript("echo $asset_bar_val")
            current_global = (out or "").strip()
        except Exception:
            current_global = None

        if (not force) and (_asset_bar_sync_last == state) and (current_global == str(state)):
            return

        hou.hscript("set -g asset_bar_val = '" + str(state) + "'")
        hou.hscript("varchange asset_bar_val")
        _asset_bar_sync_last = state
    except Exception:
        pass


def start_asset_bar_menu_sync():
    global _asset_bar_sync_cb
    if _asset_bar_sync_cb is not None:
        return

    sync_asset_bar_menu_global(force=True)

    def asset_bar_callback():
        sync_asset_bar_menu_global(force=False)

    _asset_bar_sync_cb = asset_bar_callback
    try:
        hou.ui.addEventLoopCallback(asset_bar_callback)
    except Exception:
        _asset_bar_sync_cb = None


def init_asset_bar_menu_sync(force: bool = False):
    get_asset_def_toolbar_state()
    start_asset_bar_menu_sync()
    if force:
        sync_asset_bar_menu_global(force=True)


def set_asset_def_toolbar_state(state):
    s = str(int(state)) if isinstance(state, (int, float)) else str(state).strip()
    if s not in ("0", "1", "2", "3"):
        raise ValueError("asset def toolbar state must be 0,1,2,3")
    hou.setPreference("parmdialog.asset_bar.val", s)
    sync_asset_bar_menu_global(force=True)


def toggle_pin():
    paneTab = hou.ui.paneTabUnderCursor()
    if paneTab and paneTab.hasNetworkControls():
        paneTab.setPin(not paneTab.isPin())


def toggle_bg():
    color_dict = {
        'Dark': hou.viewportColorScheme.Dark,
        'Grey': hou.viewportColorScheme.Grey,
        'Light': hou.viewportColorScheme.Light,
    }
    color_names = list(color_dict.keys())

    for viewport in _scene_viewer_viewports():
        settings = viewport.settings()
        color_name = str(settings.colorScheme()).split('.')[-1]
        if color_name not in color_dict:
            color_name = color_names[0]
        next_color_name = color_names[(color_names.index(color_name) + 1) % len(color_names)]
        settings.setColorScheme(color_dict[next_color_name])


def set_display_material(intensity, dir, defmatdiff, defmatspec, defmatamb, defmatemit, filepath=None, scale=None):
    for viewport in _scene_viewer_viewports():
        settings = viewport.settings()
        if filepath is not None:
            settings.setUVMapTexture(filepath)
        if scale is not None:
            settings.setUVMapScale(scale)
        settings.setHeadlightIntensity(intensity)
        settings.setHeadlightDirection(dir)
        settings.setDefaultMaterialDiffuse(defmatdiff)
        settings.setDefaultMaterialSpecular(defmatspec)
        settings.setDefaultMaterialAmbient(defmatamb)
        settings.setDefaultMaterialEmission(defmatemit)


def set_display_uv(filepath, scale):
    for viewport in _scene_viewer_viewports():
        settings = viewport.settings()
        settings.setUVMapTexture(filepath)
        settings.setUVMapScale(scale)


def set_display_matcap(filepath):
    for viewport in _scene_viewer_viewports():
        viewport.settings().setDefaultMaterialMatCapFile(filepath)


def _is_matcap_shading_active():
    matcap_modes = (hou.glShadingType.MatCap, hou.glShadingType.MatCapWire)

    for viewport in _scene_viewer_viewports():
        settings = viewport.settings()
        display_sets = [
            settings.displaySet(hou.displaySetType.DisplayModel),
            settings.displaySet(hou.displaySetType.SceneObject)
        ]
        if any(display_set.shadedMode() in matcap_modes for display_set in display_sets):
            return True

    return False


def toggle_matcaps_in_directory(directory):
    global _last_matcap_index
    if not _is_matcap_shading_active():
        return

    directory = package_file(directory)
    if not os.path.isdir(directory):
        print(f"Matcap directory not found: {directory}")
        return
    exr_files = [f for f in os.listdir(directory) if f.lower().endswith('.exr')]
    exr_files.sort()

    if len(exr_files) == 0:
        print("No .exr files found in the directory.")
        return

    _last_matcap_index = (_last_matcap_index + 1) % len(exr_files)
    filepath = os.path.join(directory, exr_files[_last_matcap_index])
    filename = os.path.basename(filepath)

    set_display_matcap(filepath)
    hou.ui.setStatusMessage(f"Matcap set to {filename}")


def preview_output():
    if not hou.selectedNodes():
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
            for input in result.inputs():
                result.setInput(0, None)
        else:
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
    if not hou.selectedNodes():
        print("No selected node")
        return

    for curnode in hou.selectedNodes():

        if curnode.type().name() == "redshift_material":

            curnode.setColor(hou.Color((0.99, 0.66, 0)))

            for node in curnode.parent().children():
                if node.type().name() == "redshift_material" and node != curnode:

                    node.setColor(hou.Color((0.8, 0.8, 0.8)))
        else:

            if not curnode or curnode.type().category().name() != 'Vop':
                print("No Shop or Mat selected!")
                continue

            result = None
            for node in curnode.parent().children():
                if node.type().name() == "redshift_material" and node.color() == hou.Color((0.99, 0.66, 0)):
                    result = node
                    break

            if not result:
                for node in curnode.parent().children():
                    if node.type().name() == "redshift_material":
                        result = node
                        result.setColor(hou.Color((0.99, 0.66, 0)))
                        break

            if result:

                if curnode.type().name() == "redshift::Volume":

                    result.setInput(4, curnode, 0)
                elif curnode.type().name() in ["redshift::Displacement", "redshift::DisplacementBlender"]:

                    result.setInput(1, curnode, 0)
                elif curnode.type().name() in ["redshift::BumpMap", "redshift::NormalMap", "redshift::BumpBlender"]:

                    result.setInput(2, curnode, 0)
                elif curnode.type().name() in ["redshift::PhysicalSky", "redshift::Environment"]:

                    result.setInput(3, curnode, 0)
                else:

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
    quickshade = None
    for curnode in hou.selectedNodes():
        if curnode.type().name() == 'uvquickshade':
            quickshade = curnode
            break
    if quickshade:
        file = quickshade.parm('texture').evalAsString()
    else:
        file = hou.ui.selectFile(file_type=hou.fileType.Image)
    scene_viewer = toolutils.sceneViewer()
    settings = scene_viewer.curViewport().settings()
    settings.backgroundImage(hou.viewportBGImageView.UV, 0).setImageFile(file)


def switch_to_pane(paneType, showNetworkControls=0):
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
    paneTab = hou.ui.paneTabUnderCursor()

    if not paneTab:
        pane = hou.ui.paneUnderCursor()
        if pane:
            paneTab = pane.currentTab()

    if not paneTab:
        hou.ui.displayMessage("No valid pane under cursor.")
        return

    pane_types = [
        hou.paneTabType.SceneViewer,
        hou.paneTabType.ChannelViewer,
        hou.paneTabType.CompositorViewer,
    ]

    current_type = paneTab.type()

    try:
        current_index = pane_types.index(current_type)
    except ValueError:
        next_type = pane_types[0]
    else:
        next_type = pane_types[(current_index + 1) % len(pane_types)]
    switch_to_pane(next_type)


def switch_to_pythonPane(pythonPaneType, showNetworkControls=1):
    paneTab = hou.ui.paneTabUnderCursor()
    if paneTab:
        paneTab = paneTab.setType(hou.paneTabType.PythonPanel)
        paneTab.setActiveInterface(hou.pypanel.interfaceByName(pythonPaneType))


def select_parameter_tab(node, tab_index=0):
    try:
        if node is None:
            return

        ptg = node.parmTemplateGroup()
        if ptg is None:
            return

        def walk(folder):
            for pt in folder.parmTemplates():
                if isinstance(pt, hou.FolderParmTemplate) and pt.folderType() == hou.folderType.Tabs:
                    name = pt.name()
                    return name if name else None
                if isinstance(pt, hou.FolderParmTemplate):
                    r = walk(pt)
                    if r:
                        return r
            return None

        tabs_name = walk(ptg)
        if not tabs_name:
            return

        pt = node.parmTuple(tabs_name)
        if pt is None:
            return

        pt.set((tab_index,))
    except Exception:
        pass


def switch_to_tab(tabIndex, isDetailsView=False):
    pane = hou.ui.paneUnderCursor()
    paneTab = hou.ui.paneTabUnderCursor()

    if isDetailsView:
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
        if pane:
            tabs = pane.tabs()
            if tabIndex < len(tabs):
                tabs[tabIndex].setIsCurrentTab()


def switch_next_tab(isDetailsView=False, direction=1):
    pane = hou.ui.paneUnderCursor()
    paneTab = hou.ui.paneTabUnderCursor()

    if isDetailsView:
        if paneTab and paneTab.type() == hou.paneTabType.DetailsView:
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
        if pane:
            tabs = pane.tabs()
            current_tab = pane.currentTab()
            if current_tab:
                current_index = tabs.index(current_tab)
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


def _active_network_editor():
    """Return the current Network Editor without changing pane focus."""
    pane = hou.ui.paneTabUnderCursor()
    if isinstance(pane, hou.NetworkEditor):
        return pane

    editors = [
        tab for tab in hou.ui.paneTabs()
        if isinstance(tab, hou.NetworkEditor) and tab.isCurrentTab()
    ]
    if editors:
        return editors[0]

    return hou.ui.curDesktop().paneTabOfType(hou.paneTabType.NetworkEditor)


def _layout_graph(nodes, horizontal_spacing=1.0, vertical_spacing=1.0):
    """Use Houdini's compact layout per chunk without globally shuffling it.

    Each connected operation chunk gets the same internal placement as vanilla
    ``layoutChildren``. The custom pass preserves the artist's horizontal rows,
    left-aligns those rows, and removes overlap without flattening every chunk.
    """
    nodes = list(dict.fromkeys(nodes))
    node_set = set(nodes)
    if not nodes:
        return 0, 0, 0

    parent = nodes[0].parent()
    nodes = [node for node in nodes if node.parent() == parent]
    node_set = set(nodes)
    original = {
        node: hou.Vector2(node.position())
        for node in nodes
    }
    predecessors = {node: set() for node in nodes}
    successors = {node: set() for node in nodes}

    for node in nodes:
        for connection in node.inputConnections():
            upstream = connection.inputNode()
            if upstream in node_set and upstream is not node:
                predecessors[node].add(upstream)
                successors[upstream].add(node)

    components = []
    unseen = set(nodes)
    while unseen:
        seed = min(unseen, key=lambda item: (original[item][0], -original[item][1], item.path()))
        stack = [seed]
        unseen.remove(seed)
        component = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbour in sorted(predecessors[node] | successors[node], key=lambda item: item.path()):
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    stack.append(neighbour)
        components.append(component)

    components.sort(key=lambda chunk: (
        sum(original[node][0] for node in chunk) / len(chunk),
        min(node.path() for node in chunk),
    ))

    layouts = []
    skipped_cycles = 0

    for component in components:
        component_set = set(component)
        indegree = {
            node: len(predecessors[node] & component_set)
            for node in component
        }
        ready = [node for node in component if indegree[node] == 0]
        visited = []
        while ready:
            node = ready.pop()
            visited.append(node)
            for downstream in successors[node] & component_set:
                indegree[downstream] -= 1
                if indegree[downstream] == 0:
                    ready.append(downstream)

        # Native layout can radically reshape feedback networks, so retain the
        # safety rule from the previous algorithm and leave cycles untouched.
        if len(visited) != len(component):
            skipped_cycles += 1
            continue

        terminals = [node for node in component if not (successors[node] & component_set)]
        original_center_x = sum(original[node][0] for node in component) / len(component)

        try:
            # Negative spacing asks Houdini to use its compact vanilla defaults.
            parent.layoutChildren(
                items=tuple(component),
                horizontal_spacing=-1.0,
                vertical_spacing=-1.0,
            )
        except Exception:
            for node in component:
                node.setPosition(original[node])
            skipped_cycles += 1
            continue

        vanilla_center_x = sum(node.position()[0] for node in component) / len(component)
        x_restore = original_center_x - vanilla_center_x
        target = {
            node: hou.Vector2(node.position()[0] + x_restore, node.position()[1])
            for node in component
        }

        # Vanilla can choose either output branch as the vertical continuation,
        # causing symmetric Split-style graphs to flip on repeated layouts.
        # Canonicalize every fork: output 0 stays under its parent and later
        # outputs are packed to the right in connector order.
        branching_nodes = sorted(
            (node for node in component if len(successors[node] & component_set) > 1),
            key=lambda node: (-target[node][1], node.path()),
        )
        for branch_node in branching_nodes:
            ordered_roots = []
            seen_roots = set()
            connections = sorted(
                (
                    connection for connection in branch_node.outputConnections()
                    if connection.outputNode() in component_set
                ),
                key=lambda connection: (
                    connection.outputIndex(),
                    connection.inputIndex(),
                    connection.outputNode().path(),
                ),
            )
            for connection in connections:
                root = connection.outputNode()
                if root not in seen_roots:
                    seen_roots.add(root)
                    ordered_roots.append(root)
            if len(ordered_roots) < 2:
                continue

            reachable = {}
            membership = {node: 0 for node in component}
            for root in ordered_roots:
                found = set()
                stack = [root]
                while stack:
                    current = stack.pop()
                    if current in found:
                        continue
                    found.add(current)
                    stack.extend(successors[current] & component_set)
                reachable[root] = found
                for current in found:
                    membership[current] += 1

            exclusive = {
                root: {node for node in reachable[root] if membership[node] == 1}
                for root in ordered_roots
            }
            # Match vanilla's inter-column spacing for fork branches too. The
            # previous one-tile gap made Split outputs visibly tighter than
            # separately packed chunks.
            branch_gap = float(branch_node.size()[0]) * 1.875 * horizontal_spacing
            previous_right = None
            for index, root in enumerate(ordered_roots):
                branch_nodes = exclusive[root] or {root}
                if index == 0:
                    delta_x = target[branch_node][0] - target[root][0]
                else:
                    branch_left = min(target[node][0] for node in branch_nodes)
                    delta_x = previous_right + branch_gap - branch_left
                for node in branch_nodes:
                    target[node] = hou.Vector2(target[node][0] + delta_x, target[node][1])
                previous_right = max(
                    target[node][0] + float(node.size()[0])
                    for node in branch_nodes
                )

        # Branch canonicalization may widen toward the right. Re-center the
        # complete chunk on its pre-layout X so repeated runs are idempotent.
        canonical_center_x = sum(target[node][0] for node in component) / len(component)
        canonical_restore_x = original_center_x - canonical_center_x
        for node in component:
            target[node] = hou.Vector2(
                target[node][0] + canonical_restore_x,
                target[node][1],
            )

        terminal_floor = min(target[node][1] for node in terminals)
        layouts.append({
            "component": component,
            "terminals": terminals,
            "target": target,
            "terminal_floor": terminal_floor,
            "original_center_x": original_center_x,
            "original_terminal_y": sum(original[node][1] for node in terminals) / len(terminals),
        })

    if not layouts:
        return 0, len(components), skipped_cycles

    # Houdini's whole-network layout leaves 1.875 standard tile widths between
    # disconnected components. Derive that gap from the live tile size so this
    # matches vanilla across network types and UI scales.
    tile_widths = sorted(float(node.size()[0]) for node in nodes)
    middle = len(tile_widths) // 2
    if len(tile_widths) % 2:
        standard_tile_width = tile_widths[middle]
    else:
        standard_tile_width = (tile_widths[middle - 1] + tile_widths[middle]) * 0.5
    tile_gap = standard_tile_width * 1.875 * horizontal_spacing

    # Detect the artist's existing horizontal rows from output-node heights.
    # Differences smaller than one full vanilla gap are normal hand-placement
    # noise, not a new row. Truly packed rows remain farther apart because the
    # row gap is measured between their complete bounding boxes.
    row_tolerance = tile_gap
    rows = []
    for layout in sorted(
        layouts,
        key=lambda item: (-item["original_terminal_y"], item["original_center_x"]),
    ):
        if not rows or abs(layout["original_terminal_y"] - rows[-1]["reference_y"]) > row_tolerance:
            rows.append({
                "reference_y": layout["original_terminal_y"],
                "layouts": [layout],
            })
        else:
            rows[-1]["layouts"].append(layout)
            values = [item["original_terminal_y"] for item in rows[-1]["layouts"]]
            rows[-1]["reference_y"] = sum(values) / len(values)

    # Keep every row at its existing height, align all rows to one common left
    # edge, and use the exact vanilla component gap inside each row.
    common_left = min(
        original[node][0]
        for layout in layouts
        for node in layout["component"]
    )
    previous_row_bottom = None
    for row in rows:
        row_layouts = sorted(row["layouts"], key=lambda item: item["original_center_x"])
        baseline_y = max(item["original_terminal_y"] for item in row_layouts)
        previous_right = None
        for layout in row_layouts:
            y_shift = baseline_y - layout["terminal_floor"]
            for node in layout["component"]:
                layout["target"][node][1] += y_shift
            for terminal in layout["terminals"]:
                layout["target"][terminal][1] = baseline_y

            left = min(layout["target"][node][0] for node in layout["component"])
            right = max(
                layout["target"][node][0] + float(node.size()[0])
                for node in layout["component"]
            )
            desired_left = common_left if previous_right is None else previous_right + tile_gap
            layout["shift_x"] = desired_left - left
            previous_right = right + layout["shift_x"]

        # Use the same edge-to-edge gap vertically as horizontally. Keep the
        # top row anchored and pack each following row downward without merging
        # its chunks into the row above.
        row_top = max(
            layout["target"][node][1] + float(node.size()[1])
            for layout in row_layouts
            for node in layout["component"]
        )
        row_bottom = min(
            layout["target"][node][1]
            for layout in row_layouts
            for node in layout["component"]
        )
        row_shift_y = (
            0.0
            if previous_row_bottom is None
            else previous_row_bottom - tile_gap - row_top
        )
        if row_shift_y:
            for layout in row_layouts:
                for node in layout["component"]:
                    layout["target"][node][1] += row_shift_y
        previous_row_bottom = row_bottom + row_shift_y

    moved = 0
    for layout in layouts:
        for node in layout["component"]:
            final_position = hou.Vector2(
                layout["target"][node][0] + layout["shift_x"],
                layout["target"][node][1],
            )
            node.setPosition(final_position)
            if (final_position - original[node]).length() > 1e-6:
                moved += 1

    return moved, len(components), skipped_cycles


def _layout_network_nodes(selected_only=False):
    editor = _active_network_editor()
    if editor is None:
        hou.ui.displayMessage("No Network Editor is available.")
        return

    parent = editor.pwd()
    if selected_only:
        nodes = [node for node in hou.selectedNodes() if node.parent() == parent]
        if not nodes:
            hou.ui.setStatusMessage("Lay Out Selected: no nodes selected.", severity=hou.severityType.Warning)
            return
        undo_label = "Lay Out Selected (Preserve Chunks)"
    else:
        nodes = list(parent.children())
        if not nodes:
            hou.ui.setStatusMessage("Lay Out: network is empty.")
            return
        undo_label = "Lay Out (Preserve Chunks)"

    with hou.undos.group(undo_label):
        moved, component_count, skipped_cycles = _layout_graph(nodes)

    message = f"{undo_label}: moved {moved} node(s) in {component_count} chunk(s)"
    if skipped_cycles:
        message += f"; preserved {skipped_cycles} cyclic chunk(s)"
    hou.ui.setStatusMessage(message + ".")


def layout_network_preserve_chunks():
    """Tidy all nodes in the current network without repacking chunks."""
    _layout_network_nodes(selected_only=False)


def layout_selected_preserve_chunks():
    """Tidy selected nodes in place, leaving every other node untouched."""
    _layout_network_nodes(selected_only=True)


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



def is_axiom_node(node):
    return node.type() == _AXIOM_SOP_TYPE


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
    ctrl_path = hou.getenv('CTRL_NODE')
    if not ctrl_path:
        return

    ctrl_node = hou.node(ctrl_path)
    if not ctrl_node:
        return

    ctx = hou.ui.paneTabOfType(hou.paneTabType.NetworkEditor)
    if not ctx:
        return

    selected_nodes = [n for n in hou.selectedNodes() if n != ctrl_node]

    if ctrl_node.isSelected():
        if selected_nodes:
            ctrl_node.setSelected(False)
    elif selected_nodes:
        ctrl_node.setSelected(True)
    else:
        for n in ctx.pwd().children():
            n.setSelected(False)
        ctrl_node.setSelected(True, clear_all_selected=True)


def open_floating_pane(type, network=0, pos=(), size=()):
    paneTab = hou.ui.curDesktop().createFloatingPaneTab(type, pos, size)
    if not network:
        toggle_ui_network(paneTab, 0)


def toggle_ui_network(paneTab = None, b = -1):
    if not paneTab:
        paneTab = hou.ui.paneTabUnderCursor()
    if not paneTab:
        return
    if b == -1:
        if paneTab.hasNetworkControls():
            paneTab.showNetworkControls(not paneTab.isShowingNetworkControls())
    elif b == 0:
        paneTab.showNetworkControls(0)
    elif b == 1:
        paneTab.showNetworkControls(1)


def toggle_ui_desktops():
    toggle_desktops()
    toggle_stowbars(1)
    toggle_stowbars(0)
    update_keymap()


def toggle_desktops():
    try:
        cache = _build_desktop_cache_lazy()
        desktop_names = cache.get("names", [])
        desktop_map = cache.get("map", {})

        if not desktop_names:
            return

        current_desktop = hou.ui.curDesktop()
        current_desktop_name = current_desktop.name()

        try:
            current_index = desktop_names.index(current_desktop_name)
        except ValueError:
            cache = _build_desktop_cache_lazy()
            desktop_names = cache.get("names", [])
            desktop_map = cache.get("map", {})
            if not desktop_names:
                return
            current_index = 0

        next_index = (current_index + 1) % len(desktop_names)
        next_desktop_name = desktop_names[next_index]
        next_desktop = desktop_map.get(next_desktop_name)

        if next_desktop:
            next_desktop.setAsCurrent()
            update_keymap()
    except Exception:
        try:
            desktops_dict = {desktop.name(): desktop for desktop in hou.ui.desktops()}
            desktop_names = list(desktops_dict.keys())

            current_desktop = hou.ui.curDesktop()
            current_desktop_name = current_desktop.name()

            current_index = desktop_names.index(current_desktop_name)
            next_index = (current_index + 1) % len(desktop_names)
            next_desktop_name = desktop_names[next_index]
            desktops_dict[next_desktop_name].setAsCurrent()
            update_keymap()
        except Exception:
            pass


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
    pane = hou.ui.paneTabUnderCursor()
    if pane and pane.type() == hou.paneTabType.SceneViewer:
        return pane
    return None


def _shading_mode_sets_from_pairs(pairs):
    return [a for (a, _b) in pairs], [b for (_a, b) in pairs]


def toggle_shading_mode():
    viewer = get_scene_viewer_under_cursor()
    if not viewer:
        return

    viewport = viewer.curViewport()
    settings = viewport.settings()

    display_sets = [
        settings.displaySet(hou.displaySetType.DisplayModel),
        settings.displaySet(hou.displaySetType.SceneObject)
    ]

    modes_set_1, modes_set_2 = _shading_mode_sets_from_pairs(_SHADING_MODE_PAIRS)

    for display_set in display_sets:
        current_mode = display_set.shadedMode()

        if current_mode in modes_set_1:
            mode_set = modes_set_1
        elif current_mode in modes_set_2:
            mode_set = modes_set_2
        elif current_mode == _BOUNDING_BOX_SHADING_PAIR[1]:
            mode_set = modes_set_2
        elif current_mode == _BOUNDING_BOX_SHADING_PAIR[0]:
            mode_set = modes_set_1
        else:
            mode_set = modes_set_1

        try:
            next_mode_index = (mode_set.index(current_mode) + 1) % len(mode_set)
            next_mode = mode_set[next_mode_index]
        except ValueError:
            next_mode = mode_set[0]

        display_set.setShadedMode(next_mode)


def toggle_shading_mode_pair():
    viewer = get_scene_viewer_under_cursor()
    if not viewer:
        return

    viewport = viewer.curViewport()
    settings = viewport.settings()

    display_sets = [
        settings.displaySet(hou.displaySetType.DisplayModel),
        settings.displaySet(hou.displaySetType.SceneObject)
    ]

    shading_pairs = [_BOUNDING_BOX_SHADING_PAIR, *_SHADING_MODE_PAIRS]

    for display_set in display_sets:
        current_mode = display_set.shadedMode()

        for mode_a, mode_b in shading_pairs:
            if current_mode == mode_a:
                display_set.setShadedMode(mode_b)
                break
            elif current_mode == mode_b:
                display_set.setShadedMode(mode_a)
                break


def convert_hda_to_subnet():
    selected_nodes = hou.selectedNodes()

    if len(selected_nodes) != 1:
        print("Error: Please select exactly one HDA node.")
        return
    hda_node = selected_nodes[0]
    if not hda_node.type().definition():
        print("Error: Selected node is not an HDA.")
        return

    try:
        parent = hda_node.parent()
        position = hda_node.position()

        if not hda_node.isEditable():
            hda_node.allowEditingOfContents()

        subnet = parent.createNode("subnet", hda_node.name() + "_subnet")

        internal_nodes = hda_node.children()
        if not internal_nodes:
            print("Warning: HDA contains no nodes to extract.")
            subnet.destroy()
            return

        node_map = {}
        node_positions = {}
        for node in internal_nodes:
            node_positions[node] = node.position()
            new_node = subnet.copyItems([node])[0]
            node_map[node] = new_node

        for orig_node, new_node in node_map.items():
            if orig_node in node_positions:
                new_node.setPosition(node_positions[orig_node])

        for orig_node, new_node in node_map.items():
            for i, input_node in enumerate(orig_node.inputs()):
                if input_node in node_map:
                    new_node.setInput(i, node_map[input_node])

        parm_templates = hda_node.parmTemplateGroup().entries()
        new_parm_group = hou.ParmTemplateGroup()
        for parm_template in parm_templates:
            new_parm_group.append(parm_template)
        subnet.setParmTemplateGroup(new_parm_group)

        for parm in hda_node.parms():
            parm_name = parm.name()
            subnet_parm = subnet.parm(parm_name)
            if subnet_parm:
                try:
                    subnet_parm.set(parm.eval())
                except:
                    pass

        subnet.setPosition(position)

        for i, input_node in enumerate(hda_node.inputs()):
            subnet.setInput(i, input_node)
        for conn in hda_node.outputConnections():
            output_node = conn.outputNode()
            input_index = conn.inputIndex()
            output_node.setInput(input_index, subnet, conn.outputIndex())

        hda_node.destroy()

        subnet.setSelected(True)

        print(f"HDA '{subnet.name()}' converted to subnet successfully!")

    except Exception as e:
        print(f"Error converting HDA to subnet: {str(e)}")
        if subnet:
            subnet.destroy()


def is_panel_active(panel_name):
    try:
        desktop = hou.ui.curDesktop()
        for pane in desktop.panes():
            current_tab = pane.currentTab()
            if current_tab and current_tab.type() == hou.paneTabType.PythonPanel:
                if current_tab.name() == panel_name:
                    return True
        return False
    except Exception:
        return False


def is_node_type(node, node_type_name, category_name=None):
    try:
        if not node or not isinstance(node, hou.Node):
            return False
        if category_name and node.type().category().name() != category_name:
            return False
        tname = (node.type().name() or "").lower()
        node_type_lower = node_type_name.lower()
        return tname == node_type_lower or tname.startswith(node_type_lower + "::")
    except Exception:
        return False