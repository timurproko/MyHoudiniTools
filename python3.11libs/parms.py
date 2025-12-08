from typing import Iterable, Optional, Tuple, Generator
import hou, itertools, re


class HoudiniError(Exception):
    """Display message in houdini"""

def allParmTemplateNames(group_or_folder: hou.ParmTemplateGroup) -> Iterable[str]:
    '''Generator of parm names'''
    for parm_template in group_or_folder.parmTemplates():
        yield parm_template.name()
        if parm_template.type() == hou.parmTemplateType.Folder:
            for sub_parm_template in allParmTemplateNames(parm_template):
                yield sub_parm_template


class parmUtils():

    def __init__(self, kwargs) -> None:
        self.kwargs = kwargs
        self.parm_inst = kwargs["parms"][0]
        self.parm_node = self.parm_inst.node()
        self.parm_tuple = self.parm_inst.tuple()
        self.parm_group = self.parm_node.parmTemplateGroup()
        self._parm = self.parm_tuple.parmTemplate()

    @property
    def envNode_parm(self) -> Optional[str]:
        env = hou.getenv("ctrl_node")
        if env:
            return hou.node(env)

    @property
    def envNode_multi_counter(self) -> Optional[str]:
        env = hou.getenv("MULTIPARM_NODE")
        if env:
            return hou.node(env)

    @property
    def channelType(self):
        if isinstance(self._parm, hou.StringParmTemplate):
            return "chs"
        return "ch"

    @property
    def hdaGroup(self) -> Optional[hou.ParmTemplateGroup]:
        if self.envNode_parm.type().definition():
            return self.envNode_parm.type().definition().parmTemplateGroup()
        else:
            return None

    @property
    def refrencePath(self):
        return self.parm_node.relativePathTo(self.envNode_parm)

    @staticmethod
    def nodeCountMatch(node_path: str, re_expr: str) -> int:
        mat_net = hou.node(node_path)
        all_contets = mat_net.children()
        match = re.compile(re_expr)
        valid_nodes = {
            node for node in all_contets if re.findall(match, node.name())}
        return len(valid_nodes)

    @staticmethod
    def allNodeParms(node: hou.Node) -> Iterable[str]:
        to_check = [node.parmTemplateGroup(), ]
        node_type = node.type()
        node_def = node_type.definition()
        if node_def:
            to_check.append(node_def.parmTemplateGroup())
        for group in itertools.chain(to_check):
            for name in allParmTemplateNames(group):
                yield name
        else:
            return None

    @staticmethod
    def jumpToNode(env: str, parm_type: str) -> None:
        network_editor = hou.ui.paneTabUnderCursor()
        choice = hou.ui.displayCustomConfirmation(
            f"Active {parm_type} node path: {env}", buttons=("Jump to node", "Ok"))
        if choice == 0 and isinstance(network_editor, hou.NetworkEditor):
            node_obj = hou.node(env)
            network_editor.setCurrentNode(node_obj)
            network_editor.homeToSelection()

    @staticmethod
    def createSpareParmFromExpression(parms: Tuple, parm_type: hou.ParmTemplate, min: int = 1, max: int = 10) -> None:
        re_expr = re.compile(
            r"(?P<ch_type>chs?)\((?:'|\")(?P<parm_name>[A-Za-z0-9_ ]+)(?:'|\")\)")
        for parm in parms:
            if not parm.getReferencedParm() != parm:
                parm_temp = parm.parmTemplate()
                parm_expr = None
                node = parm.node()
                if isinstance(parm_temp, hou.StringParmTemplate):
                    parm_expr = parm.unexpandedString()
                else:
                    try:
                        parm_expr = parm.expression()
                    except hou.OperationFailed:
                        raise HoudiniError("No expression found")
                re_match = re.findall(re_expr, parm_expr)
                if re_match:
                    for parm in re_match:
                        parm_name = parm[1].strip()
                        group = node.parmTemplateGroup()
                        if not parm_type == hou.StringParmTemplate:
                            new_parm = parm_type(
                                parm_name, parm_name, 1, (0,), min, max)
                        else:
                            new_parm = parm_type(parm_name, parm_name, 1)
                        group.append(new_parm)
                        node.setParmTemplateGroup(group)
                else:
                    raise HoudiniError("Parm is controlled by some other parm")

    @staticmethod
    def invalidSchemes() -> Generator:
        schemes = ("XYWH", "BeginEnd", "StartEnd", "MinMax", "MaxMin")
        for scheme in schemes:
            yield getattr(hou.parmNamingScheme, scheme)

    def valid_temp(self, invalid_parm_node: hou.Node) -> hou.ParmTemplate:
        base_parm = self._parm
        name = base_parm.name()
        parm_names = set(parmUtils.allNodeParms(invalid_parm_node))
        if name in parm_names:
            strip_parm = re.sub(r"[\d_]+$", "",
                                self._parm.name(), flags=re.IGNORECASE)
            for id in itertools.count(0, 1):
                check = "".join((strip_parm, "_", str(id)))
                if check not in parm_names:
                    base_parm.setName(check)
                    break
        if base_parm.namingScheme() in parmUtils.invalidSchemes():
            base_parm.setNamingScheme(hou.parmNamingScheme.Base1)
            
        base_parm.setConditional(hou.parmCondType.HideWhen, "")
        return base_parm

    def createRelativeReference(self, assign_to_definition: bool = True) -> None:
        if self.envNode_parm:
            if not self.parm_inst.isMultiParmInstance():
                if self.hdaGroup:
                    if assign_to_definition:
                        set_on = self.envNode_parm.type().definition()
                    else:
                        set_on = self.envNode_parm
                else:
                    set_on = self.envNode_parm
                folder_id = self.parm_node.name()
                folder_id = folder_id.replace("/", "_").strip("_")
                group = set_on.parmTemplateGroup()
                if group.findFolder(folder_id):
                    found_folder = group.findFolder(folder_id)
                    group.appendToFolder(
                        found_folder, self.valid_temp(self.envNode_parm))
                    set_on.setParmTemplateGroup(
                        group, rename_conflicting_parms=True)
                else:
                    if self.hdaGroup and assign_to_definition:
                        if self.envNode_parm.parmTemplateGroup().findFolder(folder_id):
                            raise HoudiniError(
                                "Folder found in a spare parameters of the node")
                    new_folder = hou.FolderParmTemplate(
                        folder_id, folder_id, (self.valid_temp(self.envNode_parm),), folder_type=hou.folderType.Simple)
                    group.append(new_folder)
                    set_on.setParmTemplateGroup(
                        group, rename_conflicting_parms=True)

            else:
                raise HoudiniError("Parm is a multiparm instance")

            refeshed_folder = set_on.parmTemplateGroup().findFolder(folder_id)
            latest_temp = refeshed_folder.parmTemplates()[-1].name()
            parm_to_ref = self.envNode_parm.parmTuple(latest_temp)

            for to_set, to_fetch in zip(parm_to_ref, self.parm_tuple):
                to_set.set(to_fetch.eval())
                parm_name = to_set.name()
                parm_path = f"{self.channelType}(\"{self.refrencePath}/{parm_name}\")"
                if not isinstance(self.parm_inst.parmTemplate(), hou.RampParmTemplate):
                    to_fetch.setExpression(
                        parm_path, language=hou.exprLanguage.Hscript)

        else:
            raise HoudiniError("No parm enviroment parm found")

    def deleteParm(self):
        if not self.parm_tuple.isMultiParmInstance():
            if not isinstance(self.parm_tuple.parmTemplate(), hou.FolderSetParmTemplate):
                if self.parm_inst.isSpare():
                    for parm in self.parm_tuple:
                        for parm_ref in parm.parmsReferencingThis():
                            parm_ref.deleteAllKeyframes()
                    self.parm_node.removeSpareParmTuple(self.parm_tuple)
                    return
                if self.parm_node.type().definition():
                    group = self.parm_group
                    for parm in self.parm_tuple:
                        for parm_ref in parm.parmsReferencingThis():
                            parm_ref.deleteAllKeyframes()
                    group.remove(self._parm.name())
                    self.parm_node.type().definition().setParmTemplateGroup(group)
            else:
                raise HoudiniError("Can't delete folder")
        else:
            raise HoudiniError("Parm is a multiparm instance")

    @staticmethod
    def renameParms(kwargs):
        node = kwargs["node"]
        group = node.parmTemplateGroup()
        spare_names = [parm.parmTemplate().name()
                        for parm in node.spareParms()]
        all_templates = group.entries() + group.entriesWithoutFolders()
        for parm in all_templates:
            parm_name = parm.name()
            if parm_name in spare_names:
                original_parm = parm.name()
                parm_name = re.sub(r'\d+', '', original_parm)
                label = parm_name.replace("_", " ").title()
                parm.setLabel(label)
                group.replace(original_parm, parm)
        node.setParmTemplateGroup(group)



def ctrl_node_set(kwargs):
    node_path = kwargs['node'].path()
    node = hou.node(node_path)
    base_name = "CTRL"
    node_index = 1
    color_curr = hou.Color((0.996, 0.682, 0.682))
    color_prev = hou.Color((0.8, 0.2, 0.2))

    def autoRename(node, base_name):
        if node.name().startswith(base_name):
            pass
        else:
            node.setName(base_name, "{}{}".format(base_name, node_index + 1))

    def autoRenameChildren(node, base_name):
        for node in node.children():
            if node.name().startswith(base_name):
                try:
                    index = int(node.name()[len(base_name):])
                    node_index = max(node_index, index)
                except ValueError:
                    pass

    def hideNullParms(node):
        if type(node) == hou.SopNode:
            parms = node.parmTemplateGroup()
            copyinput_template = parms.find("copyinput")
            cacheinput_template = parms.find("cacheinput")
            if copyinput_template is not None:
                copyinput_template.hide(True)
            if cacheinput_template is not None:
                cacheinput_template.hide(True)
            if copyinput_template is not None:
                parms.replace("copyinput", copyinput_template)
            if cacheinput_template is not None:
                parms.replace("cacheinput", cacheinput_template)
            node.setParmTemplateGroup(parms)

    def saveParmNodePath(node):
        node_path = node.path()
        hou.hscript("set -g ctrl_node = {}".format(node_path))

    def setParmNodeColor(node):
        ctrl_node = hou.getenv('ctrl_node')

        for node in hou.node("/").allSubChildren():
            if node.name().startswith(base_name) and node.path() != ctrl_node:
                node.setColor(color_curr)
            elif node.name().startswith(base_name) and node.path() == ctrl_node:
                node.setColor(color_prev)

    autoRename(node, base_name)
    hideNullParms(node)
    saveParmNodePath(node)
    setParmNodeColor(node)



def ctrl_open_tab(kwargs):
    node = kwargs["node"]
    desktop = hou.ui.curDesktop()
    tab = desktop.paneTabOfType(hou.paneTabType.Parm)
    if tab != None:
        pane = tab.pane()
        tab = pane.createTab(hou.paneTabType.Parm)
        tab.setCurrentNode(node)
        tab.setPin(True)
        tab.setShowNetworkControls(False)
        pane.setShowPaneTabs(True)
    else:
        pane = desktop.createFloatingPane(hou.paneTabType.Parm)
        pane.setCurrentNode(node)
        pane.setPin(True)
        pane.setShowNetworkControls(False)