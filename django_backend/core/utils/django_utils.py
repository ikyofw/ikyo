import inspect
import sys
import os


def isRunDjangoServer() -> bool:
    '''
        makemigrations command don't need to call database
    '''
    # debug in VS code
    stack = inspect.stack()
    for frame in stack[1:]:
        if frame.filename.replace("\\", "/").endswith("debugpy/server/cli.py"):
            return False
    # python makemigrations app
    return os.environ.get("RUN_MAIN") == "true" or "runserver" in sys.argv


def instanceClass(tagetClass) -> object:
    '''
        create a class instance when run django server
        tagetClass (str/class)
    '''
    if isRunDjangoServer():
        ClassObject = globals()[tagetClass] if type(tagetClass) == str else tagetClass
        instance = ClassObject()
        return instance
    return None
