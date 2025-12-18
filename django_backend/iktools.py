""" iktools
    Used for build react and copy files to django template folder(templates/react) for production.
    Please reference to django_backend/django_backend/settings.py and react/package.json
    2022-07-05
"""
import configparser
import os
from pathlib import Path

import core.utils.django_utils as ikDjangoUtils

PROJECT_APP = 'django_backend'

TEMPLATE_FOLDER = 'templates'
REACT_BUILD_OUTPUT_FOLDER = os.path.join(TEMPLATE_FOLDER, 'react')
REACT_2_DJANGO_IGNORE_STATIC_FOLDERS = []


def getDjangoReactFolder() -> Path:
    return Path(os.path.join(os.path.dirname(__file__), REACT_BUILD_OUTPUT_FOLDER))

def getDjangoAppStaticFolder() -> Path:
    return Path(os.path.join(os.path.dirname(__file__), TEMPLATE_FOLDER, 'apps'))

def getStaticFolders() -> list:
    return [Path(os.path.join(getDjangoReactFolder().resolve(), 'static')).resolve(),
            getDjangoAppStaticFolder().resolve()
    ]


def getAppNames() -> list:
    appNames = []
    projectRootDir = Path(os.path.join(os.path.dirname(__file__)))
    for dir in os.listdir(projectRootDir):
        if os.path.isdir(dir):
            appName = Path(dir).name
            if ' ' in appName or appName == PROJECT_APP or appName.startswith('__') or appName.startswith('.'):
                # e.g. 'dev source', '__pycache__', '.git'
                continue  # ignore folders if it contains blank character.
            # check the app folder has apps.py file or not
            if Path(os.path.join(dir), 'apps.py').is_file():
                appNames.append(appName)
    return appNames


def getDjangoAppConfigs() -> list:
    '''
        Load django apps except "django_backend". Sorts by app name
    '''
    appNames = getAppNames()
    appConfigs = []
    projectRootDir = Path(os.path.join(os.path.dirname(__file__)))
    for appName in appNames:
        dir = os.path.join(projectRootDir, appName)
        if os.path.isdir(dir):
            # check the the apps.py file is exists or not
            appFile = Path(os.path.join(dir, 'apps.py'))
            # get configuration class name. E.g. testApp.apps.TestAppConfig
            className = ''
            for appNameItem in appName.split('_'):
                appNameItem2 = appNameItem[0].upper() + appNameItem[1:] 
                className = '%s%s' % (className, appNameItem2)
            className = className + 'Config'
            configClassName = appName + '.apps.' + className
            # check the class is exists or not
            try:
                data = []
                with open(appFile, 'r', encoding='utf-8') as file:
                    data = file.readlines()
                for line in data:
                    if ('class %s(AppConfig):' % className) in line:
                        appConfigs.append(configClassName)
                        break
            except Exception as e:
                print('ERROR get app [%s] config failed: %s' % (appName, str(e)))
    appConfigs.sort()
    # always put the core app at the first
    if 'core.apps.CoreConfig' in appConfigs:
        appConfigs.remove('core.apps.CoreConfig')
        appConfigs.insert(0, 'core.apps.CoreConfig')
    return appConfigs


def getAppUrlFiles() -> list:
    '''
        Load django apps except "django_backend". Sorts by app name.
    '''
    urlFiles = []
    if ikDjangoUtils.isRunDjangoServer():
        appNames = getAppNames()
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
        p = Path(os.path.join(Path(os.path.abspath(__file__)).parent.resolve(), 'config.ini'))
        if not p.is_file():
            raise Exception('File [%s] is not found.' % p.name)
        self.conf = configparser.ConfigParser()
        self.conf.read(p.resolve())

    def get(self, section: str, name:str, defaultValue:str = None) -> str:
        try:
            v = self.conf.get(section, name)
            return v if v is not None and str(v).strip() != '' else defaultValue
        except:
            return defaultValue
        
    def get_bool(self, section: str, name:str, defaultValue: bool = None) -> bool:
        """
            return None if the config doesn't exist. Otherwise true/false
        """
        try:
            v = self.get(section, name, defaultValue=None)
            if v is None or str(v).strip() == '':
                return None
            return str(v).strip().lower() == 'true'
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
IK_CONFIG = IkConfig # use IK_CONFIG to replace IkConfig