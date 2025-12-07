import hdefereval
import mytools


# Start from Fist Frame
mytools.set_playback_frame()


# Keymap
def updatekeymap():
    mytools.update_keymap()
hdefereval.executeDeferred(updatekeymap)