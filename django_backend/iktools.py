""" iktools
    Used for build react and copy files to django template folder(templates/react) for production.
    Please reference to django_backend/django_backend/settings.py and react/package.json
    2022-07-05
"""
import os
import configparser
from pathlib import Path
import core.utils.djangoUtils as ikDjangoUtils

PROJECT_APP = 'django_backend'

TEMPLATE_FOLDER = 'templates'
REACT_BUILD_OUTPUT_FOLDER = os.path.join(TEMPLATE_FOLDER, 'react')
REACT_2_DJANGO_IGNORE_STATIC_FOLDERS = []


def getDjangoReactFolder() -> Path:
    return Path(os.path.join(os.path.dirname(__file__), REACT_BUILD_OUTPUT_FOLDER))


def getStaticFolder() -> str:
    return Path(os.path.join(getDjangoReactFolder().absolute(), 'static')).absolute()


def __getAppNames() -> list:
    appNames = []
    projectRootDir = Path(os.path.join(os.path.dirname(__file__)))
    for dir in os.listdir(projectRootDir):
        if os.path.isdir(dir):
            appName = Path(dir).name
            if ' ' in appName or appName == PROJECT_APP:
                continue  # ignore folders if it contains blank character.
            appNames.append(appName)
    return appNames


def getDjangoAppConfigs() -> list:
    '''
        Load django apps except "django_backend". Sorts by app name
    '''
    appNames = __getAppNames()
    appConfigs = []
    projectRootDir = Path(os.path.join(os.path.dirname(__file__)))
    for appName in appNames:
        dir = os.path.join(projectRootDir, appName)
        if os.path.isdir(dir):
            # check the the apps.py file is exists or not
            appFile = Path(os.path.join(dir, 'apps.py'))
            if appFile.is_file():
                # get configuration class name. E.g. testApp.apps.TestAppConfig
                className = appName[0].upper() + appName[1:] + 'Config'
                configClassName = appName + '.apps.' + className
                # check the class is exists or not
                try:
                    data = []
                    with open(appFile) as file:
                        data = file.readlines()
                    for line in data:
                        if ('class %s(AppConfig):' % className) in line:
                            appConfigs.append(configClassName)
                            break
                except Exception as e:
                    print('ERROR %s' % str(e))
    appConfigs.sort()
    return appConfigs


def getAppUrlFiles() -> list:
    '''
        Load django apps except "django_backend". Sorts by app name.
    '''
    urlFiles = []
    if ikDjangoUtils.isRunDjangoServer():
        appNames = __getAppNames()
        projectRootDir = Path(os.path.join(os.path.dirname(__file__)))
        for appName in appNames:
            dir = os.path.join(projectRootDir, appName)
            if os.path.isdir(dir):
                # check the the urls.py file is exists or not
                urlsFile = Path(os.path.join(dir, 'urls.py'))
                if urlsFile.is_file():
                    urlModel = appName + '.urls'
                    # check the lsit urlpatterns is exists or not
                    try:
                        data = []
                        with open(urlsFile) as file:
                            data = file.readlines()
                        for line in data:
                            if 'urlpatterns=[' in line.replace(' ', ''):
                                urlFiles.append(urlModel)
                                break
                    except Exception as e:
                        print('ERROR %s' % str(e))
        urlFiles.sort()
    return urlFiles


class __IkConfig():
    def __init__(self) -> None:
        p = Path(os.path.join(Path(os.path.abspath(__file__)).parent.absolute(), 'config.ini'))
        if not p.is_file():
            raise Exception('File [%s] is not found.' % p.name)
        self.conf = configparser.ConfigParser()
        self.conf.read(p.absolute())

    def get(self, section, name, defaultValue=None) -> str:
        try:
            v = self.conf.get(section, name)
            return v if v is not None else defaultValue
        except:
            return defaultValue

    def getSystem(self, name, defaultValue=None) -> str:
        '''
            get section "System" information
        '''
        return self.get('System', name, defaultValue)

    @property
    def production(self) -> bool:
        return self.get('System', 'production', 'false').lower() == 'true'

    @property
    def isDebug(self) -> bool:
        return self.get('System', 'debug', 'false').lower() == 'true'

    @property
    def isSuperUser(self) -> bool:
        '''
            return true if not production and superUser is true
        '''
        return not self.production and (self.get('System', 'superUser', 'false').lower() == 'true')


IkConfig = __IkConfig()