"""Register modules for direct import compatibility."""
import sys
import os
import pkgutil

for importer, modname, ispkg in pkgutil.iter_modules(__path__, __name__ + "."):
    if not ispkg:
        module_name = modname.split('.')[-1]
        try:
            module = __import__(modname, fromlist=[module_name])
            sys.modules[module_name] = module
        except ImportError:
            pass
