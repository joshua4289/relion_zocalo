import importlib

def find_module(full_module_name):
    """
    Returns module object if module `full_module_name` can be imported. 

    Returns None if module does not exist. 

    Exception is raised if (existing) module raises exception during its import.
    """
    try:
        return importlib.import_module(full_module_name)
    except ImportError as exc:
        if not (full_module_name + '.').startswith(exc.name + '.'):
            raise
    
# this is not a dependency for the zocalo runners . This is specifically
# a dependency for the cryolo wrappers 

if __name__ == "__main__":
    find_module('gemmi')
    find_module('numpy')
    find_module('relion_yolo_it')	
    
