####################
# Todo
# multi hda created per to convert subnetwork
# null input connections fails when connected to single hda input
####################
import time, hou,glob,os
global hou_parm_template
global hou_parm
##################################
class convertHDA():
    ##################################
    def __init__(self,kwargs):
        self.node = kwargs['node']
        self.toNotIncludeHDA=self.node
        self.originalSelection=hou.selectedNodes()
        self.geo = self.node.geometry()
        self.Mode = self.node.parm("Mode").eval()
        #self.ExportToTxtInsteadOfSpawningInScene = self.node.parm("ExportToTxtInsteadOfSpawningInScene").eval()
        #self.ConvertChildrenHDAs = self.node.parm("ConvertChildrenHDAs").eval()
        self.KeepHDA = self.node.parm("KeepHDA").eval()
        if self.Mode<=2:
            self.KeepHDA=0
        self.UseDefaultValues = self.node.parm("UseDefaultValues").eval()
        self.folderWithHDAs = hou.pwd().parm("folderWithHDAs").eval()
        self.folderExportTxt = hou.pwd().parm("folderExportTxt").eval()
        self.FileToDo = hou.pwd().parm("FileToDo").eval()
        self.FolderToDo = hou.pwd().parm("FolderToDo").eval()
        self.ConvertTXTtoHDA = hou.pwd().parm("ConvertTXTtoHDA").eval()
        self.Add_Suffix = 1#hou.pwd().parm("Add_Suffix").eval()
        self.ExcludeElements = []
        self.ExcludeElements.append("/opt/hfs")
        self.ExcludeElements.append("OPlibSop")
        self.ExcludeElements.append("SideFXLabs")
        self.subSuffix=""
        self.offset=0
        if self.Add_Suffix==1 or self.KeepHDA==1:
            self.subSuffix ="_ConvertMeBackToHDA"
            self.backupSufix ="_IAMABACKUP"
        if self.KeepHDA==1:
            self.offset=2
        print("license")
        print(hou.licenseCategory())
        if(str(hou.licenseCategory())=="licenseCategoryType.Commercial"):
            self.hdaFileExt = ".hda"
        if(str(hou.licenseCategory())=="licenseCategoryType.Indie"):
            self.hdaFileExt = ".hdalc"
        if(str(hou.licenseCategory())=="licenseCategoryType.Education"):
            self.hdaFileExt = ".hda"
        if(str(hou.licenseCategory())=="licenseCategoryType.ApprenticeHD"):
            self.hdaFileExt = ".hdanc"
        if(str(hou.licenseCategory())=="licenseCategoryType.Apprentice"):
            self.hdaFileExt = ".hdanc"
        print("self.hdaFileExt")
        print(self.hdaFileExt)

    ##################################
    def doAction(self):
        self.HDAs = self.getHDAs()
        print("self.Mode")
        print(self.Mode)
        #with hou.undos.group("test"):
        if self.Mode>=0 and self.Mode<=2:
            if(os.path.isdir(self.folderExportTxt )):
                self.ExportToTxtInsteadOfSpawningInScene=0
                self.ConvertStuff()
            else:
                print("Nothing exported. Does this folder exist :\""+self.folderExportTxt+"\" ?")
        if self.Mode>=4 and self.Mode<=6:
            self.ExportToTxtInsteadOfSpawningInScene=0
            self.ConvertStuff()
        if self.Mode>=8 and self.Mode<=9:
            self.ExportToTxtInsteadOfSpawningInScene=0
            self.ImportStuff()
        #hou.undos.add("test","test")
        #hou.undos.performUndo()
        print("done!")
        print("##########################")
        print("##########################")
    ##################################
    def ImportStuff(self):
        self.allNodes = hou.node("/obj").allSubChildren()
        if self.Mode==8:
            in_file = open(self.FileToDo)
            test  = in_file.read()
            test = test.split("\n\n")
            codeDoneSoFar=""
            previousParent = "/obj"
            for x in test:
                try:       
                    exec(x)
                    codeDoneSoFar+="\n\n"+x
                except:
                    print("Failed")
                    print(x)
        if self.Mode==9:
            if(self.FolderToDo!=""):
                filesInFolder = glob.glob(self.FolderToDo+"/*.txt")
                self.Mode=8
                for item in filesInFolder:
                    self.FileToDo =item
                    self.ImportStuff()
        allNewNodes = self.getNewNodes()
        if(self.UseDefaultValues==1):
            self.SetToDefaults(allNewNodes)
        if(self.ConvertTXTtoHDA==1):
            self.ConvertTXTHDA(allNewNodes)
    ##################################
    def ExportStuff(self):
        """
        defi = node.type().definition()
            if defi is not None :
                if(self.Mode==0 or self.Mode==1):
                    path=defi.libraryFilePath()
        """
        namesHDAs = []
        pathsHDAs=[]
        filePathsHDAs=[]
        for HDA in self.HDAs:
            namesHDAs.append(HDA.name())
            pathsHDAs.append(HDA.path())
            defi = node.type().definition()
            filePathsHDAs.append(defi.libraryFilePath())
            
        selectedNodes=[]
        if self.Mode==0:#or self.Mode==1:
            selectedNodesTmp = hou.selectedNodes()
            for node in selectedNodesTmp:
                if node!=self.toNotIncludeHDA:
                    selectedNodes.append(node)

        parents=[]
        names=[]
        for HDA in self.HDAs:
          if HDA.parent().path() not in parents:
                parents.append(HDA.parent().path())
                names.append(HDA.parent().name())
        for node in hou.selectedNodes():
            if node.parent().path() not in parents:
                parents.append(node.parent().path())
                names.append(node.parent().name())

        targets=[]
        for parent in parents:
            parent=hou.node(parent)
            uberparent = parent.parent()
            if "/obj" in uberparent.path():
                target = hou.copyNodesTo([parent],uberparent)[0]
                childrenTarget = target.children()
                for child in childrenTarget:
                    if child.name()==self.toNotIncludeHDA.name():
                        child.destroy()
                        hou.moveNodesTo([self.toNotIncludeHDA],target)
                        break
                target.setName(target.name()+self.backupSufix)
                targets.append(target)
        
        for parent in parents:
            children = hou.node(parent).children()
            for child in children:
                if self.Mode==0 or self.Mode==2:
                    if child not in self.HDAs:
                        child.destroy()
                if self.Mode==1:
                    if child not in selectedNodes:
                        child.destroy()
        self.ExportToTxtInsteadOfSpawningInScene=0
        self.ConvertStuff()
        
        if self.Mode==0 or self.Mode==2:
            counter=0
            self.HDAs.reverse()
            HDAsDone=[]
            for HDA in self.HDAs:
                #targetTxt = self.folderExportTxt+"/"+namesHDAs[counter]+".txt"
                filePathsHDAs[counter].split("/")
                filePathsHDAs=filePathsHDAs[len(filePathsHDAs)-1].split(".hda")[0]
                targetTxt = self.folderExportTxt+"/"+filePathsHDAs+".txt"
                print("targetTxt")
                print(targetTxt)
                self.writeNodeToTxt(hou.node(pathsHDAs[counter]+self.subSuffix),targetTxt)
                counter+=1
            for parent in parents:
                parent=hou.node(parent).destroy()
                
        if self.Mode==1:
            hipName = hou.hipFile.name().split("/")
            hipName = hipName[len(hipName)-1].split(".hip")[0]
            for parent in parents:
                parent=hou.node(parent)
                if self.Mode==1:
                    targetTxt = self.folderExportTxt+"/"+hipName+"_"+parent.name()+"_SelectedNodes.txt"
                if self.Mode==3:
                    targetTxt = self.folderExportTxt+"/"+hipName+"_"+parent.name()+"_AllNodes.txt"
                self.writeNodeToTxt(parent,targetTxt)
                parent.destroy()
        counter=0
        for target in targets:
            target.setName(names[counter])#.removesuffix(self.backupSufix))
            counter+=1
        
    ##################################
    def ConvertStuff(self):
        print("###################")
        print("To convert HDAs :")
        print(self.HDAs)
        print("###################")
        targetsToKeep=[]
        counter=0
        #hou_parent = hou.node("/obj").createNode("geo")
        for HDA in self.HDAs:
            path = HDA.type().definition().libraryFilePath()
            path= path.split("/")
            sourceName=path[len(path)-1].split(".hda")[0]
            #targetTxt = self.folderExportTxt+"/"+filePathsHDAs+".txt"
            #sourceName=HDA.name()
            hou_parent = HDA.parent()
            target = self.setupNewthing(HDA,hou_parent,0)
            children = self.getHDAsInNode(target)
            while(children):
                tmpChildren=[]
                for child in children:
                    target = self.setupNewthing(child,target,1)
                    tmpChildren += self.getHDAsInNode(target)
                    targetsToKeep.append(target)
                children=tmpChildren
            if(self.Mode==0 or self.Mode==1):
                targetTxt = self.folderExportTxt+"/"+sourceName+".txt"
                self.writeNodeToTxt(hou_parent,targetTxt)
            counter+=1
        #self.cleanup([hou_parent])
        if(self.Mode==2):
            sourceName = hou.hipFile.name().split("/")
            sourceName = sourceName[len(sourceName)-1].split(".hip")[0]
            hou.hipFile.save(file_name=hou.hipFile.name().replace(".hip","_convertedHDAs.hip"))
            targetTxt = self.folderExportTxt+"/"+sourceName+".txt"
            self.writeNodeToTxt(hou.node("/"),targetTxt)
    ##################################
    def getNewNodes(self):
        List1= list(hou.node("/obj").allSubChildren())
        List2=list(self.allNodes)
        allNewNodes=[]
        for item in List1:
            if item not in List2:
                if(self.subSuffix in item.name()):
                    allNewNodes.append(item)
        return allNewNodes
    ##################################
    def SetToDefaults(self,allNewNodes):
        for node in allNewNodes:
            parms = node.parms()
            for parm in parms:
                try:
                    parm.revertToDefaults()
                
                    parm.deleteAllKeyframes()
                    parm.revertToDefaults()
                
                    parm.revertToRampDefaults()
                except:
                    pass
    ##################################
    def ConvertTXTHDA(self,allNewNodes):
        lenghts=[]
        counter=0
        for node in allNewNodes:
            pathPArent= len(node.path().split("/"))
            lenghts.append(pathPArent)
            allNewNodes[counter]=node.path()
            counter+=1
        lenghts, allNewNodes = zip(*sorted(zip(lenghts, allNewNodes)))    
        allNewNodes=list(allNewNodes)
        allNewNodes.reverse()
        counter=0
        for path in allNewNodes:
            allNewNodes[counter]=hou.node(path)
            counter+=1
            
        for item in allNewNodes:
            name = item.name().replace(self.subSuffix,"")
            item.setName(name)
            libraryFilePath = item.parm("libraryFilePath").eval()
            minNumInputs = item.parm("minNumInputs").eval()
            maxNumInputs = item.parm("maxNumInputs").eval()
            comment = item.parm("comment").eval()
            version = item.parm("version").eval()
            isCreateBackupsEnabled = item.parm("isCreateBackupsEnabled").eval()
            da = item.createDigitalAsset(name=name,hda_file_name=self.folderWithHDAs+"/"+name+self.hdaFileExt,version=version,comment=comment,max_num_inputs=maxNumInputs,min_num_inputs=minNumInputs)
            if(maxNumInputs>4):
                for x in range(0,maxNumInputs):
                    node=hou.node(da.path()+"/"+"tmpConnectTo_"+str(x))
                    node.setInput(0, da.indirectInputs()[x])
                    node.destroy()
            inputsForHDAConvert = da.parm("inputsForHDAConvert").eval()
            inputsForHDAConvert = inputsForHDAConvert.split(" ")
            if(len(inputsForHDAConvert)==int(maxNumInputs)):
                for x in range(int(maxNumInputs)):
                    if(inputsForHDAConvert[x]!="/" and inputsForHDAConvert[x]!=" " and inputsForHDAConvert[x]!=""):
                        da.setInput(x,hou.node(inputsForHDAConvert[x]))
            parmTemplateGroup = da.parmTemplateGroup()
            entriesTmp = parmTemplateGroup.entries()
            for entry in entriesTmp:
                if("minNumInputs" in entry.name() or "maxNumInputs" in entry.name() or "comment" in entry.name() or "version" in entry.name() or "isCreateBackupsEnabled" in entry.name()) or "nInputsSourceForHDAConvert" in entry.name() or "inputsForHDAConvert" in entry.name() or "libraryFilePath" in entry.name():
                    parmTemplateGroup.remove(entry)
            da.setParmTemplateGroup(parmTemplateGroup)
            da.type().definition().updateFromNode(da)
            da.matchCurrentDefinition()
            
            
            

    ##################################
    def checkLicense(self):
        return hou.licenseCategory()
    ##################################
    def importTXT(self,fileToDo):
        in_file = open(fileToDo)
        test  = in_file.read()
        test = test.split("\n\n")
        for x in test:
            exec(x)
    ##################################
    def addChildren(self,node):
        children = node.allSubChildren()            
        tmpChildrenToAdd=[]
        HDAsToCopyToNewToAdd=[]
        for child in children:
            OK=1
            defi = child.type().definition()
            if defi is not None :
                for element in self.ExcludeElements:
                    if element in str(defi):
                        OK=0
            else:
                OK=0
            if(OK==1):
                tmpChildrenToAdd.append(child)
                HDAsToCopyToNewToAdd.append(0)
        return tmpChildrenToAdd,HDAsToCopyToNewToAdd

    ##################################
    def setupNewthing(self,HDA,hou_parent,mode):
        libraryFilePath = HDA.type().definition().libraryFilePath()
        minNumInputs = HDA.type().definition().minNumInputs()
        maxNumInputs = HDA.type().definition().maxNumInputs()
        comment = HDA.type().definition().comment()
        version = HDA.type().definition().version()
        isCreateBackupsEnabled = HDA.type().definition().isCreateBackupsEnabled()

        sourceName=HDA.name()  
        hou_parm_template=""
        wasBypassed = self.forceCook(HDA)
        if mode==0 and self.ExportToTxtInsteadOfSpawningInScene==1:         
            hou_parent.setName(sourceName+"_sub")
            source = hou.copyNodesTo([HDA],hou_parent)[0]
        else:
            source = HDA

        nInputsSource=len(HDA.inputs())
        inputs=""
        print("HDA.inputs()")
        print(HDA.inputs())
        for input in HDA.inputs():
            try:
                inputs+=input.path()+" "
            except:
                inputs+="/ "
        print("inputs")
        print(inputs)
        wasBypassed = self.forceCook(source)
        parms = source.parms()
        group = source.parmTemplateGroup()
        path = source.parent().path()
        inputConnections = source.inputConnections() 
        outputConnections = source.outputConnections()
        target = self.setupTarget(group,source,wasBypassed,path,sourceName)
        self.runThroughParms(parms,source,target)
        childrenSource = self.connections(inputConnections,outputConnections,source,target,mode)
        self.setupParms(target)
        target.setName(sourceName+self.subSuffix)
        if(self.KeepHDA==0 or mode==1):
            self.cleanup([source])
        wasBypassed = self.forceCook(target)

        #subnetwork can only have 4 inputs        
        #if(nInputsSource>4):
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
            if(self.UseDefaultValues==1):
                self.SetToDefaults([target])
        except:
            pass
    
        return target
    ##################################
    def getHDAsInNode(self,HDA):
        children = HDA.children()
        childrenHDA=[]
        for child in children:
            OK=1
            defi = child.type().definition()
            if defi is not None :
                for element in self.ExcludeElements:
                    if element in str(defi):
                        OK=0
            else:
                OK=0
            if(OK==1):
                childrenHDA.append(child)
        return childrenHDA

    ##################################
    def forceCook(self,source):
        wasBypassed=0
        if(source.isBypassed()==True):
            wasBypassed=1
            try:
                source.bypass(0)
                #source.cook(force=True)
            except:
                pass
        try:
            source.bypass(wasBypassed)        
        except:
            pass
        try:
            source.cook(force=True)
        except:
            pass
        return wasBypassed
    ##################################
    def setupTarget(self,group,source,wasBypassed,path,sourceName):
        target = hou.node(path+"/"+sourceName+self.subSuffix)
        if target:
            target.destroy()
        color = source.color()
        position = source.position()
        position[0]+=self.offset
        target=hou.node(path).createNode("subnet")
        target.setParmTemplateGroup(group)
        target.setColor(color)
        target.setPosition(position)
        target.bypass(wasBypassed) 
        #target.setName()
        return target
    ##################################
    def runThroughParms(self,parms,source,target):
        for parm in parms:
            hou_parm_template=""
            code=parm.parmTemplate().asCode()
            exec(code)
            value = parm.eval()
            name = parm.name()
            target_parm = target.parm(name)
            if target_parm is not None:
                target_parm.set(value)
            code=parm.asCode()
            #code=code.replace("    hou_node","#    pass#hou_node")
            code=code.replace("    hou_node","    pass#hou_node")
            code=code.replace("hou_node.","target.")
            try:
                exec(code)
            except (AttributeError, TypeError) as e:
                # Parameter might not exist on target, skip this code execution
                pass
            parmToDo=""
    
            code=code.split("\n")
            for c in code:
                if "hou_parm = " in c:
                    line = c.replace("target.","source.")
                    try:
                        exec("global hou_parm;"+line)
                        global hou_parm
                        if hou_parm is not None:
                            value = hou_parm.eval()
                            try:
                                exec(c)
                            except (AttributeError, TypeError):
                                # Target parameter might not exist, skip
                                pass
                    except (AttributeError, TypeError, NameError):
                        pass
                elif "hou_parm.set" in c:
                    line1="hou_parm.set(\""+str(value)+"\")"
                    line2="hou_parm.set("+str(value)+")"
                    line3="hou_parm.set(r\""+str(value)+"\")"
                    try:
                        exec(line1)
                    except:
                        try:
                            exec(line2)
                        except:
                            try:
                                exec(line3)
                            except:
                                pass
    ##################################
    def connections(self,inputConnections,outputConnections,source,target,mode):
        print("###############")
        print("###############")
        print("###############")
        if(self.ExportToTxtInsteadOfSpawningInScene==0 or mode==1):
            self.setupConnections(inputConnections,source,target)
        childrenSource = source.children()
        hou.copyNodesTo(childrenSource,target)
        if(self.ExportToTxtInsteadOfSpawningInScene==0 or mode==1):
            self.setupConnections(outputConnections,source,target)
        counter=0
        childrenInTarget= source.children()
        sourceIndirects= source.indirectInputs()
        targetIndirects= target.indirectInputs()
        inputsDone = []
        nullsForInputs = []
        #if("testHDA" in source.name()):
        maxNumInputs = source.type().definition().maxNumInputs()
        #make sure sth is connected
        tmpNull = source.parent().createNode("null")
        for x in range(maxNumInputs):
            inputNode = source.input(x)
            if not inputNode:
                inputNode = tmpNull
                source.setInput(x,tmpNull,output_index=0)
        for child in childrenInTarget:
            inputConnections = child.inputConnections() 
            for input in inputConnections:
                if(input.subnetIndirectInput()):
                        targetChild=hou.node(child.path().replace(source.path(),target.path()))
                        if (input.subnetIndirectInput().number() not in inputsDone):
                            null = target.createNode("null")
                            null.setName("tmpConnectTo_"+str(input.subnetIndirectInput().number()+0))
                            if(input.subnetIndirectInput().number()<4):
                                null.setInput(0, targetIndirects[input.subnetIndirectInput().number()])
                            nullsForInputs.append(null)
                            inputsDone.append(input.subnetIndirectInput().number())
                        else:
                            null = nullsForInputs[inputsDone.index(input.subnetIndirectInput().number())]
                        targetChild.setInput(input.inputIndex(),null)
                        counter+=1
        tmpNull.destroy()
        return childrenSource

        
    """
    ##################################
    def updateOrgPath(self,HDAs,childrenSource,source,target):
        for x in range(len(HDAs)):
            if HDAs[x] in childrenSource:
                orgPath = HDAs[x].path()
                orgPath=orgPath.replace(source.path(),target.path())
                HDAs[x] = hou.node(orgPath)
                try:
                    HDAs[x].cook(force=True)
                except:
                    pass
        return HDAs
    """
    ##################################
    def cleanup(self,targets):
        for target in targets:
            #print("deleting "+target.path())
            target.destroy()    
        for node in self.originalSelection:
            try:
                node.setSelected( True,clear_all_selected=False)
            except:
                pass
    ##################################
    def setupParms(self,target):
        parmTemplateGroup =target.parmTemplateGroup()
        #entriesWithoutFolders = parmTemplateGroup.entriesWithoutFolders())
        Standard=parmTemplateGroup.findFolder("Standard")
        if(Standard):
            StandardParmTemplats = Standard.parmTemplates()
        Spare=parmTemplateGroup.findFolder("Spare")
        if(Spare):
            SpareParmTemplats = Spare.parmTemplates() 
            group = hou.ParmTemplateGroup(StandardParmTemplats+SpareParmTemplats)
            target.setParmTemplateGroup(group)
                        
        if("/obj" in target.path()):
            target.parm("label1").hide("on")
            target.parm("label2").hide("on")
            target.parm("label3").hide("on")
            target.parm("label4").hide("on")
        else:
            pass
    ##################################    
    def setupConnections(self,connections,source,target):
        for connection in connections:
            inputNode = connection.inputNode()
            outputNode = connection.outputNode()
            inputIndex = connection.inputIndex()
            outputIndex = connection.outputIndex()
            if (inputNode==source):
                inputNode=target
            if (outputNode==source):
                outputNode=target
            try:
                outputNode.setInput(inputIndex,inputNode,outputIndex)
            except:
                pass
    ##################################
    def writeNodeToTxt(self,node,txtFile):
        codeString =node.asCode(brief=True, recurse=True, save_creation_commands=True, save_spare_parms=True,save_keys_in_frames=True)
        text_file = open(txtFile, "w")
        text_file.write("")
        text_file.close()
        text_file = open(txtFile, "a")
        text_file.write(codeString)
        text_file.close()
        print("###########")
        print("printed to ")
        print(txtFile)
        print("###########")
    ##################################
    def getHDAs(self):
        HDAsTmp=[]
        hdasToInstall = []
        allNodes=[]
        allNodes= hou.selectedNodes()
        if(self.Mode==1 or self.Mode==2 or self.Mode==5):
            allNodes = hou.node("/").allSubChildren()
        elif(self.Mode==7):
            filesInFolder = glob.glob(self.folderWithHDAs+"/*.*")
            for file in filesInFolder:
                if ".hda" in file or ".hdalc" in file or ".hdanc" in file:
                    hdasToInstall.append(file)
            for hda in hdasToInstall:
                hou.hda.installFile(hda,oplibraries_file=None, change_oplibraries_file=True, force_use_assets=False)
                basename = os.path.basename(hda)
                root, ext = os.path.splitext(basename)
                hdaNode = hou.node(hou.pwd().parent().path()).createNode(root)
                try:
                    hdaNode.cook(force=True)
                except:
                    pass
                allNodes.append(hdaNode)
    
        if(self.Mode==0 or self.Mode==1):
            HDAsToDo=[]
        for node in allNodes:
            OK=1
            defi = node.type().definition()
            if defi is not None :
                if(self.Mode==0 or self.Mode==1):
                    path=defi.libraryFilePath()
                    if path in HDAsToDo:
                        OK=0
                        print("found multiple instances of "+path)
                        print("only converting 1")
                    else:
                        HDAsToDo.append(path)
                for element in self.ExcludeElements:
                    if element in str(defi):
                        OK=0
                        break
            else:
                OK=0
            if node==self.toNotIncludeHDA:
                OK=0
            if(OK==1):#don't add if part of hda, these get converted anyway
                parentPath = node.parent().path().split("/")
                previousPath=""
                for path in parentPath:
                    previousPath+="/"+path
                    previousPath=previousPath.replace("//","/")
                    newnode = hou.node(previousPath)
                    if "None" not in str(newnode):
                        defi = newnode.type().definition()
                        if defi is not None :
                            OK=0
                            break
            if(OK==1):    
                HDAsTmp.append(node)
        
        
        
        
        
        allNodes=HDAsTmp
        #if self.Mode==1 or self.Mode==3:
        #    allNodes=HDAsTmp
        return allNodes
