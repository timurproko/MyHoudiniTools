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


def delete_parms(node):
    """Remove spare parameters from inside the Parameters tab folder.
    
    Custom solution that only removes templates from the folder without
    checking if folder is empty and without calling Houdini's removeSpareParmTuple.
    """
    try:
        if node is None:
            return
        
        ptg = node.parmTemplateGroup()
        if ptg is None:
            return
        
        # Find the Parameters tab folder
        parameters_folder = None
        foldername = None
        
        # First try to find by the standard name
        foldername = 'folder_generatedparms'
        parameters_folder = ptg.find(foldername)
        
        # If not found, search for any tab folder with "Parameters" label
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
            # No Parameters folder found, do nothing
            return
        
        # Get all templates in the folder
        folder_templates = list(parameters_folder.parmTemplates())
        
        # Check if folder is already empty
        if not folder_templates:
            # Folder is empty, remove the folder itself
            ptg.remove(foldername)
            node.setParmTemplateGroup(ptg)
            return
        
        # Identify which templates are spare parameters
        spare_template_names = set()
        for template in folder_templates:
            parm = node.parm(template.name())
            if parm and parm.isSpare():
                spare_template_names.add(template.name())
        
        if not spare_template_names:
            # No spare parameters in folder, do nothing
            return
        
        # Custom method: manually remove ONLY spare parameter templates from folder
        # Keep all other templates (non-spare parameters)
        remaining_templates = []
        for template in folder_templates:
            if template.name() not in spare_template_names:
                remaining_templates.append(template)
        
        # Only remove spare parameters inside the folder
        # Don't remove the folder itself - just update it with remaining templates
        # (If folder becomes empty, it will be removed on the next call)
        new_folder = parameters_folder.clone()
        new_folder.setParmTemplates(remaining_templates)
        ptg.replace(foldername, new_folder)
        
        # Apply the template group changes
        # This removes the spare parameter templates from the folder
        # The folder remains (even if empty) until next call
        node.setParmTemplateGroup(ptg)
                
    except Exception as e:
        # Debug: uncomment to see errors
        # print(f"delete_parms error: {e}")
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


# ===================== HOUDINI SOURCE CODE  =====================
# Extracted and modified from vexpressionmenu.py
# Creates spare parameters in a regular tab folder at the bottom

# Strings representing channel calls
_chcalls = [
    'ch', 'chf', 'chi', 'chu', 'chv', 'chp', 'ch2', 'ch3', 'ch4',
    'vector(chramp', 'chramp',
    'vector(chrampderiv', 'chrampderiv',
    'chs',
    'chdict', 'chsop'
]

# Expression for finding ch calls
_chcall_exp = re.compile(f"""
\\b  # Start at word boundary
({"|".join(re.escape(chcall) for chcall in _chcalls)})  # Match any call string
\\s*[(]\\s*  # Opening bracket, ignore any surrounding whitespace
('\\w+'|"\\w+")  # Single or double quoted string
\\s*[),]  # Optional white space and closing bracket or comma marking end of first argument
""", re.VERBOSE)

# Number of components corresponding to different ch calls. If a call string is
# not in this dict, it's assumed to have a single component.
_ch_size = {
    'chu': 2, 'chv': 3, 'chp': 4, 'ch2': 4, 'ch3': 9, 'ch4': 16,
}

# This expression matches comments (single and multiline) and also strings
# (though it will miss strings with escaped quote characters).
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
        return  # No-op

    ptg = node.parmTemplateGroup()
    # Use a single shared tab for all generated parameters
    foldername = 'folder_generatedparms'
    
    # Check if folder already exists (by name or by label)
    folder = ptg.find(foldername)
    if not folder:
        # Try to find an existing tab with label "Parameters" to reuse
        for entry in ptg.entries():
            if isinstance(entry, (hou.FolderParmTemplate, hou.FolderSetParmTemplate)):
                if entry.folderType() == hou.folderType.Tabs and (entry.label() or "").lower() == "parameters":
                    folder = entry
                    foldername = entry.name()
                    break
    if not folder:
        # Find the Code tab to insert after it
        code_tab_name = None
        entries = ptg.entries()
        for entry in entries:
            # Look for tab folders (both FolderParmTemplate and FolderSetParmTemplate)
            is_tab_folder = False
            if isinstance(entry, hou.FolderParmTemplate):
                is_tab_folder = entry.folderType() == hou.folderType.Tabs
            elif isinstance(entry, hou.FolderSetParmTemplate):
                is_tab_folder = entry.folderType() == hou.folderType.Tabs
            
            if is_tab_folder:
                # Check if this is the Code tab by looking at its label or name
                label = entry.label() or ""
                name = entry.name() or ""
                if "code" in label.lower() or "code" in name.lower():
                    code_tab_name = name
                    break
        
        # Create new tab folder if we didn't find an existing one
        if not folder:
            folder = hou.FolderParmTemplate(
                foldername,
                "Parameters",
                folder_type=hou.folderType.Tabs,
            )
            folder.setTags({"sidefx::look": "blank"})
            
            # Insert after Code tab if found, otherwise append at the end
            if code_tab_name:
                ptg.insertAfter(code_tab_name, folder)
            else:
                # Fallback: append at the bottom if Code tab not found
                ptg.append(folder)

    # Insert/replace the parameter templates
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
        # The parm has an expression/keyframes, evaluate it to the get its
        # current value
        code = parm.evalAsString()
        simple = False
    else:
        code = original.strip()
        if len(code) > 2 and code.startswith("`") and code.endswith("`"):
            # The whole string is in backticks, evaluate it
            code = parm.evalAsString()
            simple = False
    # Remove comments
    code = _comment_or_string_exp.sub(_remove_comments, code)

    # Loop over the channel refs found in the VEX, work out the corresponding
    # template type, remember for later (we might need to check first if the
    # user wants to replace existing parms).
    refs = []
    existing = []
    foundnames = set()
    for match in _chcall_exp.finditer(code):
        call = match.group(1)
        name = match.group(2)[1:-1]

        # If the same parm shows up more than once, only track the first
        # case.  This avoids us double-adding since we delay actual
        # creation of parms until we've run over everything.
        if name in foundnames:
            continue
        foundnames.add(name)
        
        size = _ch_size.get(call, 1)
        label = name.title().replace("_", " ")

        if call in ("vector(chramp", "vector(chrampderiv"):
            # Result was cast to a vector, assume it's a color
            template = hou.RampParmTemplate(name, label, hou.rampParmType.Color)
        elif call in ("chramp", "chrampderiv"):
            # No explicit cast, assume it's a float
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
                # The existing parameter isn't a spare, so just skip it
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
                # The template type is different, remember the name and template
                # type to replace later
                existing.append((name, template))
            else:
                # No difference in template type, we can skip this
                continue
        else:
            # Remember the parameter name and template type to insert later
            refs.append((name, template))

    # If there are existing parms with the same names but different template
    # types, ask the user if they want to replace them
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
        if result == 0:  # Replace
            refs.extend(existing)
        elif result == 2:  # Cancel
            return

    _addSpareParmsToTabFolder(node, parmname, refs)

    if refs:
        if simple:
            # Re-write the contents of the snippet so the node will re-run the
            # VEX and discover the new parameters.
            # (This is really a workaround for a bug (#123616), since Houdini
            # should ideally know to update VEX snippets automatically).
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


# ===================== HOUDINI SOURCE CODE  =====================

