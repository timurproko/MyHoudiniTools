import hdefereval, os, hou
import mytools, hotkeySystem_patch


# Global Variables
PRELOAD_DESKTOP_CACHE = False
HOUDINI_USER_PREF_DIR = hou.homeHoudiniDirectory()


# Turn on AutoSave
# hou.appendSessionModuleSource('''hou.hscript("autosave on")''')


# Cleanup Keymap
if os.path.exists(hou.text.expandString("$HOUDINI_USER_PREF_DIR/Houdini.keymap2.overrides")):
    os.remove(hou.text.expandString("$HOUDINI_USER_PREF_DIR/Houdini.keymap2.overrides"))
if os.path.exists(hou.text.expandString("$HOUDINI_USER_PREF_DIR/Modeler.keymap2.overrides")):
    os.remove(hou.text.expandString("$HOUDINI_USER_PREF_DIR/Modeler.keymap2.overrides"))
def updatekeymap():
    mytools.update_keymap()
hdefereval.executeDeferred(updatekeymap)


# Create Default Geo
hou.node('/obj').createNode('geo', 'geo').setSelected(True, True)


# Initialize Asset Definition Toolbar
def initAssetDefinitionToolbar():
    mytools.init_asset_bar_menu_sync(force=False)
hdefereval.executeDeferred(initAssetDefinitionToolbar)


# Hide UI Elements
def hideAssetDefinitionToolbar():
    mytools.set_asset_def_toolbar_state(3)
hdefereval.executeDeferred(hideAssetDefinitionToolbar)

def hideShelf():
    hou.ui.curDesktop().shelfDock().show(0)
    hou.hscript("set -g shelf_tab_val = '0'")
hdefereval.executeDeferred(hideShelf)


# Set UV Settings
def setUVSettings():
    mytools.set_display_uv("$HOUDINI_USER_PREF_DIR/packages/MyTools/lookdev/UVChecker_Empty_4K.png", 1)
    mytools.set_display_matcap("$HOUDINI_USER_PREF_DIR/packages/MyTools/lookdev/matcaps/ceramic_lightbulb.exr")
hdefereval.executeDeferred(setUVSettings)


# Desktop Cache Preloading
if PRELOAD_DESKTOP_CACHE:
    def precacheDesktops():
        mytools.build_desktop_cache()
    hdefereval.executeDeferred(precacheDesktops)


# Parameters Panel Auto-switch
def registerVSCSelectionCallback():
    try:
        from nodes.scripts import vex_wrangle
        vex_wrangle.register()
    except Exception:
        pass
hdefereval.executeDeferred(registerVSCSelectionCallback)