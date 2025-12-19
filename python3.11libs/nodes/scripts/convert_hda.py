import time
import hou
import glob
import os

_EXCLUDE_ELEMENTS = ["/opt/hfs", "OPlibSop", "SideFXLabs"]


class convertHDA():
    def __init__(self, kwargs):
        self.node = kwargs['node']
        self.toNotIncludeHDA = self.node
        self.originalSelection = hou.selectedNodes()
        
        try:
            self.geo = self.node.geometry()
        except (hou.OperationFailed, hou.ObjectWasDeleted):
            self.geo = None
        
        self.Mode = self.node.parm("Mode").eval()
        self.KeepHDA = self.node.parm("KeepHDA").eval()
        
        if self.Mode <= 2:
            self.KeepHDA = 0
        
        self.UseDefaultValues = self.node.parm("UseDefaultValues").eval()
        self.folderWithHDAs = hou.pwd().parm("folderWithHDAs").eval()
        self.folderExportTxt = hou.pwd().parm("folderExportTxt").eval()
        self.FileToDo = hou.pwd().parm("FileToDo").eval()
        self.FolderToDo = hou.pwd().parm("FolderToDo").eval()
        self.ConvertTXTtoHDA = hou.pwd().parm("ConvertTXTtoHDA").eval()
        self.Add_Suffix = 1
        
        self.ExcludeElements = list(_EXCLUDE_ELEMENTS)
        self.subSuffix = ""
        self.offset = 0
        
        if self.Add_Suffix == 1 or self.KeepHDA == 1:
            self.subSuffix = "_ConvertMeBackToHDA"
            self.backupSufix = "_IAMABACKUP"
        
        if self.KeepHDA == 1:
            self.offset = 2
        
        self.hdaFileExt = self._get_hda_file_extension()

    def _get_hda_file_extension(self):
        """Get HDA file extension based on license category."""
        try:
            license_category = str(hou.licenseCategory())
            if license_category == "licenseCategoryType.Commercial":
                return ".hda"
            elif license_category == "licenseCategoryType.Indie":
                return ".hdalc"
            elif license_category == "licenseCategoryType.Education":
                return ".hda"
            elif license_category in ["licenseCategoryType.ApprenticeHD", "licenseCategoryType.Apprentice"]:
                return ".hdanc"
        except Exception:
            pass
        return ".hda"

    def doAction(self):
        try:
            self.HDAs = self.getHDAs()
            
            if self.Mode >= 0 and self.Mode <= 2:
                if os.path.isdir(self.folderExportTxt):
                    self.ExportToTxtInsteadOfSpawningInScene = 0
                    self.ConvertStuff()
                else:
                    print(f"Nothing exported. Does this folder exist: \"{self.folderExportTxt}\"?")
            
            if self.Mode >= 4 and self.Mode <= 6:
                self.ExportToTxtInsteadOfSpawningInScene = 0
                self.ConvertStuff()
            
            if self.Mode >= 8 and self.Mode <= 9:
                self.ExportToTxtInsteadOfSpawningInScene = 0
                self.ImportStuff()
            
            print("done!")
        except Exception as e:
            print(f"Error in doAction: {e}")

    def ImportStuff(self):
        try:
            self.allNodes = hou.node("/obj").allSubChildren()
            
            if self.Mode == 8:
                try:
                    with open(self.FileToDo, 'r') as in_file:
                        test = in_file.read()
                        test = test.split("\n\n")
                        codeDoneSoFar = ""
                        previousParent = "/obj"
                        for x in test:
                            try:
                                exec(x)
                                codeDoneSoFar += "\n\n" + x
                            except Exception as e:
                                print(f"Failed to execute: {e}")
                                print(x)
                except (IOError, OSError) as e:
                    print(f"Error reading file: {e}")
            
            if self.Mode == 9:
                if self.FolderToDo != "":
                    filesInFolder = glob.glob(self.FolderToDo + "/*.txt")
                    self.Mode = 8
                    for item in filesInFolder:
                        self.FileToDo = item
                        self.ImportStuff()
            
            allNewNodes = self.getNewNodes()
            
            if self.UseDefaultValues == 1:
                self.SetToDefaults(allNewNodes)
            
            if self.ConvertTXTtoHDA == 1:
                self.ConvertTXTHDA(allNewNodes)
        except Exception as e:
            print(f"Error in ImportStuff: {e}")

    def ExportStuff(self):
        try:
            namesHDAs = []
            pathsHDAs = []
            filePathsHDAs = []
            
            for HDA in self.HDAs:
                if not HDA or not HDA.isValid():
                    continue
                try:
                    namesHDAs.append(HDA.name())
                    pathsHDAs.append(HDA.path())
                    defi = HDA.type().definition()
                    if defi:
                        filePathsHDAs.append(defi.libraryFilePath())
                except (hou.ObjectWasDeleted, AttributeError):
                    continue
            
            selectedNodes = []
            if self.Mode == 0:
                selectedNodesTmp = hou.selectedNodes()
                for node in selectedNodesTmp:
                    if node and node.isValid() and node != self.toNotIncludeHDA:
                        selectedNodes.append(node)
            
            parents = []
            names = []
            
            for HDA in self.HDAs:
                if not HDA or not HDA.isValid():
                    continue
                try:
                    parent_path = HDA.parent().path()
                    if parent_path not in parents:
                        parents.append(parent_path)
                        names.append(HDA.parent().name())
                except (hou.ObjectWasDeleted, AttributeError):
                    continue
            
            for node in hou.selectedNodes():
                if not node or not node.isValid():
                    continue
                try:
                    parent_path = node.parent().path()
                    if parent_path not in parents:
                        parents.append(parent_path)
                        names.append(node.parent().name())
                except (hou.ObjectWasDeleted, AttributeError):
                    continue
            
            targets = []
            for parent_path in parents:
                try:
                    parent = hou.node(parent_path)
                    if not parent or not parent.isValid():
                        continue
                    uberparent = parent.parent()
                    if uberparent and "/obj" in uberparent.path():
                        target = hou.copyNodesTo([parent], uberparent)[0]
                        childrenTarget = target.children()
                        for child in childrenTarget:
                            if child.name() == self.toNotIncludeHDA.name():
                                child.destroy()
                                hou.moveNodesTo([self.toNotIncludeHDA], target)
                                break
                        target.setName(target.name() + self.backupSufix)
                        targets.append(target)
                except (hou.ObjectWasDeleted, hou.OperationFailed):
                    continue
            
            for parent_path in parents:
                try:
                    parent = hou.node(parent_path)
                    if not parent or not parent.isValid():
                        continue
                    children = parent.children()
                    for child in children:
                        if not child or not child.isValid():
                            continue
                        if self.Mode == 0 or self.Mode == 2:
                            if child not in self.HDAs:
                                child.destroy()
                        if self.Mode == 1:
                            if child not in selectedNodes:
                                child.destroy()
                except (hou.ObjectWasDeleted, hou.OperationFailed):
                    continue
            
            self.ExportToTxtInsteadOfSpawningInScene = 0
            self.ConvertStuff()
            
            if self.Mode == 0 or self.Mode == 2:
                counter = 0
                self.HDAs.reverse()
                for HDA in self.HDAs:
                    if not HDA or not HDA.isValid():
                        continue
                    try:
                        if counter < len(filePathsHDAs):
                            file_path = filePathsHDAs[counter].split("/")
                            file_name = file_path[len(file_path) - 1].split(".hda")[0]
                            targetTxt = self.folderExportTxt + "/" + file_name + ".txt"
                            target_node = hou.node(pathsHDAs[counter] + self.subSuffix)
                            if target_node and target_node.isValid():
                                self.writeNodeToTxt(target_node, targetTxt)
                        counter += 1
                    except (hou.ObjectWasDeleted, IndexError, AttributeError):
                        continue
                
                for parent_path in parents:
                    try:
                        parent = hou.node(parent_path)
                        if parent and parent.isValid():
                            parent.destroy()
                    except (hou.ObjectWasDeleted, hou.OperationFailed):
                        continue
            
            if self.Mode == 1:
                try:
                    hipName = hou.hipFile.name().split("/")
                    hipName = hipName[len(hipName) - 1].split(".hip")[0]
                    for parent_path in parents:
                        try:
                            parent = hou.node(parent_path)
                            if not parent or not parent.isValid():
                                continue
                            if self.Mode == 1:
                                targetTxt = self.folderExportTxt + "/" + hipName + "_" + parent.name() + "_SelectedNodes.txt"
                            if self.Mode == 3:
                                targetTxt = self.folderExportTxt + "/" + hipName + "_" + parent.name() + "_AllNodes.txt"
                            self.writeNodeToTxt(parent, targetTxt)
                            parent.destroy()
                        except (hou.ObjectWasDeleted, hou.OperationFailed):
                            continue
                except (AttributeError, IndexError):
                    pass
            
            counter = 0
            for target in targets:
                if not target or not target.isValid():
                    continue
                try:
                    if counter < len(names):
                        target.setName(names[counter])
                    counter += 1
                except (hou.ObjectWasDeleted, hou.OperationFailed, IndexError):
                    continue
        except Exception as e:
            print(f"Error in ExportStuff: {e}")

    def ConvertStuff(self):
        print("###################")
        print("To convert HDAs :")
        print(self.HDAs)
        print("###################")
        
        targetsToKeep = []
        counter = 0
        
        for HDA in self.HDAs:
            if not HDA or not HDA.isValid():
                continue
            try:
                defi = HDA.type().definition()
                if not defi:
                    continue
                path = defi.libraryFilePath()
                path = path.split("/")
                sourceName = path[len(path) - 1].split(".hda")[0]
                hou_parent = HDA.parent()
                target = self.setupNewthing(HDA, hou_parent, 0)
                children = self.getHDAsInNode(target)
                
                while children:
                    tmpChildren = []
                    for child in children:
                        if not child or not child.isValid():
                            continue
                        target = self.setupNewthing(child, target, 1)
                        tmpChildren += self.getHDAsInNode(target)
                        targetsToKeep.append(target)
                    children = tmpChildren
                
                if self.Mode == 0 or self.Mode == 1:
                    targetTxt = self.folderExportTxt + "/" + sourceName + ".txt"
                    self.writeNodeToTxt(hou_parent, targetTxt)
                counter += 1
            except (hou.ObjectWasDeleted, hou.OperationFailed, AttributeError, IndexError) as e:
                print(f"Error converting HDA: {e}")
                continue
        
        if self.Mode == 2:
            try:
                sourceName = hou.hipFile.name().split("/")
                sourceName = sourceName[len(sourceName) - 1].split(".hip")[0]
                hou.hipFile.save(file_name=hou.hipFile.name().replace(".hip", "_convertedHDAs.hip"))
                targetTxt = self.folderExportTxt + "/" + sourceName + ".txt"
                self.writeNodeToTxt(hou.node("/"), targetTxt)
            except (AttributeError, IndexError, hou.OperationFailed) as e:
                print(f"Error saving converted HDAs: {e}")

    def getNewNodes(self):
        try:
            List1 = list(hou.node("/obj").allSubChildren())
            List2 = list(self.allNodes)
            allNewNodes = []
            
            for item in List1:
                if item not in List2:
                    if self.subSuffix in item.name():
                        allNewNodes.append(item)
            
            return allNewNodes
        except (hou.ObjectWasDeleted, AttributeError):
            return []

    def SetToDefaults(self, allNewNodes):
        for node in allNewNodes:
            if not node or not node.isValid():
                continue
            try:
                parms = node.parms()
                for parm in parms:
                    try:
                        parm.revertToDefaults()
                        parm.deleteAllKeyframes()
                        parm.revertToDefaults()
                        parm.revertToRampDefaults()
                    except (hou.OperationFailed, AttributeError):
                        pass
            except (hou.ObjectWasDeleted, AttributeError):
                continue

    def ConvertTXTHDA(self, allNewNodes):
        try:
            lenghts = []
            counter = 0
            
            for node in allNewNodes:
                if not node or not node.isValid():
                    continue
                try:
                    pathPArent = len(node.path().split("/"))
                    lenghts.append(pathPArent)
                    allNewNodes[counter] = node.path()
                    counter += 1
                except (hou.ObjectWasDeleted, AttributeError):
                    continue
            
            lenghts, allNewNodes = zip(*sorted(zip(lenghts, allNewNodes)))
            allNewNodes = list(allNewNodes)
            allNewNodes.reverse()
            
            counter = 0
            for path in allNewNodes:
                try:
                    allNewNodes[counter] = hou.node(path)
                    counter += 1
                except (hou.ObjectWasDeleted, hou.OperationFailed):
                    continue
            
            for item in allNewNodes:
                if not item or not item.isValid():
                    continue
                try:
                    name = item.name().replace(self.subSuffix, "")
                    item.setName(name)
                    
                    libraryFilePath = item.parm("libraryFilePath").eval()
                    minNumInputs = item.parm("minNumInputs").eval()
                    maxNumInputs = item.parm("maxNumInputs").eval()
                    comment = item.parm("comment").eval()
                    version = item.parm("version").eval()
                    isCreateBackupsEnabled = item.parm("isCreateBackupsEnabled").eval()
                    
                    da = item.createDigitalAsset(
                        name=name,
                        hda_file_name=self.folderWithHDAs + "/" + name + self.hdaFileExt,
                        version=version,
                        comment=comment,
                        max_num_inputs=maxNumInputs,
                        min_num_inputs=minNumInputs
                    )
                    
                    if maxNumInputs > 4:
                        for x in range(0, maxNumInputs):
                            try:
                                node = hou.node(da.path() + "/" + "tmpConnectTo_" + str(x))
                                node.setInput(0, da.indirectInputs()[x])
                                node.destroy()
                            except (hou.ObjectWasDeleted, hou.OperationFailed, IndexError):
                                pass
                    
                    inputsForHDAConvert = da.parm("inputsForHDAConvert").eval()
                    inputsForHDAConvert = inputsForHDAConvert.split(" ")
                    
                    if len(inputsForHDAConvert) == int(maxNumInputs):
                        for x in range(int(maxNumInputs)):
                            if inputsForHDAConvert[x] not in ["/", " ", ""]:
                                try:
                                    da.setInput(x, hou.node(inputsForHDAConvert[x]))
                                except (hou.ObjectWasDeleted, hou.OperationFailed):
                                    pass
                    
                    parmTemplateGroup = da.parmTemplateGroup()
                    entriesTmp = parmTemplateGroup.entries()
                    
                    for entry in entriesTmp:
                        entry_name = entry.name()
                        if any(keyword in entry_name for keyword in [
                            "minNumInputs", "maxNumInputs", "comment", "version",
                            "isCreateBackupsEnabled", "nInputsSourceForHDAConvert",
                            "inputsForHDAConvert", "libraryFilePath"
                        ]):
                            parmTemplateGroup.remove(entry)
                    
                    da.setParmTemplateGroup(parmTemplateGroup)
                    da.type().definition().updateFromNode(da)
                    da.matchCurrentDefinition()
                except (hou.ObjectWasDeleted, hou.OperationFailed, AttributeError) as e:
                    print(f"Error converting TXT to HDA: {e}")
                    continue
        except Exception as e:
            print(f"Error in ConvertTXTHDA: {e}")

    def checkLicense(self):
        try:
            return hou.licenseCategory()
        except Exception:
            return None

    def importTXT(self, fileToDo):
        try:
            with open(fileToDo, 'r') as in_file:
                test = in_file.read()
                test = test.split("\n\n")
                for x in test:
                    try:
                        exec(x)
                    except Exception as e:
                        print(f"Error executing code: {e}")
        except (IOError, OSError) as e:
            print(f"Error reading file: {e}")

    def addChildren(self, node):
        if not node or not node.isValid():
            return [], []
        
        try:
            children = node.allSubChildren()
            tmpChildrenToAdd = []
            HDAsToCopyToNewToAdd = []
            
            for child in children:
                if not child or not child.isValid():
                    continue
                
                OK = 1
                try:
                    defi = child.type().definition()
                    if defi is not None:
                        for element in self.ExcludeElements:
                            if element in str(defi):
                                OK = 0
                                break
                    else:
                        OK = 0
                except (AttributeError, hou.ObjectWasDeleted):
                    OK = 0
                
                if OK == 1:
                    tmpChildrenToAdd.append(child)
                    HDAsToCopyToNewToAdd.append(0)
            
            return tmpChildrenToAdd, HDAsToCopyToNewToAdd
        except (hou.ObjectWasDeleted, AttributeError):
            return [], []

    def setupNewthing(self, HDA, hou_parent, mode):
        if not HDA or not HDA.isValid():
            return None
        
        try:
            defi = HDA.type().definition()
            if not defi:
                return None
            
            libraryFilePath = defi.libraryFilePath()
            minNumInputs = defi.minNumInputs()
            maxNumInputs = defi.maxNumInputs()
            comment = defi.comment()
            version = defi.version()
            isCreateBackupsEnabled = defi.isCreateBackupsEnabled()
            
            sourceName = HDA.name()
            wasBypassed = self.forceCook(HDA)
            
            if mode == 0 and self.ExportToTxtInsteadOfSpawningInScene == 1:
                hou_parent.setName(sourceName + "_sub")
                source = hou.copyNodesTo([HDA], hou_parent)[0]
            else:
                source = HDA
            
            nInputsSource = len(HDA.inputs())
            inputs = ""
            
            for input_node in HDA.inputs():
                try:
                    if input_node and input_node.isValid():
                        inputs += input_node.path() + " "
                    else:
                        inputs += "/ "
                except (hou.ObjectWasDeleted, AttributeError):
                    inputs += "/ "
            
            wasBypassed = self.forceCook(source)
            parms = source.parms()
            group = source.parmTemplateGroup()
            path = source.parent().path()
            inputConnections = source.inputConnections()
            outputConnections = source.outputConnections()
            
            target = self.setupTarget(group, source, wasBypassed, path, sourceName)
            if not target:
                return None
            
            self.runThroughParms(parms, source, target)
            childrenSource = self.connections(inputConnections, outputConnections, source, target, mode)
            self.setupParms(target)
            target.setName(sourceName + self.subSuffix)
            
            if self.KeepHDA == 0 or mode == 1:
                self.cleanup([source])
            
            wasBypassed = self.forceCook(target)
            
            g = target.parmTemplateGroup()
            p = hou.IntParmTemplate("nInputsSourceForHDAConvert", "nInputsSourceForHDAConvert", 1, default_value=[nInputsSource])
            g.append(p)
            p = hou.StringParmTemplate("inputsForHDAConvert", "inputsForHDAConvert", 1, default_value=[inputs])
            g.append(p)
            p = hou.StringParmTemplate("libraryFilePath", "libraryFilePath", 1, default_value=[libraryFilePath])
            g.append(p)
            p = hou.StringParmTemplate("comment", "comment", 1, default_value=[comment])
            g.append(p)
            p = hou.StringParmTemplate("version", "version", 1, default_value=[version])
            g.append(p)
            p = hou.IntParmTemplate("minNumInputs", "minNumInputs", 1, default_value=[minNumInputs])
            g.append(p)
            p = hou.IntParmTemplate("maxNumInputs", "maxNumInputs", 1, default_value=[maxNumInputs])
            g.append(p)
            p = hou.IntParmTemplate("isCreateBackupsEnabled", "isCreateBackupsEnabled", 1, default_value=[isCreateBackupsEnabled])
            g.append(p)
            
            try:
                target.setParmTemplateGroup(g)
                if self.UseDefaultValues == 1:
                    self.SetToDefaults([target])
            except (hou.OperationFailed, AttributeError):
                pass
            
            return target
        except (hou.ObjectWasDeleted, hou.OperationFailed, AttributeError) as e:
            print(f"Error in setupNewthing: {e}")
            return None

    def getHDAsInNode(self, HDA):
        if not HDA or not HDA.isValid():
            return []
        
        try:
            children = HDA.children()
            childrenHDA = []
            
            for child in children:
                if not child or not child.isValid():
                    continue
                
                OK = 1
                try:
                    defi = child.type().definition()
                    if defi is not None:
                        for element in self.ExcludeElements:
                            if element in str(defi):
                                OK = 0
                                break
                    else:
                        OK = 0
                except (AttributeError, hou.ObjectWasDeleted):
                    OK = 0
                
                if OK == 1:
                    childrenHDA.append(child)
            
            return childrenHDA
        except (hou.ObjectWasDeleted, AttributeError):
            return []

    def forceCook(self, source):
        if not source or not source.isValid():
            return 0
        
        wasBypassed = 0
        try:
            if source.isBypassed():
                wasBypassed = 1
                try:
                    source.bypass(0)
                except (hou.OperationFailed, hou.ObjectWasDeleted):
                    pass
        except (hou.ObjectWasDeleted, AttributeError):
            pass
        
        try:
            source.bypass(wasBypassed)
        except (hou.OperationFailed, hou.ObjectWasDeleted):
            pass
        
        try:
            source.cook(force=True)
        except (hou.OperationFailed, hou.ObjectWasDeleted):
            pass
        
        return wasBypassed

    def setupTarget(self, group, source, wasBypassed, path, sourceName):
        try:
            target_path = path + "/" + sourceName + self.subSuffix
            target = hou.node(target_path)
            if target and target.isValid():
                target.destroy()
        except (hou.ObjectWasDeleted, hou.OperationFailed):
            pass
        
        try:
            color = source.color()
            position = source.position()
            position[0] += self.offset
            target = hou.node(path).createNode("subnet")
            target.setParmTemplateGroup(group)
            target.setColor(color)
            target.setPosition(position)
            target.bypass(wasBypassed)
            return target
        except (hou.ObjectWasDeleted, hou.OperationFailed, AttributeError):
            return None

    def runThroughParms(self, parms, source, target):
        if not source or not source.isValid() or not target or not target.isValid():
            return
        
        for parm in parms:
            try:
                code = parm.parmTemplate().asCode()
                exec(code)
                value = parm.eval()
                name = parm.name()
                target_parm = target.parm(name)
                
                if target_parm is not None:
                    target_parm.set(value)
                
                code = parm.asCode()
                code = code.replace("    hou_node", "    pass#hou_node")
                code = code.replace("hou_node.", "target.")
                
                try:
                    exec(code)
                except (AttributeError, TypeError):
                    pass
                
                code = code.split("\n")
                for c in code:
                    if "hou_parm = " in c:
                        line = c.replace("target.", "source.")
                        try:
                            exec("global hou_parm;" + line)
                            global hou_parm
                            if hou_parm is not None:
                                value = hou_parm.eval()
                                try:
                                    exec(c)
                                except (AttributeError, TypeError):
                                    pass
                        except (AttributeError, TypeError, NameError):
                            pass
                    elif "hou_parm.set" in c:
                        line1 = "hou_parm.set(\"" + str(value) + "\")"
                        line2 = "hou_parm.set(" + str(value) + ")"
                        line3 = "hou_parm.set(r\"" + str(value) + "\")"
                        try:
                            exec(line1)
                        except Exception:
                            try:
                                exec(line2)
                            except Exception:
                                try:
                                    exec(line3)
                                except Exception:
                                    pass
            except (hou.ObjectWasDeleted, AttributeError, hou.OperationFailed):
                continue

    def connections(self, inputConnections, outputConnections, source, target, mode):
        if not source or not source.isValid() or not target or not target.isValid():
            return []
        
        try:
            if self.ExportToTxtInsteadOfSpawningInScene == 0 or mode == 1:
                self.setupConnections(inputConnections, source, target)
            
            childrenSource = source.children()
            hou.copyNodesTo(childrenSource, target)
            
            if self.ExportToTxtInsteadOfSpawningInScene == 0 or mode == 1:
                self.setupConnections(outputConnections, source, target)
            
            counter = 0
            childrenInTarget = source.children()
            sourceIndirects = source.indirectInputs()
            targetIndirects = target.indirectInputs()
            inputsDone = []
            nullsForInputs = []
            
            try:
                defi = source.type().definition()
                if not defi:
                    return childrenSource
                maxNumInputs = defi.maxNumInputs()
            except (AttributeError, hou.ObjectWasDeleted):
                return childrenSource
            
            try:
                tmpNull = source.parent().createNode("null")
                for x in range(maxNumInputs):
                    inputNode = source.input(x)
                    if not inputNode:
                        inputNode = tmpNull
                        source.setInput(x, tmpNull, output_index=0)
            except (hou.ObjectWasDeleted, hou.OperationFailed):
                tmpNull = None
            
            for child in childrenInTarget:
                if not child or not child.isValid():
                    continue
                try:
                    inputConnections = child.inputConnections()
                    for input_conn in inputConnections:
                        if input_conn.subnetIndirectInput():
                            try:
                                targetChild = hou.node(child.path().replace(source.path(), target.path()))
                                if not targetChild or not targetChild.isValid():
                                    continue
                                
                                input_num = input_conn.subnetIndirectInput().number()
                                if input_num not in inputsDone:
                                    null = target.createNode("null")
                                    null.setName("tmpConnectTo_" + str(input_num + 0))
                                    if input_num < 4:
                                        null.setInput(0, targetIndirects[input_num])
                                    nullsForInputs.append(null)
                                    inputsDone.append(input_num)
                                else:
                                    null = nullsForInputs[inputsDone.index(input_num)]
                                
                                targetChild.setInput(input_conn.inputIndex(), null)
                                counter += 1
                            except (hou.ObjectWasDeleted, hou.OperationFailed, IndexError, AttributeError):
                                continue
                except (hou.ObjectWasDeleted, AttributeError):
                    continue
            
            if tmpNull:
                try:
                    tmpNull.destroy()
                except (hou.ObjectWasDeleted, hou.OperationFailed):
                    pass
            
            return childrenSource
        except (hou.ObjectWasDeleted, hou.OperationFailed, AttributeError) as e:
            print(f"Error in connections: {e}")
            return []

    def cleanup(self, targets):
        for target in targets:
            if not target or not target.isValid():
                continue
            try:
                target.destroy()
            except (hou.ObjectWasDeleted, hou.OperationFailed):
                pass
        
        for node in self.originalSelection:
            if not node or not node.isValid():
                continue
            try:
                node.setSelected(True, clear_all_selected=False)
            except (hou.ObjectWasDeleted, hou.OperationFailed):
                pass

    def setupParms(self, target):
        if not target or not target.isValid():
            return
        
        try:
            parmTemplateGroup = target.parmTemplateGroup()
            Standard = parmTemplateGroup.findFolder("Standard")
            
            if Standard:
                StandardParmTemplats = Standard.parmTemplates()
            else:
                StandardParmTemplats = []
            
            Spare = parmTemplateGroup.findFolder("Spare")
            if Spare:
                SpareParmTemplats = Spare.parmTemplates()
                group = hou.ParmTemplateGroup(StandardParmTemplats + SpareParmTemplats)
                target.setParmTemplateGroup(group)
            
            if "/obj" in target.path():
                try:
                    for label in ["label1", "label2", "label3", "label4"]:
                        parm = target.parm(label)
                        if parm:
                            parm.hide("on")
                except (AttributeError, hou.OperationFailed):
                    pass
        except (hou.ObjectWasDeleted, AttributeError, hou.OperationFailed):
            pass

    def setupConnections(self, connections, source, target):
        if not source or not source.isValid() or not target or not target.isValid():
            return
        
        for connection in connections:
            try:
                inputNode = connection.inputNode()
                outputNode = connection.outputNode()
                inputIndex = connection.inputIndex()
                outputIndex = connection.outputIndex()
                
                if inputNode == source:
                    inputNode = target
                if outputNode == source:
                    outputNode = target
                
                if inputNode and inputNode.isValid() and outputNode and outputNode.isValid():
                    outputNode.setInput(inputIndex, inputNode, outputIndex)
            except (hou.ObjectWasDeleted, hou.OperationFailed, AttributeError):
                continue

    def writeNodeToTxt(self, node, txtFile):
        if not node or not node.isValid():
            return
        
        try:
            codeString = node.asCode(
                brief=True,
                recurse=True,
                save_creation_commands=True,
                save_spare_parms=True,
                save_keys_in_frames=True
            )
            
            with open(txtFile, "w") as text_file:
                text_file.write("")
            
            with open(txtFile, "a") as text_file:
                text_file.write(codeString)
            
            print("###########")
            print("printed to ")
            print(txtFile)
            print("###########")
        except (hou.ObjectWasDeleted, hou.OperationFailed, IOError, OSError) as e:
            print(f"Error writing to file: {e}")

    def getHDAs(self):
        HDAsTmp = []
        hdasToInstall = []
        allNodes = []
        allNodes = hou.selectedNodes()
        
        if self.Mode == 1 or self.Mode == 2 or self.Mode == 5:
            try:
                allNodes = hou.node("/").allSubChildren()
            except (hou.ObjectWasDeleted, AttributeError):
                allNodes = []
        elif self.Mode == 7:
            try:
                filesInFolder = glob.glob(self.folderWithHDAs + "/*.*")
                for file in filesInFolder:
                    if any(ext in file for ext in [".hda", ".hdalc", ".hdanc"]):
                        hdasToInstall.append(file)
                
                for hda in hdasToInstall:
                    try:
                        hou.hda.installFile(
                            hda,
                            oplibraries_file=None,
                            change_oplibraries_file=True,
                            force_use_assets=False
                        )
                        basename = os.path.basename(hda)
                        root, ext = os.path.splitext(basename)
                        hdaNode = hou.node(hou.pwd().parent().path()).createNode(root)
                        try:
                            hdaNode.cook(force=True)
                        except (hou.OperationFailed, hou.ObjectWasDeleted):
                            pass
                        allNodes.append(hdaNode)
                    except (hou.OperationFailed, hou.ObjectWasDeleted, AttributeError):
                        continue
            except Exception as e:
                print(f"Error installing HDAs: {e}")
        
        if self.Mode == 0 or self.Mode == 1:
            HDAsToDo = []
        
        for node in allNodes:
            if not node or not node.isValid():
                continue
            
            OK = 1
            try:
                defi = node.type().definition()
                if defi is not None:
                    if self.Mode == 0 or self.Mode == 1:
                        path = defi.libraryFilePath()
                        if path in HDAsToDo:
                            OK = 0
                            print(f"found multiple instances of {path}")
                            print("only converting 1")
                        else:
                            HDAsToDo.append(path)
                    
                    for element in self.ExcludeElements:
                        if element in str(defi):
                            OK = 0
                            break
                else:
                    OK = 0
            except (AttributeError, hou.ObjectWasDeleted):
                OK = 0
            
            if node == self.toNotIncludeHDA:
                OK = 0
            
            if OK == 1:
                try:
                    parentPath = node.parent().path().split("/")
                    previousPath = ""
                    for path_segment in parentPath:
                        previousPath += "/" + path_segment
                        previousPath = previousPath.replace("//", "/")
                        newnode = hou.node(previousPath)
                        if newnode and newnode.isValid() and "None" not in str(newnode):
                            defi = newnode.type().definition()
                            if defi is not None:
                                OK = 0
                                break
                except (hou.ObjectWasDeleted, AttributeError):
                    pass
            
            if OK == 1:
                HDAsTmp.append(node)
        
        allNodes = HDAsTmp
        return allNodes
