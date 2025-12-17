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


def show_parms(node):
    current_value = node.parm("parm_mode").eval()
    new_value = not current_value
    node.parm("parm_mode").set(new_value)
    toggle_node_color_from_current(node)


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


def update_parms(node):
    """Update spare parameters by removing only those that are not referenced in the code.
    
    Compares existing spare parameters against channel calls found in the snippet
    parameter and removes only the ones that are not in the code.
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
        
        parameters_folder = None
        foldername = None
        
        foldername = 'folder_generatedparms'
        parameters_folder = ptg.find(foldername)
        
        if not parameters_folder:
            for entry in ptg.entries():
                if isinstance(entry, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
                    if entry.folderType() == hou.folderType.Tabs:
                        label = (entry.label() or "").lower()
                        if label == "parameters":
                            parameters_folder = entry
                            foldername = entry.name()
                            break
        
        if not parameters_folder:
            return
        
        folder_templates = list(parameters_folder.parmTemplates())
        
        if not folder_templates:
            return
        
        # Find spare parameters that are NOT in the code
        spare_to_remove = set()
        for template in folder_templates:
            parm = node.parm(template.name())
            if parm and parm.isSpare():
                # Only remove if not referenced in code
                if template.name() not in referenced_channel_names:
                    spare_to_remove.add(template.name())
        
        if not spare_to_remove:
            return
        
        # Keep templates that are not spare or are referenced in code
        remaining_templates = []
        for template in folder_templates:
            if template.name() not in spare_to_remove:
                remaining_templates.append(template)
        
        new_folder = parameters_folder.clone()
        new_folder.setParmTemplates(remaining_templates)
        ptg.replace(foldername, new_folder)
        
        node.setParmTemplateGroup(ptg)
                
    except Exception as e:
        pass


def delete_parms(node):
    """Remove all spare parameters and the Parameters tab folder using Houdini's built-in method."""
    try:
        if node is None:
            return
        
        ptg = node.parmTemplateGroup()
        if ptg is None:
            return
        
        # Find the Parameters tab folder
        parameters_folder = None
        foldername = None
        
        foldername = 'folder_generatedparms'
        parameters_folder = ptg.find(foldername)
        
        if not parameters_folder:
            for entry in ptg.entries():
                if isinstance(entry, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
                    if entry.folderType() == hou.folderType.Tabs:
                        label = (entry.label() or "").lower()
                        if label == "parameters":
                            parameters_folder = entry
                            foldername = entry.name()
                            break
        
        if not parameters_folder:
            return
        
        # Get all spare parameters from the folder
        folder_templates = list(parameters_folder.parmTemplates())
        spare_param_names = []
        
        for template in folder_templates:
            parm = node.parm(template.name())
            if parm and parm.isSpare():
                spare_param_names.append(template.name())
        
        # Remove all spare parameters using Houdini's built-in method
        for name in spare_param_names:
            try:
                node.removeSpareParmTuple(name)
            except Exception:
                pass
        
        # Remove the folder if it exists and is now empty
        ptg = node.parmTemplateGroup()
        if ptg:
            parameters_folder = ptg.find(foldername)
            if not parameters_folder:
                for entry in ptg.entries():
                    if isinstance(entry, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
                        if entry.folderType() == hou.folderType.Tabs:
                            label = (entry.label() or "").lower()
                            if label == "parameters":
                                foldername = entry.name()
                                break
            
            if foldername and ptg.find(foldername):
                ptg.remove(foldername)
                node.setParmTemplateGroup(ptg)
                
    except Exception as e:
        pass


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
    """
    For each ch() call in the given parm name, create a corresponding spare
    parameter on the node. Parameters are placed in a tab folder at the bottom.
    """
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
    """Create spare parameters from ch() calls in the snippet parameter."""
    try:
        if node is None:
            return
        snippet_parm = node.parm("snippet")
        if snippet_parm is None:
            return
        createSpareParmsFromChCalls(node, "snippet")
    except Exception:
        pass