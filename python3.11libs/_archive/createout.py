import hou, re



def cursorPosition(network):
    position = network.cursorPosition()
    return position



def getNetworkEditor():
    editors = None
    pane = hou.ui.paneTabUnderCursor()
    if not pane:
        if not pane:
            for p in hou.ui.paneTabs():
                if p.type() == hou.paneTabType.NetworkEditor:
                    pane = p
                    break

            if not pane:
                return (-1, -1, -1)
    if pane.type().name() == 'NetworkEditor':
        editors = [
        pane]
    if not editors:
        editors = [pane for pane in hou.ui.paneTabs() if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab()]
    if not editors:
        return (-1, -1, -1)
    else:
        editors = editors[-1]
        ctx = editors.pwd()
        type_ctx = ctx.type().childTypeCategory()
        return (
        editors, ctx, type_ctx)



def setNodeAsSelected(node=None):
    if not node:
        return
    node.setSelected(True)
    editors = [pane for pane in hou.ui.paneTabs() if isinstance(pane, hou.NetworkEditor) and pane.isCurrentTab()]
    if not editors:
        return
    for pane in editors:
        if pane.linkGroup() == hou.paneLinkType.FollowSelection:
            if pane.currentNode() != node and not pane.isPin():
                pane.setCurrentNode(node)
            return

    editors[0].setCurrentNode(node)



def createOut(nodes=None, name=None):
    with hou.undos.group('createOutSops'):
        if not nodes:
            nodes = hou.selectedNodes()

        if not nodes:
            que = hou.ui.readInput('Provide Null Name:', initial_contents='null', buttons=(
                'OUT',
                'IN',
                'Cancel'), close_choice=2, title='Create Null')
            if que[0] == 2:
                return
            name = re.sub('[^0-9a-zA-Z\\\\.]', '_', que[1])
            outprefix = 'OUT_'
            inprefix = 'IN_'
            if name == '':
                outprefix = 'OUT'
                inprefix = 'IN'
            if que[0] == 1:
                outprefix = 'IN_'
            else:
                outprefix = 'OUT_'
            network, ctx, type_ctx = getNetworkEditor()
            if network:
                dropPosition = cursorPosition(network)
                n = ctx.createNode('null', outprefix + re.sub('[^0-9a-zA-Z\\\\.]', '_', name), run_init_scripts=False, load_contents=True, exact_type_name=True)
                n.setUserData('nodeshape', 'circle')
                if dropPosition:
                    n.setPosition(dropPosition)
            return



        #Disabled Context
        if nodes[0].type().category().name() in ['Vop']: 
            return



        # Non SOP Context
        if nodes[0].type().category().name() not in ['Sop']: 
            que = None

            if len(nodes) > 0 and not name:
                que = hou.ui.readInput('Provide Null Name:', buttons=(
                    'OUT',
                    'IN',
                    'Cancel'), close_choice=2, title='Create Null')
                if que[0] == 2:
                    return
                name = re.sub('[^0-9a-zA-Z\\\\.]', '_', que[1])
                
            else:
                que = [0, name]

            for node in nodes:
                if len(node.outputLabels()) == 1:
                    if que:
                        if que[1] == '':
                            name = re.sub('[^0-9a-zA-Z\\\\.]', '_', node.name())
                        else:
                            name = que[1]
                    outprefix = 'OUT_'
                    inprefix = 'IN_'
                    if name == '':
                        outprefix = 'OUT'
                        inprefix = 'IN'
                    if que:
                        if que[0] == 1:
                            outprefix = 'IN_'

                    if que[0] == 0:
                        n = node.parent().createNode('null', 'null', run_init_scripts=False, load_contents=True, exact_type_name=True)
                        n.setName(outprefix + re.sub('[^0-9a-zA-Z\\\\.]', '_', name), unique_name=True)
                        n.setUserData('nodeshape', 'circle')
                        n.setInput(0, node, 0)
                        # Connect to all children
                        for child in node.outputs():
                            if child != n and child != node:
                                child.setInput(0, None)
                                child.setNextInput(n, 0)
                        n.moveToGoodPosition()
                        pos = n.position()
                        setNodeAsSelected(n)

                    if que[0] == 1:
                        nodeInputs = node.inputs()
                        n = node.createInputNode(0, 'null', 'null', run_init_scripts=False, load_contents=True, exact_type_name=True)
                        n.setName(outprefix + re.sub('[^0-9a-zA-Z\\\\.]', '_', name), unique_name=True)
                        n.setUserData('nodeshape', 'circle')
                        # Connect to all parent
                        for parent in nodeInputs:
                            if parent != n and parent != node:
                                n.setInput(0, parent, 0)
                        pos = n.position()
                        setNodeAsSelected(n)

                else:
                    o = 0
                    for output in node.outputLabels():
                        if output == '':
                            label = '_Output_' + str(o)
                        else:
                            label = '_' + re.sub('[^0-9a-zA-Z\\\\.]', '_', output)
                        if que:
                            if que[1] == '':
                                name = re.sub('[^0-9a-zA-Z\\\\.]', '_', node.name())
                            else:
                                name = que[1]
                        outprefix = 'OUT_'
                        inprefix = 'IN_'
                        if name == '':
                            outprefix = 'OUT'
                            inprefix = 'IN'
                        if que:
                            if que[0] == 1:
                                outprefix = 'IN_'
                        n = node.parent().createNode('null', outprefix + re.sub('[^0-9a-zA-Z\\\\.]', '_', name) + label, run_init_scripts=False, load_contents=True, exact_type_name=True)
                        n.setUserData('nodeshape', 'circle')
                        n.setInput(0, node, o)
                        n.moveToGoodPosition()
                        pos = n.position()
                        o += 1
                        setNodeAsSelected(n)



        # SOP Context
        else:
            merges = hou.ui.displayMessage('Create Object Merge?', buttons=(
                'Yes',
                'No',
                'Cancel'), close_choice=2, title='Create Null')
            if merges == 2:
                return
            que = None

            if len(nodes) > 0 and not name and merges == 0:
                que = hou.ui.readInput('Provide Null Name:', buttons=(
                    'OUT',
                    'Cancel'), close_choice=1, title='Create Null')
                if que[0] == 1:
                    return
                name = re.sub('[^0-9a-zA-Z\\\\.]', '_', que[1])

            elif len(nodes) > 0 and not name and merges == 1:
                que = hou.ui.readInput('Provide Null Name:', buttons=(
                    'OUT',
                    'IN',
                    'Cancel'), close_choice=2, title='Create Null')
                if que[0] == 2:
                    return
                name = re.sub('[^0-9a-zA-Z\\\\.]', '_', que[1])
                
            else:
                que = [0, name]

            for node in nodes:
                if len(node.outputLabels()) == 1:
                    if que:
                        if que[1] == '':
                            name = re.sub('[^0-9a-zA-Z\\\\.]', '_', node.name())
                        else:
                            name = que[1]
                    outprefix = 'OUT_'
                    inprefix = 'IN_'
                    if name == '':
                        outprefix = 'OUT'
                        inprefix = 'IN'
                    if que:
                        if que[0] == 1:
                            outprefix = 'IN_'

                    if que[0] == 0:
                        n = node.parent().createNode('null', 'null', run_init_scripts=False, load_contents=True, exact_type_name=True)
                        n.setName(outprefix + re.sub('[^0-9a-zA-Z\\\\.]', '_', name), unique_name=True)
                        n.setUserData('nodeshape', 'circle')
                        n.setInput(0, node, 0)
                        # Connect to all children
                        for child in node.outputs():
                            if child != n and child != node:
                                child.setInput(0, None)
                                child.setNextInput(n, 0)
                        n.moveToGoodPosition()
                        pos = n.position()
                        setNodeAsSelected(n)

                    if que[0] == 1:
                        nodeInputs = node.inputs()
                        n = node.createInputNode(0, 'null', 'null', run_init_scripts=False, load_contents=True, exact_type_name=True)
                        n.setName(outprefix + re.sub('[^0-9a-zA-Z\\\\.]', '_', name), unique_name=True)
                        n.setUserData('nodeshape', 'circle')
                        # Connect to all parent
                        for parent in nodeInputs:
                            if parent != n and parent != node:
                                n.setInput(0, parent, 0)
                        pos = n.position()
                        setNodeAsSelected(n)

                    if merges == 0:
                        m = node.parent().createNode('object_merge', inprefix + re.sub('[^0-9a-zA-Z\\\\.]', '_', name))
                        relative_path = m.relativePathTo(n)
                        m.setParms({'objpath1': relative_path, 'xformtype': 'none'})
                        m.setPosition([pos[0], pos[1] - 1])
                        n.setColor(hou.Color([0, 0, 0]))
                        m.setColor(hou.Color([0, 0, 0]))

                else:
                    o = 0
                    for output in node.outputLabels():
                        if output == '':
                            label = '_Output_' + str(o)
                        else:
                            label = '_' + re.sub('[^0-9a-zA-Z\\\\.]', '_', output)
                        if que:
                            if que[1] == '':
                                name = re.sub('[^0-9a-zA-Z\\\\.]', '_', node.name())
                            else:
                                name = que[1]
                        outprefix = 'OUT_'
                        inprefix = 'IN_'
                        if name == '':
                            outprefix = 'OUT'
                            inprefix = 'IN'
                        if que:
                            if que[0] == 1:
                                outprefix = 'IN_'
                        n = node.parent().createNode('null', outprefix + re.sub('[^0-9a-zA-Z\\\\.]', '_', name) + label, run_init_scripts=False, load_contents=True, exact_type_name=True)
                        n.setUserData('nodeshape', 'circle')
                        n.setInput(0, node, o)
                        n.moveToGoodPosition()
                        pos = n.position()
                        o += 1
                        setNodeAsSelected(n)

                        if merges == 0:
                            m = node.parent().createNode('object_merge', inprefix + re.sub('[^0-9a-zA-Z\\\\.]', '_', name) + label)
                            relative_path = m.relativePathTo(n)
                            m.setParms({'objpath1': relative_path, 'xformtype': 'none'})
                            m.setPosition([pos[0], pos[1] - 1])
                            n.setColor(hou.Color([0, 0, 0]))
                            m.setColor(hou.Color([0, 0, 0]))