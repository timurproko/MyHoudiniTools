import hou, json, hutil
import os, subprocess, platform



def node_parms_to_json(nodes, file=None, hidden=None, debug=False):
    if not nodes:
        nodes = hou.selectedNodes()
    if not nodes:
        return
    else:
        if not file:
            file = hou.ui.selectFile(file_type=hou.fileType.Any, default_value=nodes[0].name() + '.json', title='Export Parms to Json', collapse_sequences=False, image_chooser=False, chooser_mode=hou.fileChooserMode.Write)
        if not file:
            return
        res = 1
        d = {}
        for node in nodes:
            try:
                d[node.name()] = {}
                d[node.name()]['nameComponents'] = node.type().nameComponents()
                cnt = 0
                ramps = []
                for parm in node.parms():
                    if parm.parmTemplate().type() != hou.parmTemplateType.FolderSet and parm.parmTemplate().type() != hou.parmTemplateType.Button and parm.parmTemplate().type() != hou.parmTemplateType.Ramp and parm.parmTemplate().type() != hou.parmTemplateType.Label and parm.parmTemplate().type() != hou.parmTemplateType.Data:
                        if debug:
                            print('processing:', parm.name())
                        if res == 1:
                            ptemplate = parm.parmTemplate()
                            menu = None
                            try:
                                if ptemplate.menuType() == hou.menuType.Normal:
                                    x = parm.menuItems()
                                    menu = True
                            except:
                                menu = None

                            componentIndex = parm.componentIndex()
                            default = parm.parmTemplate().defaultValue()
                            d[node.name()][parm.name()] = {}
                            if menu:
                                if parm.parmTemplate().type() == hou.parmTemplateType.Int:
                                    d[node.name()][parm.name()]['value'] = parm.eval()
                                elif parm.parmTemplate().type() == hou.parmTemplateType.Float:
                                    d[node.name()][parm.name()]['value'] = parm.eval()
                                else:
                                    d[node.name()][parm.name()]['value'] = parm.evalAsString()
                            elif parm.parmTemplate().type() == hou.parmTemplateType.String:
                                d[node.name()][parm.name()]['value'] = parm.evalAsString()
                            else:
                                d[node.name()][parm.name()]['value'] = parm.eval()
                            try:
                                exp = parm.expression()
                                if exp != '""':
                                    d[node.name()][parm.name()]['expression'] = exp
                                    d[node.name()][parm.name()]['hasExpression'] = 1
                                else:
                                    d[node.name()][parm.name()]['hasExpression'] = 0
                            except:
                                d[node.name()][parm.name()]['hasExpression'] = 0

                            defaultIsTuple = isinstance(default, tuple)
                            if defaultIsTuple:
                                if menu:
                                    if parm.parmTemplate().type() == hou.parmTemplateType.String:
                                        p = str(default[componentIndex])
                                    else:
                                        p = default[componentIndex]
                                else:
                                    p = default[componentIndex]
                            elif menu:
                                if parm.parmTemplate().type() == hou.parmTemplateType.String:
                                    p = str(default)
                                else:
                                    p = default
                            else:
                                p = default
                            con = parm.parmTemplate().conditionals()
                            try:
                                disableCon = con[hou.parmCondType.DisableWhen]
                                d[node.name()][parm.name()]['disableWhen'] = disableCon
                            except:
                                disableCon = ''

                            try:
                                hideCon = con[hou.parmCondType.HideWhen]
                                d[node.name()][parm.name()]['hideWhen'] = hideCon
                            except:
                                hideCon = ''

                            if menu:
                                if parm.parmTemplate().type() == hou.parmTemplateType.Int:
                                    d[node.name()][parm.name()]['options'] = [int(pp) for pp in parm.menuItems()]
                                else:
                                    d[node.name()][parm.name()]['options'] = parm.menuItems()
                                d[node.name()][parm.name()]['labels'] = parm.menuLabels()
                                d[node.name()][parm.name()]['type'] = 'menu'
                                d[node.name()][parm.name()]['menuType'] = str(parm.parmTemplate().type()).split('.')[-1]
                            else:
                                d[node.name()][parm.name()]['type'] = str(parm.parmTemplate().dataType()).split('.')[-1]
                            if parm.parmTemplate().type() == hou.parmTemplateType.Float or parm.parmTemplate().type() == hou.parmTemplateType.Int:
                                if not menu:
                                    d[node.name()][parm.name()]['minValue'] = parm.parmTemplate().minValue()
                                    d[node.name()][parm.name()]['minValueEnforced'] = parm.parmTemplate().minIsStrict()
                                    d[node.name()][parm.name()]['maxValue'] = parm.parmTemplate().maxValue()
                                    d[node.name()][parm.name()]['maxValueEnforced'] = parm.parmTemplate().maxIsStrict()
                            d[node.name()][parm.name()]['default'] = p
                            d[node.name()][parm.name()]['description'] = parm.parmTemplate().help()
                    if parm.parmTemplate().type() == hou.parmTemplateType.Ramp:
                        d[node.name()][parm.name()] = {}
                        d[node.name()][parm.name()]['rampPTS'] = len(parm.eval().keys())
                        d[node.name()][parm.name()]['rampBasis'] = [str(s) for s in parm.eval().basis()]
                        ramps.append(parm.name())

            except Exception as e:
                print('Node not supported:', node.name(), 'skipping...', e)

        if d:
            d['ramps'] = ramps
            with open(hou.text.expandString(file), 'w') as outfile:
                json.dump(d, outfile, sort_keys=True, indent=4)
        return



def node_parms_from_json(nodes, file=None):
    rampBasisLookup = {'rampBasis.Linear': (hou.rampBasis.Linear), 'rampBasis.BSpline': (hou.rampBasis.BSpline), 'rampBasis.Bezier': (hou.rampBasis.Bezier), 'rampBasis.CatmullRom': (hou.rampBasis.CatmullRom), 'rampBasis.Constant': (hou.rampBasis.Constant), 'rampBasis.Hermite': (hou.rampBasis.Hermite), 'rampBasis.MonotoneCubic': (hou.rampBasis.MonotoneCubic)}
    if not nodes:
        nodes = hou.selectedNodes()
    if not nodes:
        return
    if not file:
        file = hou.ui.selectFile(file_type=hou.fileType.Any, default_value=nodes[0].name() + '.json', title='Import Parms from Json', collapse_sequences=False, image_chooser=False, chooser_mode=hou.fileChooserMode.Write)
    if not file:
        return
    d = hutil.json.loadFromFile(file)
    for node in nodes:
        ramps = d['ramps']
        if node.name() not in d.keys():
            entry = list(d.keys())[0]
        else:
            entry = node.name()
        for r in ramps:
            for p in node.parms():
                if r == p.name():
                    if len(p.eval().keys()) != d[entry][r]['rampPTS']:
                        basis = [
                         hou.rampBasis.Linear] * d[entry][r]['rampPTS']
                        for i in range(len(d[entry][r]['rampBasis'])):
                            basis[i] = rampBasisLookup[d[entry][r]['rampBasis'][i]]

                        p.set(hou.Ramp(p.evalAsRamp().basis(), tuple([0.0] * d[entry][r]['rampPTS']), tuple([0.0] * d[entry][r]['rampPTS'])))
                        break

        for parm in node.parms():
            if parm.parmTemplate().type() != hou.parmTemplateType.FolderSet and parm.parmTemplate().type() != hou.parmTemplateType.Button and parm.parmTemplate().type() != hou.parmTemplateType.Ramp and parm.parmTemplate().type() != hou.parmTemplateType.Label:
                if parm.name() in d[entry]:
                    parm.set(d[entry][parm.name()]['value'])



def load_preset(kwargs, load_by_button=0):
    node = kwargs['node']
    hda_name = node.name()
    parm = kwargs['parm']
    
    parm_name = parm.name()
    index = parm_name[-1]
    
    auto_apply = node.parm(f"auto_apply{index}").eval()
    if (auto_apply == 0) and (load_by_button == 0):
        return

    item = node.parm(f"presets{index}").evalAsString()
    dist_path = node.parm(f"destination_node{index}").eval()
    
    if not item:
        print(f"{hda_name}: No preset selected for instance {index}.")
        return
    if not dist_path:
        print(f"{hda_name}: Destination node not specified for instance {index}.")
        return

    dist_node = hou.node(dist_path)
    if not dist_node:
        print(f"{hda_name}: Invalid destination node specified for instance {index}: {dist_path}")
        return
    
    try:
        node_parms_from_json([dist_node], item)
    except Exception as e:
        print(f"{hda_name}: Error loading preset for instance {index}: {e}")

    if load_by_button == 1:
        node.parm(f"auto_apply{index}").set(0)



def generate_menu_from_json_files(node, index):
    dir_path = node.parm(f"presets_folder{index}").eval()
    
    menu = []
    
    if not os.path.isdir(dir_path):
        return menu
    
    json_files = [f for f in os.listdir(dir_path) if f.endswith(".json")]
    
    if not json_files:
        return menu
    
    for filename in json_files:
        file_path = os.path.join(dir_path, filename)
        display_name = os.path.splitext(filename)[0].replace('_', ' ')
        menu.append(file_path)
        menu.append(display_name)
    
    return menu



def open_present_folder(kwargs):
    node = kwargs['node']
    hda_name = node.name()
    parm = kwargs['parm']
    
    parm_name = parm.name()
    index = parm_name[-1]
    
    dir_path = node.parm(f"presets_folder{index}").eval()
    
    if not os.path.isdir(dir_path):
        return
    
    try:
        if platform.system() == "Windows":
            os.startfile(dir_path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", dir_path])
        else:
            subprocess.Popen(["xdg-open", dir_path])
    except Exception as e:
        print(f"{hda_name}: Error opening folder: {e}")