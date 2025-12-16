import hdefereval
import mytools


# Start from Fist Frame
mytools.set_playback_frame()


# Keymap
def updatekeymap():
    mytools.update_keymap()
hdefereval.executeDeferred(updatekeymap)


# Initialize Asset Definition Toolbar
def initAssetDefinitionToolbar():
    mytools.init_asset_bar_menu_sync(force=True)
hdefereval.executeDeferred(initAssetDefinitionToolbar)