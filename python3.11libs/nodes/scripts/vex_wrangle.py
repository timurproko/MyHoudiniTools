import hou
import re
import time
from ..constants import vex_wrangle as _vex_consts
import mytools

_selection_callback_id = None
_last_selected_node_path = None


def _extract_channel_names_from_code(node, parmname):
    parm = node.parm(parmname)
    if not parm:
        return set()
    
    original = parm.unexpandedString()
    if len(parm.keyframes()) > 0:
        code = parm.evalAsString()
    else:
        code = original.strip()
        if len(code) > 2 and code.startswith("`") and code.endswith("`"):
            code = parm.evalAsString()
    
    code = _comment_or_string_exp.sub(_remove_comments, code)
    
    foundnames = set()
    for match in _chcall_exp.finditer(code):
        name = match.group(2)[1:-1]
        foundnames.add(name)
    
    return foundnames




def _update_folder_spare_parms_recursive(ptg, entry, referenced_channel_names, node, target_names=None, target_labels=None, entry_path=None):
    updated = False
    should_remove = False
    
    if entry_path is None:
        entry_path = []
    if target_names is None:
        target_names = []
    if target_labels is None:
        target_labels = []
    
    if isinstance(entry, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
        entry_name = entry.name()
        entry_label = (entry.label() or "").lower()
        
        matches_pattern = False
        if target_names:
            for target_name in target_names:
                if entry_name.startswith(target_name) or entry_name == target_name:
                    matches_pattern = True
                    break
        if not matches_pattern and target_labels:
            for target_label in target_labels:
                if target_label in entry_label:
                    matches_pattern = True
                    break
        
        folder_templates = list(entry.parmTemplates())
        
        updated_templates = []
        for i, template in enumerate(folder_templates):
            if isinstance(template, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
                nested_updated, updated_template, nested_should_remove = _update_folder_spare_parms_recursive(
                    ptg, template, referenced_channel_names, node, target_names, target_labels, entry_path + [i])
                if nested_updated:
                    updated = True
                if not nested_should_remove:
                    updated_templates.append(updated_template)
            else:
                updated_templates.append(template)
        
        if matches_pattern:
            spare_to_remove = set()
            for template in updated_templates:
                if not isinstance(template, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
                    parm = node.parm(template.name())
                    if parm and parm.isSpare():
                        if template.name() not in referenced_channel_names:
                            spare_to_remove.add(template.name())
            
            if spare_to_remove:
                final_templates = []
                for template in updated_templates:
                    if template.name() not in spare_to_remove:
                        final_templates.append(template)
                
                if len(final_templates) == 0:
                    should_remove = True
                    updated = True
                    return updated, entry, should_remove
                
                new_folder = entry.clone()
                new_folder.setParmTemplates(final_templates)
                updated = True
                return updated, new_folder, should_remove
        
        if updated:
            if len(updated_templates) == 0 and matches_pattern:
                should_remove = True
                return updated, entry, should_remove
            
            new_folder = entry.clone()
            new_folder.setParmTemplates(updated_templates)
            return updated, new_folder, should_remove
    
    return updated, entry, should_remove


def update_parms(node):
    try:
        if node is None:
            return
        
        snippet_parm = node.parm("snippet")
        referenced_channel_names = set()
        if snippet_parm:
            referenced_channel_names = _extract_channel_names_from_code(node, "snippet")
        
        ptg = node.parmTemplateGroup()
        if ptg is None:
            return
        
        found_folders = []
        target_names = ['folder_generatedparms']
        target_labels = ['parameters', 'generated channel parameters']
        
        for entry in ptg.entries():
            mytools.find_folders_recursive(entry, found_folders, target_names, target_labels)
        
        if not found_folders:
            return
        
        updated = False
        updated_entries = []
        entries_to_remove = set()
        
        for entry in ptg.entries():
            if isinstance(entry, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
                was_updated, updated_entry, should_remove = _update_folder_spare_parms_recursive(
                    ptg, entry, referenced_channel_names, node, target_names, target_labels)
                if was_updated:
                    updated = True
                    if should_remove:
                        entries_to_remove.add(entry.name())
                    else:
                        updated_entries.append((entry.name(), updated_entry))
                else:
                    updated_entries.append((entry.name(), entry))
            else:
                updated_entries.append((entry.name(), entry))
        
        if updated:
            for entry_name, updated_entry in updated_entries:
                try:
                    ptg.replace(entry_name, updated_entry)
                except Exception:
                    indices = ptg.findIndices(updated_entry)
                    if indices:
                        ptg.replaceWithIndices(indices, updated_entry)
            
            for entry_name in entries_to_remove:
                try:
                    ptg.remove(entry_name)
                except Exception:
                    try:
                        folder = ptg.find(entry_name)
                        if folder:
                            indices = ptg.findIndices(folder)
                            if indices:
                                ptg.removeWithIndices(indices)
                    except Exception:
                        pass
            
            node.setParmTemplateGroup(ptg)
                
    except Exception as e:
        pass


def delete_parms(node):
    node.removeSpareParms()


def on_deleted(node):
    """Called when a vex_wrangle node is being deleted.
    Simplified: relies on parms_watcher's unified deletion handler.
    """
    if node is None:
        return
    
    try:
        parm = node.parm("snippet")
    except (AttributeError, RuntimeError):
        return
    
    if parm is None:
        return
    
    try:
        import parms_watcher
        parms_watcher.remove_parm_from_watcher(parm, type_="parm")
    except Exception:
        pass


def edit_code(node):
    parm = node.parm("snippet")
    vscEmbed(parm, _vex_consts.IDE_NAME)


def vscEmbed(parm, ide):
    """Open parameter in external editor and embed in Houdini panel.
    Works for both VEX wrangle nodes and regular parameters.
    """
    import parms_watcher
    import hdefereval

    try:
        reload(parms_watcher)
    except NameError:
        from importlib import reload
        reload(parms_watcher)
    
    parms_watcher.add_watcher(parm)

    def _create_embedded_panel():
        try:
            desktop = hou.ui.curDesktop()
            existing_vsc_tab = None
            for pane in desktop.paneTabs():
                if pane.type() == hou.paneTabType.PythonPanel and pane.name() == ide:
                    existing_vsc_tab = pane
                    break

            if existing_vsc_tab:
                existing_vsc_tab.setIsCurrentTab()
            else:
                tab = desktop.paneTabOfType(hou.paneTabType.Parm)
                if tab is None:
                    tab = desktop.paneTabOfType(hou.paneTabType.NetworkEditor)
                if tab is None:
                    return
                
                pane = tab.pane()
                tab.setShowNetworkControls(False)
                pane.setShowPaneTabs(True)
                new_tab = pane.createTab(hou.paneTabType.PythonPanel)
                new_tab.setName(ide)
                new_tab.showToolbar(False)
                
                def _set_interface():
                    try:
                        time.sleep(0.25)
                        interfaces = hou.pypanel.interfaces()
                        if "vscEmbed" in interfaces:
                            new_tab.setActiveInterface(interfaces["vscEmbed"])
                        else:
                            for name, interface in interfaces.items():
                                if hasattr(interface, 'label') and interface.label() == ide:
                                    new_tab.setActiveInterface(interfaces[name])
                                    break
                    except Exception as e:
                        print(f"vscEmbed error setting interface: {e}")
                
                hdefereval.executeDeferred(_set_interface)
        except Exception as e:
            print(f"vscEmbed error: {e}")
    
    hdefereval.executeDeferred(_create_embedded_panel)


_chcalls = [
    'ch', 'chf', 'chi', 'chu', 'chv', 'chp', 'ch2', 'ch3', 'ch4',
    'vector(chramp', 'chramp',
    'vector(chrampderiv', 'chrampderiv',
    'chs',
    'chdict', 'chsop'
]

_chcall_exp = re.compile(f"""
\\b  # Start at word boundary
({"|".join(re.escape(chcall) for chcall in _chcalls)})  # Match any call string
\\s*[(]\\s*  # Opening bracket, ignore any surrounding whitespace
('\\w+'|"\\w+")  # Single or double quoted string
\\s*[),]  # Optional white space and closing bracket or comma marking end of first argument
""", re.VERBOSE)

_ch_size = {
    'chu': 2, 'chv': 3, 'chp': 4, 'ch2': 4, 'ch3': 9, 'ch4': 16,
}

_comment_or_string_exp = re.compile(
    r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
    re.DOTALL | re.MULTILINE
)


def _remove_comments(match):
    s = match.group(0)
    if s.startswith('/'):
        return ' '
    else:
        return s


def _addSpareParmsToTabFolder(node, parmname, refs):
    if not refs:
        return

    ptg = node.parmTemplateGroup()
    foldername = 'folder_generatedparms'
    
    folder = ptg.find(foldername)
    if not folder:
        for entry in ptg.entries():
            if isinstance(entry, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
                if entry.folderType() == hou.folderType.Tabs and (entry.label() or "").lower() == "parameters":
                    folder = entry
                    foldername = entry.name()
                    break
    if not folder:
        first_tab_name = None
        entries = ptg.entries()
        for entry in entries:
            is_tab_folder = False
            if isinstance(entry, hou.FolderParmTemplate):
                is_tab_folder = entry.folderType() == hou.folderType.Tabs
            elif isinstance(entry, hou.FolderSetParmTemplate):
                is_tab_folder = entry.folderType() == hou.folderType.Tabs
            
            if is_tab_folder:
                first_tab_name = entry.name()
                break
        
        if not folder:
            folder = hou.FolderParmTemplate(
                foldername,
                "Parameters",
                folder_type=hou.folderType.Tabs,
            )
            folder.setTags({"sidefx::look": "blank"})
            
            if first_tab_name:
                ptg.insertBefore(first_tab_name, folder)
            else:
                ptg.append(folder)

    indices = ptg.findIndices(folder)
    for name, template in refs:
        exparm = node.parm(name) or node.parmTuple(name)
        if exparm:
            ptg.replace(name, template)
        else:
            ptg.appendToFolder(indices, template)
    node.setParmTemplateGroup(ptg)


def createSpareParmsFromChCalls(node, parmname):
    mytools.select_parameter_tab(node, 0)
    
    parm = node.parm(parmname)
    original = parm.unexpandedString()
    simple = True
    if len(parm.keyframes()) > 0:
        code = parm.evalAsString()
        simple = False
    else:
        code = original.strip()
        if len(code) > 2 and code.startswith("`") and code.endswith("`"):
            code = parm.evalAsString()
            simple = False
    code = _comment_or_string_exp.sub(_remove_comments, code)

    refs = []
    existing = []
    foundnames = set()
    for match in _chcall_exp.finditer(code):
        call = match.group(1)
        name = match.group(2)[1:-1]

        if name in foundnames:
            continue
        foundnames.add(name)
        
        size = _ch_size.get(call, 1)
        label = name.title().replace("_", " ")

        if call in ("vector(chramp", "vector(chrampderiv"):
            template = hou.RampParmTemplate(name, label, hou.rampParmType.Color)
        elif call in ("chramp", "chrampderiv"):
            template = hou.RampParmTemplate(name, label, hou.rampParmType.Float)
        elif call == "chs":
            template = hou.StringParmTemplate(name, label, size)
        elif call == "chsop":
            template = hou.StringParmTemplate(
                name, label, size, string_type=hou.stringParmType.NodeReference)
        elif call == "chi":
            template = hou.IntParmTemplate(name, label, size)
        elif call == "chdict":
            template = hou.DataParmTemplate(
                name, label, size,
                data_parm_type=hou.dataParmType.KeyValueDictionary
            )
        else:
            template = hou.FloatParmTemplate(name, label, size, min=0, max=1)

        exparm = node.parm(name) or node.parmTuple(name)
        if exparm:
            if not exparm.isSpare():
                continue
            extemplate = exparm.parmTemplate()
            etype = extemplate.type()
            ttype = template.type()
            if (
                etype != ttype or
                extemplate.numComponents() != template.numComponents() or
                (ttype == hou.parmTemplateType.String and
                 extemplate.stringType() != template.stringType())
            ):
                existing.append((name, template))
            else:
                continue
        else:
            refs.append((name, template))

    if existing:
        exnames = ", ".join(f'"{name}"' for name, _ in existing)
        if len(existing) > 1:
            msg = f"Parameters {exnames} already exist, replace them?"
        else:
            msg = f"Parameter {exnames} already exists, replace it?"
        result = hou.ui.displayCustomConfirmation(
            msg, ("Replace", "Skip Existing", "Cancel"), close_choice=2,
            title="Replace Existing Parameters?",
            suppress=hou.confirmType.DeleteSpareParameters,
        )
        if result == 0:
            refs.extend(existing)
        elif result == 2:
            return

    _addSpareParmsToTabFolder(node, parmname, refs)

    if refs:
        if simple:
            parm.set(original)


def toggle_node_color(node):
    if node is None:
        return
    
    current_color = node.color().rgb()
    default_color = _vex_consts.TOGGLE_NODE_DEFAULT_COLOR
    selected_color = _vex_consts.TOGGLE_NODE_SELECTED_COLOR
    alternate_color = _vex_consts.TOGGLE_NODE_ALTERNATE_COLOR
    
    if current_color == default_color:
        node.setColor(hou.Color(selected_color))
    elif current_color == selected_color:
        node.setColor(hou.Color(alternate_color))
    else:
        node.setColor(hou.Color(default_color))


def _on_node_selection_changed():
    global _last_selected_node_path
    
    try:
        if not mytools.is_panel_active(_vex_consts.IDE_NAME):
            _last_selected_node_path = None
            return
        
        selected_nodes = hou.selectedNodes()
        if not selected_nodes:
            _last_selected_node_path = None
            return
        
        selected_node = selected_nodes[0]
        current_node_path = selected_node.path()
        
        if current_node_path == _last_selected_node_path:
            return
        
        _last_selected_node_path = current_node_path
        
        if not mytools.is_node_type(selected_node, "vex_wrangle", "Sop"):
            parm_pane = hou.ui.paneTabOfType(hou.paneTabType.Parm)
            if parm_pane:
                parm_pane.setIsCurrentTab()
        else:
            edit_code(selected_node)
    except Exception:
        pass


def register():
    global _selection_callback_id
    
    if _selection_callback_id is not None:
        return
    
    try:
        try:
            from PySide6 import QtCore
        except ImportError:
            from PySide2 import QtCore
        
        timer = QtCore.QTimer()
        timer.timeout.connect(_on_node_selection_changed)
        timer.start(100)
        _selection_callback_id = timer
    except Exception:
        _selection_callback_id = None