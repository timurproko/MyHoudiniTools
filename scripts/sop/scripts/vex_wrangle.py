import hou
import re
import time
import hou_module_loader
import mytools


_vex_consts = hou_module_loader.load_from_hou_path(
    "scripts/sop/constants/vex_wrangle.py",
    "_mytools_vex_wrangle_constants",
)

_SHOW_PARMS_COLOR = _vex_consts.SHOW_PARMS_COLOR
_SHOW_PARMS_PREV_COLOR_USERDATA_KEY = _vex_consts.SHOW_PARMS_PREV_COLOR_USERDATA_KEY


def toggle_node_color_from_current(
    node,
    highlight_color=_SHOW_PARMS_COLOR,
    userdata_key=_SHOW_PARMS_PREV_COLOR_USERDATA_KEY,
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
# Snippet from Markus Jarderot via StackOverflow
# This will miss some edge cases but generally
# avoid picking up commented out ch references.
def createSpareParmsFromChCalls(node, parmname):
    """ For each ch() call in the given parm name create
        a corresponding spare parameter on the node.
    """
    issimple = True
    parm = node.parm(parmname)
    if len(parm.keyframes()) > 0:
        # we have a keyframe, so expression.
        # we will want to follow it.
        issimple = False
        code = parm.evalAsString()
    else:
        # No keyframes.  Attempt an unexpanded update to avoid
        # triggering excessive replacement.
        code = node.parm(parmname).unexpandedString()
        # Check if the code is itself a backtick chref, as often
        # created by paste references. We want to follow these.
        stripcode = code.strip()
        if len(stripcode) >= 2:
            # is this entirely a backtick expression?
            if stripcode[0] == "`" and stripcode[-1] == "`":
                issimple = False
                code = parm.evalAsString()

    # Strip out comments.  We only want
    # active ch() calls.
    code = mytools.remove_c_like_comments(code)

    # Now find all ch() patterns.
    chcalls = [
        "ch",
        "chf",
        "chi",
        "chu",
        "chv",
        "chp",
        "ch2",
        "ch3",
        "ch4",
        r"vector\(chramp",
        "chramp",
        r"vector\(chrampderiv",
        "chrampderiv",
        "chs",
        "chdict",
        "chsop",
    ]

    ch_to_size = {
        "ch": 1,
        "chf": 1,
        "chi": 1,
        "chu": 2,
        "chv": 3,
        "chp": 4,
        "ch2": 4,
        "ch3": 9,
        "ch4": 16,
        r"vector\(chramp": 1,
        "chramp": 1,
        r"vector\(chrampderiv": 1,
        "chrampderiv": 1,
        "chs": 1,
        "chsop": 1,
        "chdict": 1,
    }

    chmatches = []
    for chcall in chcalls:
        # We wish to match ch("foo"); ch("foo", 3.2); ch('foo')
        # We do not want to match ch("../foo"); ch("foo" + "bar");
        matches = re.findall(r"\b" + chcall + r" *\( *\"(\w+)\" *[\),]", code)
        matches += re.findall(r"\b" + chcall + r" *\( *'(\w+)' *[\),]", code)
        chmatches.append(matches)

        # Check if we have this parameter already.
        for match in matches:
            if (node.parm(match) is None) and (node.parmTuple(match) is None):
                # No match, add the parameter.
                template = None
                tuplesize = ch_to_size[chcall]
                label = match.title().replace("_", " ")
                if chcall == r"vector\(chramp" or chcall == r"vector\(chrampderiv":
                    template = hou.RampParmTemplate(match, label, hou.rampParmType.Color)
                elif chcall == "chramp" or chcall == "chrampderiv":
                    # No explicit cast, guess float.
                    template = hou.RampParmTemplate(match, label, hou.rampParmType.Float)
                elif chcall == "chs":
                    template = hou.StringParmTemplate(match, label, tuplesize)
                elif chcall == "chsop":
                    template = hou.StringParmTemplate(
                        match,
                        label,
                        tuplesize,
                        string_type=hou.stringParmType.NodeReference,
                    )
                elif chcall == "chi":
                    template = hou.IntParmTemplate(match, label, tuplesize)
                elif chcall == "chdict":
                    template = hou.DataParmTemplate(
                        match,
                        label,
                        tuplesize,
                        data_parm_type=hou.dataParmType.KeyValueDictionary,
                    )
                else:
                    # Range is less meaningfull for tuples, so set it nicely for scalars.
                    template = hou.FloatParmTemplate(match, label, tuplesize, min=0, max=1)
                node.addSpareParmTuple(template)

    # If we are not simple we can't write back as it will chase the
    # parameter and do something unexpected.  So we just cowardly don't
    # update.
    if issimple:
        code = node.parm(parmname).unexpandedString()
        node.parm(parmname).set(code)


# ===================== HOUDINI SOURCE CODE  =====================