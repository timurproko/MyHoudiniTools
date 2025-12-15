"""Register modules for direct import compatibility."""
import sys

_COMPAT_MODULES = ['vex_wrangle', 'visualize', 'output']

for module_name in _COMPAT_MODULES:
    try:
        module = __import__(f'nodes.scripts.{module_name}', fromlist=[module_name])
        sys.modules[module_name] = module
    except ImportError:
        pass

