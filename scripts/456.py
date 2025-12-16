import hdefereval
import mytools


# Start from Fist Frame
mytools.set_playback_frame()


# Keymap
def updatekeymap():
    mytools.update_keymap()
hdefereval.executeDeferred(updatekeymap)


# Ensure asset definition toolbar state is initialized when file is loaded
def initAssetDefinitionToolbar():
    # Ensure preference exists, and force-sync the radio-menu global.
    # HIP loads can reset Houdini globals, so we re-sync after file load.
    mytools.get_asset_def_toolbar_state()
    mytools.start_asset_bar_menu_sync()
    mytools.sync_asset_bar_menu_global(force=True)
hdefereval.executeDeferred(initAssetDefinitionToolbar)