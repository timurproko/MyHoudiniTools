import subprocess, tempfile, os, hou, platform

def sendToRizom(rizomPath, exportFile, nodes=None):
    if not nodes:
        nodes = hou.selectedNodes()
    elif nodes:
        if not os.path.exists(rizomPath):
            hou.ui.displayMessage('You need to specify the correct rizom path.\n' + rizomPath + ' does not exist.\nYou have to set the correct path in the package .json', title='RizomUV Bridge')
            return
        nodes[0].geometry().saveToFile(exportFile)
        houdiniGroupsToClipboardRizom(nodes[0].geometry())
        cmd = '"' + rizomPath + '" "' + exportFile + '"'
        if platform.system() == 'Windows':
            subprocess.Popen(cmd)
        else:
            if platform.system() == 'Darwin':
                subprocess.Popen(['open', '-a', rizomPath, '--args', exportFile])
            else:
                cmd = '"' + rizomPath + '" "' + exportFile + '"'
                subprocess.Popen([rizomPath, exportFile])



def sendToRizomClearUvs(rizomPath, exportFile, nodes=None):
    if not nodes:
        nodes = hou.selectedNodes()
    elif nodes:
        if not os.path.exists(rizomPath):
            hou.ui.displayMessage('You need to specify the correct rizom path.\n' + rizomPath + ' does not exist.\nYou have to set the correct path in the package .json', title='RizomUV Bridge')
            return
        nodes[0].geometry().saveToFile(exportFile)
        houdiniGroupsToClipboardRizom(nodes[0].geometry())
        cmd = '"' + rizomPath + '" /nu "' + exportFile + '"'
        if platform.system() == 'Windows':
            subprocess.Popen(cmd)
        else:
            if platform.system() == 'Darwin':
                subprocess.Popen(['open', '-a', rizomPath, '--args', exportFile])
            else:
                cmd = '"' + rizomPath + '" -nu "' + exportFile + '"'
                subprocess.Popen([rizomPath, '-nu', exportFile])



def automaticRoundtrip(rizomPath, exportFile, nodes=None):
    luascript = 'ZomLoad({File={Path="odfilepath", ImportGroups=true, XYZ=true}, NormalizeUVW=true})\n--U3dSymmetrySet({Point={0, 0, 0}, Normal={1, 0, 0}, Threshold=0.01, Enabled=true, UPos=0.5, LocalMode=false})\nZomSelect({PrimType="Edge", Select=true, ResetBefore=true, ProtectMapName="Protect", FilterIslandVisible=true, Auto={Skeleton={}, Open=true, PipesCutter=true, HandleCutter=true}})\nZomCut({PrimType="Edge"})\nZomUnfold({PrimType="Edge", MinAngle=1e-005, Mix=1, Iterations=1, PreIterations=5, StopIfOutOFDomain=false, RoomSpace=0, PinMapName="Pin", ProcessNonFlats=true, ProcessSelection=true, ProcessAllIfNoneSelected=true, ProcessJustCut=true, BorderIntersections=true, TriangleFlips=true})\nZomIslandGroups({Mode="DistributeInTilesEvenly", MergingPolicy=8322, GroupPath="RootGroup"})\nZomPack({ProcessTileSelection=false, RecursionDepth=1, RootGroup="RootGroup", Scaling={Mode=2}, Rotate={}, Translate=true, LayoutScalingMode=2})\nZomSave({File={Path="odfilepath", UVWProps=true}, __UpdateUIObjFileName=true})\nZomQuit()\n'
    if not nodes:
        nodes = hou.selectedNodes()
    if nodes:
        if not os.path.exists(rizomPath):
            hou.ui.displayMessage('You need to specify the correct rizom path.\n' + rizomPath + ' does not exist.\nYou have to set the correct path in the package .json', title='RizomUV Bridge')
            return
        for node in nodes:
            node.geometry().saveToFile(exportFile)
            f = open(tempfile.gettempdir() + os.sep + 'rizom.lua', 'w')
            f.write(luascript.replace('odfilepath', exportFile.replace('\\', '/')))
            f.close()
            cmd = '"' + rizomPath + '" -cfi "' + tempfile.gettempdir() + os.sep + 'rizom.lua' + '"'
            if platform.system() == 'Windows':
                subprocess.call(cmd, shell=False)
            else:
                if platform.system() == 'Darwin':
                    os.system('open -W "' + rizomPath + '" --args -cfi "' + tempfile.gettempdir() + os.sep + 'rizom.lua"')
                else:
                    subprocess.call([rizomPath, '-cfi', tempfile.gettempdir() + os.sep + 'rizom.lua'])
            getFromRizom([node], rizomPath, exportFile)



def getFromRizom(nodes, rizomPath, exportFile):
    node = None
    if not nodes:
        nodes = hou.selectedNodes()
        if not nodes:
            return
    node = nodes[0]
    if node:
        if not os.path.exists(rizomPath):
            hou.ui.displayMessage('You need to specify the correct rizom path.\n' + rizomPath + ' does not exist.\nYou have to set the correct path in the package .json', title='RizomUV Bridge')
            return
        parent = node.parent()
        n = parent.createNode('attribcopy', 'TransferUVs', run_init_scripts=False, load_contents=True, exact_type_name=True)
        n.setParms({'attribname': 'uv'})
        n.setInput(0, node)
        m = parent.createNode('file')
        m.setParms({'filemode':2,  'file':exportFile})
        m.setHardLocked(1)
        n.setInput(1, m)
        n.setDisplayFlag(True)
        n.moveToGoodPosition()
        m.moveToGoodPosition()



def getPointSelection(points):
    zomSelect = ''
    for point in points:
        zomSelect += str(point.number()) + ', '

    if zomSelect != '':
        return 'ZomSelect({PrimType="Vertex", WorkingSet="Visible", ResetBefore=true, Select=true, IDs={ ' + zomSelect[:-2] + '}, List=true})'
    return ''



def getPrimSelection(polygons):
    zomSelect = ''
    for prim in polygons:
        zomSelect += str(prim.number()) + ', '

    if zomSelect != '':
        return 'ZomSelect({PrimType="Polygon", WorkingSet="Visible", ResetBefore=true, Select=true, IDs={ ' + zomSelect[:-2] + '}, List=true})'
    return ''



def getEdgeSelection(edges):
    zomSelect = ''
    for edge in edges:
        prims = edge.prims()
        pointIDs = []
        points = edge.points()
        for point in points:
            pointIDs.append(point.number())

        for prim in prims:
            primPTS = []
            for pt in prim.points()[::-1]:
                primPTS.append(pt.number())

            location = 0
            idx1 = primPTS.index(pointIDs[0])
            idx2 = primPTS.index(pointIDs[1])
            if idx2 == idx1 + 1:
                location = idx2
            else:
                if idx2 == idx1 - 1:
                    location = idx1
                else:
                    location = 0
            zomSelect += str(prim.number()) + ', ' + str(location) + ', '

    if zomSelect != '':
        return 'ZomSelect({PrimType="Edge", WorkingSet="Visible", ResetBefore=true, Select=true, IDs={ ' + zomSelect[:-2] + '}, List=true,  EdgesAsPolyEdgeIDs=true})'
    return ''



def houdiniGroupsToClipboardRizom(geo):
    points = ()
    prims = ()
    edges = ()
    for grp in geo.pointGroups():
        points += geo.globPoints(grp.name())

    for grp in geo.primGroups():
        prims = geo.globPrims(grp.name())

    for grp in geo.edgeGroups():
        edges = geo.globEdges(grp.name())

    selString = ''
    if points:
        selString += getPointSelection(points) + '\n'
    if prims:
        selString += getPrimSelection(prims) + '\n'
    if edges:
        selString += getEdgeSelection(edges) + '\n'
    if selString != '':
        hou.ui.copyTextToClipboard(selString)
        with open(tempfile.gettempdir() + os.sep + "rizom_s0.lua", "w") as f:
            f.write(selString)



def automaticRoundtrip(rizomPath, exportFile, nodes=None):
    luascript = 'ZomLoad({File={Path="odfilepath", ImportGroups=true, XYZ=true}, NormalizeUVW=true})\n--U3dSymmetrySet({Point={0, 0, 0}, Normal={1, 0, 0}, Threshold=0.01, Enabled=true, UPos=0.5, LocalMode=false})\nZomSelect({PrimType="Edge", Select=true, ResetBefore=true, ProtectMapName="Protect", FilterIslandVisible=true, Auto={Skeleton={}, Open=true, PipesCutter=true, HandleCutter=true}})\nZomCut({PrimType="Edge"})\nZomUnfold({PrimType="Edge", MinAngle=1e-005, Mix=1, Iterations=1, PreIterations=5, StopIfOutOFDomain=false, RoomSpace=0, PinMapName="Pin", ProcessNonFlats=true, ProcessSelection=true, ProcessAllIfNoneSelected=true, ProcessJustCut=true, BorderIntersections=true, TriangleFlips=true})\nZomIslandGroups({Mode="DistributeInTilesEvenly", MergingPolicy=8322, GroupPath="RootGroup"})\nZomPack({ProcessTileSelection=false, RecursionDepth=1, RootGroup="RootGroup", Scaling={Mode=2}, Rotate={}, Translate=true, LayoutScalingMode=2})\nZomSave({File={Path="odfilepath", UVWProps=true}, __UpdateUIObjFileName=true})\nZomQuit()\n'
    if not nodes:
        nodes = hou.selectedNodes()
    if nodes:
        if not os.path.exists(rizomPath):
            hou.ui.displayMessage('You need to specify the correct rizom path.\n' + rizomPath + ' does not exist.\nYou have to set the correct path in the package .json', title='RizomUV Bridge')
            return
        for node in nodes:
            node.geometry().saveToFile(exportFile)
            f = open(tempfile.gettempdir() + os.sep + 'rizom.lua', 'w')
            f.write(luascript.replace('odfilepath', exportFile.replace('\\', '/')))
            f.close()
            cmd = '"' + rizomPath + '" -cfi "' + tempfile.gettempdir() + os.sep + 'rizom.lua' + '"'
            if platform.system() == 'Windows':
                subprocess.call(cmd, shell=False)
            else:
                if platform.system() == 'Darwin':
                    os.system('open -W "' + rizomPath + '" --args -cfi "' + tempfile.gettempdir() + os.sep + 'rizom.lua"')
                else:
                    subprocess.call([rizomPath, '-cfi', tempfile.gettempdir() + os.sep + 'rizom.lua'])
            getFromRizom([node], rizomPath, exportFile)


def passGroups(rizomPath, node=None):
    if not os.path.exists(rizomPath):
        hou.ui.displayMessage('You need to specify the correct rizom path.\n' + rizomPath + ' does not exist.\nYou have to set the correct path in the package .json', title='RizomUV Bridge')
        return
    nodetype = node.type().name()
    if nodetype == "groupcreate":
        houdiniGroupsToClipboardRizom(node.geometry())
        # hou.ui.setStatusMessage("Group selection sent to Slot 0 in RizomUV.", severity=hou.severityType.Message)
        hou.ui.setStatusMessage("Group selection saved into: " + tempfile.gettempdir() + os.sep + "rizom_s0.lua", severity=hou.severityType.Message)

    else:
        hou.ui.setStatusMessage("Selected node is not a Group, please select a Group instead.", severity=hou.severityType.Warning)