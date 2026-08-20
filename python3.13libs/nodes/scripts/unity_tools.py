import hou, re


def set_proj_path():
    proj_path = hou.getPreference('parmdialog.proj.path')
    hou.hscript("set -g UNITY = '" + str(proj_path) + "'")
    path = hou.parm("proj_path").eval()
    path = re.sub(r'/$', '', path)
    hou.parm("proj_path").set(path)
    hou.hscript("set -g UNITY = {}".format(path))
    hou.ui.setStatusMessage("Unity Project set as Houdini variable: $UNITY.", severity=hou.severityType.Message)
    check_and_set_proj_path()


def remove_proj_path():
    proj_path = hou.getPreference('parmdialog.proj.path')
    hou.hscript("set -g UNITY = '" + str(proj_path) + "'")
    path = ""
    hou.hscript("set -g UNITY = {}".format(path))
    hou.parm("proj_path").disable(0)
    hou.parm("proj_path_disabled").set(0)
    hou.hscript("set -u UNITY")
    hou.ui.setStatusMessage("Unity Project removed from Houdini variable.", severity=hou.severityType.Message)
    hou.parm("proj_path").set("")
    check_and_set_proj_path()


def invoke_dialogue():
    res = hou.ui.displayMessage("Do you want to delete Unity Project Path?", buttons=('Delete', 'Cancel'), close_choice=1)
    if res == 0:
        remove_proj_path()

 
def check_and_set_proj_path():
    unity_var = hou.getenv('UNITY')
    
    if unity_var:
        hou.parm("proj_path_set").set(1)
    else:
        hou.parm("proj_path_set").set(0)