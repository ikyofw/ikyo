import sys

def isRunDjangoServer() -> bool:
    '''
        makemigrations command don't need to call database
    '''
    return 'runserver' in sys.argv

def instanceClass(tagetClass) -> object:
    '''
        create a class instance when run django server
        tagetClass (str/class)
    '''
    if isRunDjangoServer(): # 
        ClassObject = globals()[tagetClass] if type(tagetClass) == str else tagetClass
        instance = ClassObject()
        return instance
    return None