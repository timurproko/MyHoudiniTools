import hou
import os
import sys
import time
import subprocess
import hdefereval
import tempfile
import hashlib

QtCore = None
QtWidgets = None
Slot = None

_houdini_version = hou.applicationVersion()
_houdini_major = _houdini_version[0]

if "PySide6.QtCore" in sys.modules:
    QtCore = sys.modules["PySide6.QtCore"]
    QtWidgets = sys.modules.get("PySide6.QtWidgets")
    if QtWidgets is None:
        QtWidgets = sys.modules.get("PySide6.QtGui")
    Slot = QtCore.Slot
elif "PySide2.QtCore" in sys.modules:
    QtCore = sys.modules["PySide2.QtCore"]
    QtWidgets = sys.modules.get("PySide2.QtWidgets")
    if QtWidgets is None:
        QtWidgets = sys.modules.get("PySide2.QtGui")
    Slot = QtCore.Slot
elif "PySide.QtCore" in sys.modules:
    QtCore = sys.modules["PySide.QtCore"]
    QtWidgets = sys.modules.get("PySide.QtGui")
    Slot = QtCore.Slot

if QtCore is None or QtWidgets is None:
    if _houdini_major >= 21:
        try:
            from PySide6 import QtCore, QtWidgets
            Slot = QtCore.Slot
        except ImportError:
            try:
                from PySide2 import QtCore, QtWidgets
                Slot = QtCore.Slot
            except ImportError:
                pass
    else:
        try:
            from PySide2 import QtCore, QtWidgets
            Slot = QtCore.Slot
        except ImportError:
            try:
                from PySide import QtCore
                from PySide import QtGui as QtWidgets
                Slot = QtCore.Slot
            except ImportError:
                pass

if QtCore is None or QtWidgets is None:
    raise ImportError(
        "parms_watcher: Could not import Qt modules. "
        "Houdini {} should provide PySide2 or PySide6. "
        "Please check your Houdini installation.".format(_houdini_version)
    )

TEMP_FOLDER = os.environ.get("EXTERNAL_EDITOR_TEMP_PATH",
                             tempfile.gettempdir())

def is_valid_parm(parm):
    template = parm.parmTemplate()
    if template.dataType() in [hou.parmData.Float,
                               hou.parmData.Int,
                               hou.parmData.String]:
        return True
    return False

def is_python_node(node):
    node_def = node.type().definition()
    if not node_def:
        return False
    if node_def.sections().get("PythonCook") is not None:
        return True
    return False

def clean_exp(parm):
    try:
        exp = parm.expression()
        if exp == "":
            exp = None
    except hou.OperationFailed:
        exp = None
    if exp is not None:
        parm.deleteAllKeyframes()

def get_extra_file_scripts(node):
    node_def = node.type().definition()
    if node_def is None:
        return []
    extra_file_options = node_def.extraFileOptions()
    pymodules = [m.split('/')[0] for m in extra_file_options.keys() \
                 if "IsPython" in m \
                 and extra_file_options[m]]
    return pymodules

def get_config_file():
    try:
        return hou.findFile("ExternalEditor.cfg")
    except hou.OperationFailed:
        return os.path.join(hou.expandString("$HOUDINI_USER_PREF_DIR"), "ExternalEditor.cfg")

def set_external_editor():
    r = QtWidgets.QFileDialog.getOpenFileName(hou.ui.mainQtWindow(),
                                                "Select an external editor program")
    if r[0]:
        cfg = get_config_file()
        with open(cfg, 'w') as f:
            f.write(r[0])
        root, file = os.path.split(r[0])
        QtWidgets.QMessageBox.information(hou.ui.mainQtWindow(),
                                          "Editor set",
                                          "External editor set to: " + file)
        return r[0]
    return None

def get_external_editor():
    editor = os.environ.get("EDITOR")
    if not editor or not os.path.exists(editor):
        cfg = get_config_file()
        if os.path.exists(cfg):
            with open(cfg, 'r') as f:
                editor = f.read().strip()
        else:
            editor = ""
    if os.path.exists(editor):
        return editor
    else:
        r = QtWidgets.QMessageBox.information(hou.ui.mainQtWindow(),
                                             "Editor not set",
                                             "No external editor set, pick one ?",
                                             QtWidgets.QMessageBox.Yes,
                                             QtWidgets.QMessageBox.Cancel)
        if r == QtWidgets.QMessageBox.Cancel:
            return
        return set_external_editor()
    return None

def _read_file_data(file_name):
    with open(file_name, 'r') as f:
        data = f.read()
    if data == '':
        time.sleep(0.5)
        with open(file_name, 'r') as f:
            data = f.read()
    return data

if Slot is not None:
    @Slot(str)
    def filechanged(file_name):
        _filechanged_impl(file_name)
else:
    def filechanged(file_name):
        _filechanged_impl(file_name)

def _filechanged_impl(file_name):
    """ Signal emitted by the watcher to update the parameter contents.
        TODO: set expression when not a string parm.
    """
    parms_bindings = getattr(hou.session, "PARMS_BINDINGS", None)
    if not parms_bindings:
        return
    parm = None
    node = None
    tool = None
    try:
        binding = parms_bindings.get(file_name)
        if isinstance(binding, hou.Parm):
            parm = binding
        elif isinstance(binding, hou.Tool):
            tool = binding
        else:
            node = binding
        try:
            if binding == "__temp__python_source_editor":
                data = _read_file_data(file_name)
                try:
                    hou.setSessionModuleSource(data)
                except hou.OperationFailed:
                    print("Watcher error: Invalid source code.")
                return
        except hou.ObjectWasDeleted:
            remove_file_from_watcher(file_name)
            del parms_bindings[file_name]
            return
        if tool is not None:
            data = _read_file_data(file_name)
            try:
                tool.setScript(data)
            except hou.ObjectWasDeleted:
                remove_file_from_watcher(file_name)
                del parms_bindings[file_name]
                return
            return
        if node is not None:
            try:
                data = _read_file_data(file_name)
                section = "PythonCook"
                if "_extraSection_" in file_name:
                    section = file_name.split("_extraSection_")[-1].split('.')[0]
                watcher = get_file_watcher()
                watcher.blockSignals(True)
                node.type().definition().sections()[section].setContents(data)
                watcher.blockSignals(False)
            except hou.OperationFailed as e:
                print("parms_watcher: Can't update module content {}, watcher will be removed.".format(e))
                remove_file_from_watcher(file_name)
                del parms_bindings[file_name]
            return
        if parm is not None:
            try:
                parm.parmTemplate()
            except hou.ObjectWasDeleted:
                remove_file_from_watcher(file_name)
                del parms_bindings[file_name]
                return
            data = _read_file_data(file_name)
            template = parm.parmTemplate()
            if template.dataType() == hou.parmData.String:
                parm.set(data)
                return
            if template.dataType() == hou.parmData.Float:
                try:
                    data = float(data)
                    clean_exp(parm)
                    parm.set(data)
                    return
                except ValueError:
                    parm.setExpression(data)
                return
            if template.dataType() == hou.parmData.Int:
                try:
                    data = int(data)
                    clean_exp(parm)
                    parm.set(data)
                    return
                except ValueError:
                    parm.setExpression(data)
                return
    except Exception as e:
        print("Watcher error: " + str(e))

def get_file_ext(parm, type_="parm"):
    """ Get the file name's extention according to parameter's temaplate.
    """
    if type_ == "python_node":
        return ".py"
    template = parm.parmTemplate()
    editorlang = template.tags().get("editorlang", "").lower()
    if editorlang == "vex":
        return ".vfl"
    elif editorlang == "python":
        return ".py"
    elif editorlang == "opencl":
        return ".cl"
    else:
        try:
            if parm.expressionLanguage() == hou.exprLanguage.Python:
                return ".py"
            else:
                return ".txt"
        except hou.OperationFailed:
            return ".txt"

def get_file_name(data, type_="parm"):
    """ Construct an unique file name from a parameter with right extension.
    """
    if type_ == "parm":
        node = data.node()
        sid = str(node.sessionId())
        file_name = sid + '_' + node.name() + '_' + data.name() + get_file_ext(data)
        file_path = TEMP_FOLDER + os.sep + file_name
    elif type_ == "python_node" or "extra_section|" in type_:
        sid = hashlib.sha1(data.path().encode("utf-8")).hexdigest()
        name = data.name()
        if "extra_section|" in type_:
            name += "_extraSection_" + type_.split('|')[-1]
        file_name = sid + '_' + name + get_file_ext(data, type_="python_node")
        file_path = TEMP_FOLDER + os.sep + file_name
    elif type_.startswith("__shelf_tool|"):
        language = type_.split('|')[-1]
        if language == "python":
            file_name = "__shelf_tool_" + data.name() + ".py"
        else:
            file_name = "__shelf_tool_" + data.name() + ".txt"
        file_path = TEMP_FOLDER + os.sep + file_name
    elif type_ == "__temp__python_source_editor":
        file_name = "__python_source_editor.py"
        file_path = TEMP_FOLDER + os.sep + file_name
    return file_path

def get_file_watcher():
    return getattr(hou.session, "FILE_WATCHER", None)

def get_parm_bindings():
    return getattr(hou.session, "PARMS_BINDINGS", None)

def clean_files():
    """Clean up orphaned bindings and watcher entries.
    Simplified, reliable cleanup that checks object validity once.
    """
    bindings = get_parm_bindings()
    if not bindings:
        return
    
    keys_to_delete = []
    
    # Get a snapshot of bindings to avoid modification during iteration
    try:
        items = list(bindings.items())
    except (RuntimeError, KeyError):
        try:
            items = [(k, bindings[k]) for k in list(bindings.keys())]
        except Exception:
            return
    
    for file_path, binding in items:
        if not file_path or not isinstance(file_path, str):
            keys_to_delete.append(file_path)
            continue
        
        # Special case for session module source
        if binding == "__temp__python_source_editor":
            continue
        
        # Check if binding object is still valid
        is_valid = False
        try:
            if isinstance(binding, hou.Tool):
                binding.filePath()  # Test if tool is valid
                is_valid = True
            elif isinstance(binding, hou.Parm):
                binding.parmTemplate()  # Test if parm is valid
                is_valid = True
            elif isinstance(binding, hou.Node):
                binding.path()  # Test if node is valid
                is_valid = True
        except (hou.ObjectWasDeleted, AttributeError, RuntimeError, TypeError):
            is_valid = False
        
        if not is_valid:
            remove_file_from_watcher(file_path)
            keys_to_delete.append(file_path)
    
    # Remove invalid entries
    for k in keys_to_delete:
        try:
            if k in bindings:
                del bindings[k]
        except (KeyError, RuntimeError):
            pass

def _parm_deleted(parm, **kwargs):
    """Unified deletion handler for parm-based watchers."""
    try:
        file_name = get_file_name(parm, type_="parm")
        remove_file_from_watcher(file_name, delete_file=True)
    except Exception:
        pass

def _node_deleted(node, **kwargs):
    """Deletion handler for python node-based watchers."""
    try:
        file_name = get_file_name(node, type_="python_node")
        remove_file_from_watcher(file_name, delete_file=True)
    except Exception:
        pass

def add_watcher_to_section(selection):
    sel_def = selection.type().definition()
    if not sel_def: return
    sections = get_extra_file_scripts(selection)
    r = hou.ui.selectFromList(sections, exclusive=True,
                              title="Pick a section:")
    if not r: return
    section = sections[r[0]]
    add_watcher(selection, type_="extra_section|" + section)

def add_watcher(selection, type_="parm"):
    """ Create a file with the current parameter contents and 
        create a file watcher, if not already created and found in hou.Session,
        add the file to the list of watched files.

        Link the file created to a parameter where the tool has been executed from
        and when the file changed, edit the parameter contents with text contents.
    """
    file_path = get_file_name(selection, type_=type_)
    if type_ == "parm":
        try:
            data = selection.expression()
        except hou.OperationFailed:
            if os.environ.get("EXTERNAL_EDITOR_EVAL_EXPRESSION") == '1':
                data = str(selection.eval())
            else:
                data = str(selection.rawValue())
    elif type_ == "python_node":
        data = selection.type().definition().sections()["PythonCook"].contents()
    elif "extra_section|" in type_:
        sec_name = type_.split('|')[-1]
        sec = selection.type().definition().sections().get(sec_name)
        if not sec:
            print("Error: No section {} found.".format(sec))
        data = sec.contents()
    elif type_ == "__temp__python_source_editor":
        data = hou.sessionModuleSource()
    elif type_.startswith("__shelf_tool|"):
        data = selection.script()
    with open(file_path, 'w') as f:
        f.write(data)
    vsc = get_external_editor()
    if not vsc:
        hou.ui.setStatusMessage("No external editor set",
                                severity=hou.severityType.Error)
        return
    p = QtCore.QProcess(parent=hou.ui.mainQtWindow())
    p.start(vsc, [file_path])
    watcher = get_file_watcher()
    if not watcher:
        watcher = QtCore.QFileSystemWatcher([file_path],
                                            parent=hou.ui.mainQtWindow())
        watcher.fileChanged.connect(filechanged)
        hou.session.FILE_WATCHER = watcher
    else:
        if not file_path in watcher.files():
            watcher.addPath(file_path)
    parms_bindings = get_parm_bindings()
    if not parms_bindings:
        hou.session.PARMS_BINDINGS = {}
        parms_bindings = hou.session.PARMS_BINDINGS
    if not file_path in parms_bindings.keys():
        parms_bindings[file_path] = selection
        # Register deletion callbacks for automatic cleanup
        if type_ == "python_node" or "extra_section|" in type_:
            selection.addEventCallback((hou.nodeEventType.BeingDeleted,),
                                       _node_deleted)
        elif type_ == "parm":
            # Register callback on the node containing the parm
            # Capture file_path in closure to avoid issues with deleted parm
            node = selection.node()
            if node:
                # Capture file_path in closure
                captured_file_path = file_path
                def _node_deleted_handler(*args, **kwargs):
                    remove_file_from_watcher(captured_file_path, delete_file=True)
                node.addEventCallback((hou.nodeEventType.BeingDeleted,), _node_deleted_handler)
    clean_files()

def parm_has_watcher(parm):
    """ Check if a parameter has a watcher attached to it
        Used to display or hide "Remove Watcher" menu.
    """
    file_name = get_file_name(parm)
    watcher = get_file_watcher()
    if not watcher:
        return False
    parms_bindings = get_parm_bindings()
    if not parms_bindings:
        return False
    if file_name in parms_bindings.keys():
        return True
    return False

def tool_has_watcher(tool, type_=""):
    """ Check if a shelf tool has a watcher attached to it
        Used to display or hide "Remove Watcher" menu.
    """
    file_name = get_file_name(tool, type_=type_)
    watcher = get_file_watcher()
    if not watcher:
        return False
    parms_bindings = get_parm_bindings()
    if not parms_bindings:
        return False
    if file_name in parms_bindings.keys():
        return True
    return False

def _delete_temp_file(file_name):
    """Delete the temporary file if it exists.
    Simple, reliable file deletion without retries.
    """
    if not file_name or not isinstance(file_name, str):
        return False
    
    try:
        if os.path.exists(file_name):
            os.remove(file_name)
            return True
    except (OSError, PermissionError, FileNotFoundError):
        pass
    except Exception:
        pass
    
    return False

def remove_file_from_watcher(file_name, delete_file=True):
    """Remove file from watcher and bindings.
    Returns True if successfully removed, False otherwise.
    This is the single, reliable cleanup function.
    """
    if not file_name or not isinstance(file_name, str):
        return False
    
    removed = False
    try:
        watcher = get_file_watcher()
        if watcher:
            watched_files = watcher.files()
            if file_name in watched_files:
                watcher.removePath(file_name)
                removed = True
    except Exception:
        pass
    
    try:
        bindings = get_parm_bindings()
        if bindings and file_name in bindings:
            del bindings[file_name]
            removed = True
    except Exception:
        pass
    
    if delete_file:
        _delete_temp_file(file_name)
    
    return removed

def remove_parm_from_watcher(parm, type_="parm"):
    """Remove a parameter's file from watcher and bindings.
    This is a convenience function that gets the file name and removes it.
    Returns True if successfully removed, False otherwise.
    """
    try:
        file_name = get_file_name(parm, type_=type_)
        return remove_file_from_watcher(file_name)
    except Exception:
        return False

def remove_file_watched(parm, type_="parm"):
    """ Check if a given parameter's watched file exist and remove it
        from watcher list, do not remove the file itself.
    """
    file_name = get_file_name(parm, type_=type_)
    r = remove_file_from_watcher(file_name)
    if r:
        clean_files()
        QtWidgets.QMessageBox.information(hou.ui.mainQtWindow(),
                                          "Watcher Removed",
                                          "Watcher removed on file: " + file_name)

