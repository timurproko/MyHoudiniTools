import hou
import re
import time
from ..constants import vex_wrangle as _vex_consts
import mytools


def toggle_node_color_from_current(
    node,
    highlight_color=_vex_consts.SHOW_PARMS_COLOR,
    userdata_key=_vex_consts.SHOW_PARMS_PREV_COLOR_USERDATA_KEY,
):
    if node is None:
        return

    prev = node.userData(userdata_key)
    if prev:
        try:
            node.setColor(hou.Color(mytools.decode_rgb(prev)))
        finally:
            try:
                node.destroyUserData(userdata_key)
            except Exception:
                node.setUserData(userdata_key, "")
        return

    node.setUserData(userdata_key, mytools.encode_rgb(node.color().rgb()))
    node.setColor(hou.Color(highlight_color))


def _extract_channel_names_from_code(node, parmname):
    """Extract all channel parameter names referenced in the code."""
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


def _find_folders_recursive(entry, found_folders, target_names=None, target_labels=None):
    """Recursively search for folders matching target names or labels."""
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
            _find_folders_recursive(sub_entry, found_folders, target_names, target_labels)


def _update_folder_spare_parms_recursive(ptg, entry, referenced_channel_names, node, entry_path=None):
    """Recursively update folders, modifying them in place if they need updates."""
    updated = False
    
    if entry_path is None:
        entry_path = []
    
    if isinstance(entry, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
        folder_templates = list(entry.parmTemplates())
        
        updated_templates = []
        for i, template in enumerate(folder_templates):
            if isinstance(template, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
                nested_updated, updated_template = _update_folder_spare_parms_recursive(
                    ptg, template, referenced_channel_names, node, entry_path + [i])
                if nested_updated:
                    updated = True
                    updated_templates.append(updated_template)
                else:
                    updated_templates.append(template)
            else:
                updated_templates.append(template)
        
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
            
            new_folder = entry.clone()
            new_folder.setParmTemplates(final_templates)
            updated = True
            return updated, new_folder
        
            new_folder = entry.clone()
            new_folder.setParmTemplates(updated_templates)
            return updated, new_folder
    
    return updated, entry


def update_parms(node):
    """Update spare parameters by removing only those that are not referenced in the code.
    
    Works with both the custom folder_generatedparms folder (including nested ones like
    folder_generatedparms_snippet) and any Parameters tab folders that Houdini may create.
    Updates all matching folders found, including nested folders.
    """
    try:
        if node is None:
            return
        
        # Extract channel names from code
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
            _find_folders_recursive(entry, found_folders, target_names, target_labels)
        
        if not found_folders:
            return
        
        updated = False
        updated_entries = []
        
        for entry in ptg.entries():
            if isinstance(entry, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
                was_updated, updated_entry = _update_folder_spare_parms_recursive(
                    ptg, entry, referenced_channel_names, node)
                if was_updated:
                    updated = True
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
            node.setParmTemplateGroup(ptg)
                
    except Exception as e:
        pass


def delete_parms(node):
    node.removeSpareParms()


def edit_code(node):
    parm = node.parm("snippet")
    vscEmbed(parm, "Visual Studio Code")


def vscEmbed(parm, ide):
    from HoudiniExprEditor import ParmWatcher

    try:
        reload(ParmWatcher)
    except NameError:
        from importlib import reload

        reload(ParmWatcher)
    ParmWatcher.add_watcher(parm)

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
        pane = tab.pane()
        tab.setShowNetworkControls(False)
        pane.setShowPaneTabs(True)
        tab = pane.createTab(hou.paneTabType.PythonPanel)
        tab.setName(ide)
        tab.showToolbar(False)
        time.sleep(0.25)
        tab.setActiveInterface(hou.pypanel.interfaces()["vscEmbed"])


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
    """Substitution function replaces comments with spaces and leaves strings alone."""
    s = match.group(0)
    if s.startswith('/'):
        return ' '
    else:
        return s


def _addSpareParmsToTabFolder(node, parmname, refs):
    """
    Takes a list of (name, template) in refs and injects them into a
    tab folder for generated parms. Creates the folder as a tab right after
    the Code tab if it doesn't exist.
    """
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
    _find_and_select_first_tab(node)
    
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


def create_parms(node):
    try:
        if node is None:
            return
        snippet_parm = node.parm("snippet")
        if snippet_parm is None:
            return
        createSpareParmsFromChCalls(node, "snippet")
    except Exception:
        pass


def _find_and_select_first_tab(node):
    """Find the first tabs folder and select its first tab (index 0) for the given node."""
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

        pt.set((0,))
    except Exception:
        pass
