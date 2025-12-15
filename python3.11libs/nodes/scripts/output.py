import hou, os, subprocess



def refresh(kwargs):
    node = kwargs["node"]
    input_source = node.parm("source").eval()
    
    try:
        ctrl_name = node.parm("import_source").eval()
        hda_node = get_input_node(node)
        if hda_node and ctrl_name and hda_node.node(ctrl_name):
            reimport(kwargs)
    except Exception:
        pass

    if input_source == 0:
        hide_parameters(kwargs)
        convert_to_import_blocks(kwargs)



def is_hda(node):
    return node.type().definition() is not None



def get_input_node(node):
    import_source = node.parm("source").eval()

    if import_source == 0:
        return node.parent()
    elif import_source == 1:
        return node.input(0)
    else:
        raise ValueError(f"Invalid value for 'import_source': {import_source}")



def reimport(kwargs):
    node = kwargs["node"]

    try:
        hda_node = get_input_node(node)
    except ValueError as e:
        return hou.ui.setStatusMessage(str(e), severity=hou.severityType.Warning)

    if not hda_node:
        raise Exception("No input connected.")

    if not is_hda(hda_node):
        return hou.ui.setStatusMessage("Target node is not an HDA.", severity=hou.severityType.Warning)
    
    definition = hda_node.type().definition()
    if not definition:
        raise Exception("HDA has no definition to modify.")

    ctrl_name = node.parm("import_source").eval()
    if not ctrl_name:
        return hou.ui.setStatusMessage("Parameter 'source' is empty.", severity=hou.severityType.Warning)

    from_node = hda_node.node(ctrl_name)
    if not from_node:
        return hou.ui.setStatusMessage(f"'{ctrl_name}' node is not found inside HDA.", severity=hou.severityType.Warning)

    from_ptg = from_node.parmTemplateGroup()

    new_ptg = hou.ParmTemplateGroup()
    for parm_template in from_ptg.entries():
        new_ptg.append(parm_template)

    definition.setParmTemplateGroup(new_ptg)
    hda_node.removeSpareParms()

    for parm in from_node.parms():
        parm_name = parm.name()
        hda_parm_path = f'../{parm_name}'

        try:
            hda_parm = hda_node.parm(parm_name)
            if not hda_parm:
                continue

            parm_template = parm.parmTemplate()
            if parm_template is None:
                continue

            if parm_template.dataType() == hou.parmData.Int:
                expr_func = "ch"
            elif parm_template.dataType() == hou.parmData.Float:
                expr_func = "ch"
            elif parm_template.dataType() == hou.parmData.String:
                expr_func = "chs"
            else:
                expr_func = "ch"

            parm.setExpression(f'{expr_func}("{hda_parm_path}")')

        except hou.OperationFailed:
            pass

    hou.ui.setStatusMessage("HDA updated successfully.", severity=hou.severityType.ImportantMessage)



def execute_hda(kwargs):
    update_directory(kwargs)

    node = kwargs["node"]

    try:
        hda_node = get_input_node(node)
    except ValueError as e:
        return hou.ui.setStatusMessage(str(e), severity=hou.severityType.Warning)

    if not hda_node:
        raise Exception("No input connected.")
        
    if not is_hda(hda_node):
        return hou.ui.setStatusMessage("Target node is not an HDA.", severity=hou.severityType.Warning)

    definition = hda_node.type().definition()
    if not definition:
        raise Exception("Selected node is not an HDA.")

    hda_name = node.parm("filename").eval() + ".hda"
    save_directory = node.parm("directory").eval()
    target_path = os.path.join(save_directory, hda_name)


    definition.updateFromNode(hda_node)

    backups = node.parm("backups").eval()
    definition.save(target_path, create_backup=backups)

    hou.ui.setStatusMessage(f"HDA saved to: {target_path}", severity=hou.severityType.Message)

    set_editable_node(kwargs)



def open(kwargs):
    node = kwargs["node"]
    directory = node.parm("directory").eval()

    if not directory:
        return

    if os.path.exists(directory):
        os.startfile(directory)
    else:
        result = hou.ui.displayMessage(
            f"The directory does not exist:\n{directory}\n\nWould you like to create it?",
            buttons=["Create", "Cancel"],
            default_choice=0,
            close_choice=1,
            severity=hou.severityType.Message
        )

        if result == 0:
            try:
                os.makedirs(directory)
                os.startfile(directory)
            except Exception as e:
                hou.ui.displayMessage(f"Failed to create folder:\n{str(e)}", severity=hou.severityType.Error)



def open_type_properties(kwargs):
    node = kwargs["node"].parent()
    hou.ui.openTypePropertiesDialog(node)



def open_parameters(kwargs):
    node = kwargs["node"]
    try:
        ctrl_name = node.parm("import_source").eval()
        hda_node = get_input_node(node)
        ctrl_node = hda_node.node(ctrl_name) if hda_node else None
        if ctrl_node:
            hou.ui.openParameterInterfaceDialog(ctrl_node)
    except Exception:
        pass



def set_editable_node(kwargs):
    node = kwargs["node"]
    try:
        edit_node = node.parm("editable_node").eval()
        edit_node = convert_operator_path(edit_node)
        hda_node = get_input_node(node)
        
        if hda_node:
            hda_def = hda_node.type().definition()

            if not edit_node:
                hda_def.removeSection("EditableNodes")
            else:
                hda_def.addSection("EditableNodes", edit_node)
    
    except Exception as e:
        print(f"Error: {e}")



def convert_operator_path(path):
    if path.startswith("../"):
        path = path[3:]
    return path



def hide_parameters(kwargs):
    parent_node = kwargs["node"].parent()
    if not parent_node:
        return

    if parent_node.type().category().name() != "Object":
        return

    definition = parent_node.type().definition()
    if not definition:
        return

    ptg = definition.parmTemplateGroup()
    modified = False
    tab_count = 0
    new_ptg = hou.ParmTemplateGroup()

    def hide_templates(templates):
        hidden = []
        for t in templates:
            if isinstance(t, hou.FolderParmTemplate):
                hidden_folder = t.clone()
                hidden_folder.setParmTemplates(hide_templates(t.parmTemplates()))
                hidden.append(hidden_folder)
            else:
                hidden_parm = t.clone()
                if hidden_parm.name() == "renderable" or tab_count < 3:
                    hidden_parm.hide(True)
                    modified = True
                hidden.append(hidden_parm)
        return hidden

    for entry in ptg.entries():
        if isinstance(entry, hou.FolderParmTemplate) and entry.folderType() == hou.folderType.Tabs:
            if tab_count < 3:
                hidden_tab = entry.clone()
                hidden_tab.setParmTemplates(hide_templates(entry.parmTemplates()))
                new_ptg.append(hidden_tab)
                modified = True
                tab_count += 1
            else:
                updated_tab = entry.clone()
                updated_tab.setParmTemplates(hide_templates(entry.parmTemplates()))
                new_ptg.append(updated_tab)
        elif isinstance(entry, hou.ParmTemplate):
            cloned = entry.clone()
            if cloned.name() == "renderable":
                cloned.hide(True)
                modified = True
            new_ptg.append(cloned)
        else:
            new_ptg.append(entry)

    if modified:
        try:
            definition.setParmTemplateGroup(new_ptg)
            parent_node.parmTemplateGroup()
        except:
            pass



def convert_to_import_blocks(kwargs):
    parent_node = kwargs["node"].parent()
    if not parent_node:
        return

    definition = parent_node.type().definition()
    if not definition:
        return

    ptg = definition.parmTemplateGroup()
    modified = False
    new_ptg = hou.ParmTemplateGroup()

    def convert_folder(folder):
        new_folder = hou.FolderParmTemplate(
            folder.name(),
            folder.label(),
            folder_type=hou.folderType.ImportBlock
        )
        for sub in folder.parmTemplates():
            if isinstance(sub, hou.FolderParmTemplate) and sub.folderType() == hou.folderType.Tabs:
                new_folder.addParmTemplate(convert_folder(sub))
            else:
                new_folder.addParmTemplate(sub)
        return new_folder

    for entry in ptg.entries():
        if isinstance(entry, hou.FolderParmTemplate) and entry.folderType() == hou.folderType.Tabs:
            new_folder = convert_folder(entry)
            new_ptg.append(new_folder)
            modified = True
        else:
            new_ptg.append(entry)

    if modified:
        try:
            definition.setParmTemplateGroup(new_ptg)
        except:
            pass



def execute_top(kwargs):
    update_directory(kwargs)
    
    node = kwargs["node"]
    topnet = node.node('topnet1')
    dirty_button = topnet.parm('dirtybutton')
    execute_button = topnet.parm('cookbutton')

    dirty_button.pressButton()
    execute_button.pressButton()



def execute_rop(kwargs, rop_name):
    update_directory(kwargs)

    node = kwargs["node"]
    rop = node.node(rop_name)
    execute_button = rop.parm('execute')
    execute_button.pressButton()



def update_filename(kwargs, param_changed, param_update):
    value_changed = kwargs["node"].parm(param_changed).eval()
    kwargs["node"].parm(param_update).set(value_changed)



def update_directory(kwargs):
    node = kwargs["node"]
    path = node.parm("directory").unexpandedString()
    if not path.endswith('/'):
        path += '/'
    node.parm("directory").set(path)



def convert_to_raw(kwargs):
    update_directory(kwargs)

    node = kwargs["node"]
    console = node.evalParm("console")
    
    directory = node.evalParm("directory")
    filename = node.evalParm("filename")
    suffix = "_heightmap"

    input_file = directory + filename + suffix + ".png"
    output_file = directory + filename + suffix + ".raw"
    meta_file = input_file + ".meta"
    
    imagemagick_binary = node.evalParm("imagemagickbinary")
    
    if (imagemagick_binary == 0):
        imagemagick = ""
        if imagemagick == '':
            if(console):
                print("System Environment Variable Path is not implemented, update code to use")
            return
    elif (imagemagick_binary == 1):
        imagemagick = os.path.join(os.environ.get("PDG_IMAGEMAGICK_DIR", ""), "magick.exe")
        if imagemagick == '':
            if(console):
                print("PDG_IMAGEMAGICK_DIR is not defined")
            return
    elif (imagemagick_binary == 2):
        imagemagick = os.environ.get("PDG_IMAGEMAGICK", "magick")
        if imagemagick == '':
            if(console):
                print("PDG_IMAGEMAGICK is not defined")
            return
    elif (imagemagick_binary == 3):
        imagemagick = node.evalParm("customimagemagickbinary")
        if imagemagick == '':
            if(console):
                print("ImageMagick Binary Path is empty")
            return
    
    if os.path.exists(input_file):
    
        command = [
            imagemagick,
            input_file,
            "-depth", "16",
            "-type", "Grayscale",
            "-compress", "none",
            f"gray:{output_file}"
        ]
        
        try:
            subprocess.run(command, check=True)
            if console:
                print(f"Image converted successfully: {output_file}")
        except subprocess.CalledProcessError as e:
            if console:
                print(f"Error occurred: {e}")
        
        if os.path.isfile(input_file):
            os.remove(input_file)
        if os.path.isfile(meta_file):
            os.remove(meta_file)
    else:
        if console:
            print("No PNG file, save PNG file first")

