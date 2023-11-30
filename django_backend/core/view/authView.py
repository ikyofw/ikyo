import csv
import inspect
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock

import core.core.fs as ikfs
import core.core.http as ikHttp
import core.utils.datetimeUtils as datetimeUtils
from core.auth.index import Authentication, UserPermission
from core.core.exception import IkException
from core.models import User
from core.user.session import SessionManager
from django.core.handlers.wsgi import WSGIHandler
from iktools import IkConfig
from rest_framework.views import APIView

logger = logging.getLogger('backend')

SESSION_DATA_NAME_PREFIX = '$IKG_'
SESSION_DATA_NAME = '$IK_$G'
SESSION_VIEW_DATA_NAME = '$IK_$S'
SESSION_DATA_TIMESTAMP_SUFFIX = '_$TIMESTAMP'

_RuntimeOutputLock = Lock()
_RuntimeOutputHasAddHeader = False


class AuthAPIView(APIView):
    authentication_classes = [Authentication, ]
    permission_classes = [UserPermission, ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.__viewUUID = None  # client request ID. E.g. SUUID, each screen instance has its own suuid
        self.__instanceID = int(datetime.now().timestamp() * 1e6)

    def getCurrentUser(self) -> User:
        '''
            return User
        '''
        return self.request.user

    def getCurrentUserId(self) -> int:
        user = self.getCurrentUser()
        return None if user is None else user.id

    def getCurrentUserName(self) -> int:
        user = self.getCurrentUser()
        return None if user is None else user.usr_nm

    def getViewUrl(self) -> str:
        '''
            this function is used for urls.py file
        '''
        return self.__class__.__name__.lower()

    def __isUseSession(self) -> bool:
        return ikHttp.isSupportSession(self.request)

    def __getSessionParameterName(self, name, isGlobal=False) -> str:
        if self.__isUseSession():
            return name
        else:
            if isGlobal:
                return '%s%s' % (SESSION_DATA_NAME_PREFIX, name)
            className = self.__class__.__name__
            return '%s_%s' % (className, name)

    def __getSessionParameterTimestampName(self, name) -> str:
        return '%s%s' % (name, SESSION_DATA_TIMESTAMP_SUFFIX)

    def __getSessionData(self, isGlobal=False, isDelete=False) -> dict:
        name = SESSION_DATA_NAME if isGlobal else SESSION_VIEW_DATA_NAME
        data = self.request.session.get(name, None)
        if data is None and not isDelete:
            data = {}
            self.request.session[name] = data
            self.request.session[self.__getSessionParameterTimestampName(name)] = datetime.now().timestamp()
        elif isGlobal and isDelete:
            del self.request.session[self.__getSessionParameterTimestampName(name)]
            del self.request.session[name]
        if not isGlobal:
            dataSetName = self.__viewUUID
            if dataSetName is None or dataSetName == '':
                dataSetName = '%s.%s' % (inspect.getmodule(self).__name__, self.__class__.__name__)
            screenData = data.get(dataSetName, None)
            if screenData is None and not isDelete:
                screenData = {}
                data[dataSetName] = screenData
                data[self.__getSessionParameterTimestampName(dataSetName)] = datetime.now().timestamp()
            elif isDelete:
                del data[self.__getSessionParameterTimestampName(dataSetName)]
                del data[dataSetName]
            data = screenData
        return data

    def ____popSessionData(self, data, name, default=None) -> any:
        data.pop(self.__getSessionParameterTimestampName(name), None)
        return data.pop(name, default)

    def getSessionParameter(self, name, delete=False, default=None, isGlobal=False) -> any:
        '''
            return object
        '''
        name2 = self.__getSessionParameterName(name, isGlobal)
        if self.__isUseSession():
            data = self.__getSessionData(isGlobal)
            if delete:
                return self.____popSessionData(data, name2, default)
            else:
                return data.get(name2, default)
        else:
            if delete:
                return SessionManager.getPrmAndDelete(self.getCurrentUser(), name2, defaultValue=default)
            else:
                return SessionManager.getPrms(self.getCurrentUser(), name2, defaultValue=default)

    def getSessionParameterInt(self, name, delete=False, default=None, isGlobal=False) -> int:
        if self.__isUseSession():
            value = self.getSessionParameter(name, delete=delete, default=default, isGlobal=isGlobal)
            return None if value is None else int(value)
        else:
            name2 = self.__getSessionParameterName(name, isGlobal)
            if delete:
                value = SessionManager.getPrmAndDelete(self.getCurrentUser(), name2, defaultValue=default)
                return None if value is None else int(value)
            else:
                value = SessionManager.getPrms(self.getCurrentUser(), name2, defaultValue=default)
                return None if value is None or value == '' else int(value)

    def getSessionParameterBool(self, name, delete=False, default=None, isGlobal=False) -> bool:
        '''
            return: None/True/False
        '''
        if self.__isUseSession():
            value = self.getSessionParameter(name, delete=delete, default=default, isGlobal=isGlobal)
            return None if value is None else bool(value)
        else:
            name2 = self.__getSessionParameterName(name, isGlobal)
            if delete:
                value = SessionManager.getPrmAndDelete(self.getCurrentUser(), name2, defaultValue=default)
                return None if value is None else bool(value)
            else:
                value = SessionManager.getPrms(self.getCurrentUser(), name2, defaultValue=default)
                return None if value is None or value == '' else bool(value)

    def setSessionParameters(self, parameters: dict, isGlobal: bool = False) -> None:
        if parameters is not None:
            for key, value in parameters.items():
                self.setSessionParameter(key, value, isGlobal)

    def setSessionParameter(self, name, value, isGlobal=False) -> None:
        if self.__isUseSession():
            data = self.__getSessionData(isGlobal)
            name2 = self.__getSessionParameterName(name, isGlobal)
            data[name2] = value
            data[self.__getSessionParameterTimestampName(name2)] = datetime.now().timestamp()
        else:
            name2 = self.__getSessionParameterName(name, isGlobal)
            SessionManager.updatePrms(self.getCurrentUser(), name2, value)

    def cleanSessionParameters(self, isGlobal=False) -> None:
        if self.__isUseSession():
            self.__getSessionData(isGlobal, isDelete=True)
            # namePrefix = self.__getSessionParameterName('', isGlobal)
            # for name in list(data.keys()):
            #    if name.startswith(namePrefix):
            #        self.____popSessionData(data, name)
        else:
            self.deleteSessionParameters(nameFilters="*")

    def deleteSessionParameters(self, nameFilters, isGlobal=False) -> None:
        ''' 
            nameFilter: str: "dog" / "*dog" / "*dog*" / "*dog" or a list
        '''
        if self.__isUseSession():
            name2 = []
            if type(nameFilters) == list:
                name2 = nameFilters
            else:
                name2 = [nameFilters]
            data = self.__getSessionData(isGlobal)
            keys = list(data.keys())
            namePrefix = self.__getSessionParameterName('', isGlobal)
            namePrefixLen = len(namePrefix)
            for nameFilter in name2:
                if '*' in nameFilter:
                    if len(nameFilter) > 2 and nameFilter[0] == '*' and nameFilter[-1] == '*':
                        # "*xx*"
                        key = nameFilter[1:-1]
                        for name in keys:
                            if name.startswith(namePrefix) and key in name[namePrefixLen:]:
                                self.____popSessionData(data, name)
                    elif nameFilter[0] != '*' and nameFilter[-1] == '*':
                        # start with: __startswith
                        key = nameFilter[:-1]
                        for name in keys:
                            if name.startswith(namePrefix) and name[namePrefixLen:].startswith(key):
                                self.____popSessionData(data, name)
                    elif nameFilter[-1] != '*' and nameFilter[0] == '*':
                        # end with: __endswith
                        key = nameFilter[1:]
                        for name in keys:
                            if name.startswith(namePrefix) and name[namePrefixLen:].endswith(key):
                                self.____popSessionData(data, name)
                    else:
                        self.cleanSessionParameters(isGlobal)
                        break
                else:
                    name3 = self.__getSessionParameterName(nameFilter, isGlobal)
                    self.____popSessionData(data, name3)
        else:
            name2 = None
            if type(nameFilters) == list:
                name2 = []
                for name in nameFilters:
                    name2.append(self.__getSessionParameterName(name, isGlobal))
            else:
                name2 = self.__getSessionParameterName(nameFilters, isGlobal)
            return SessionManager.deletePrms(self.getCurrentUser(), name2)

    def _logDuration(self, startTime: datetime, endTime: datetime = None, actionName: str = None, description: str = None) -> None:
        global _RuntimeOutputLock, _RuntimeOutputHasAddHeader

        try:
            if startTime is None:
                return
            if str(IkConfig.get('System', 'debugRunTime', 'false')).strip().lower() != 'true':
                return  # ignore
            outputFile = IkConfig.get('System', 'debugRunTimeOutputFile', 'var/logs/runtime.csv').replace('\\', '/').strip()
            if not outputFile.startswith('/'):
                if outputFile.startswith('var/'):
                    outputFile = outputFile[4:]
                outputFile = ikfs.getVarFolder(outputFile)
            outputFile = Path(outputFile)

            methodName = ''
            frame = inspect.currentframe().f_back
            callerModule = inspect.getmodule(frame).__name__
            callerClass = frame.f_locals.get('self', None).__class__.__name__
            callerMethod = frame.f_code.co_name
            try:
                v = getCurrentView()
                if v is not None:
                    callerModule = v.__module__
            except:
                pass
            if endTime is None:
                endTime = datetime.now()
            seconds = (endTime - startTime).total_seconds()
            csvContent = []
            csvContent.append([datetime.strftime(endTime, '%Y-%m-%d %H:%M:%S.%f'),
                               self.__instanceID,
                               callerModule,
                               callerClass,
                               callerMethod,
                               actionName,
                               self.request.method,
                               self.request.build_absolute_uri(),
                               self.request.path,
                               datetime.strftime(startTime, '%Y-%m-%d %H:%M:%S.%f'),
                               datetime.strftime(endTime, '%Y-%m-%d %H:%M:%S.%f'),
                               seconds,
                               datetimeUtils.getDurationStr(startTime, endTime),
                               description
                               ])

            _RuntimeOutputLock.acquire()
            try:
                if not _RuntimeOutputHasAddHeader:
                    isNewFile = not outputFile.is_file()
                    if isNewFile:
                        csvContent.insert(0, ['date',
                                              'request id',
                                              'module',
                                              'class',
                                              'caller',
                                              'api action',
                                              'http method',
                                              'http url',
                                              'http path',
                                              'start time',
                                              'end time',
                                              'duration in seconds',
                                              'duration time',
                                              'description'
                                              ])
                        ikfs.mkParentDirs(outputFile)
                    _RuntimeOutputHasAddHeader = True
                with open(outputFile, 'a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerows(csvContent)
            finally:
                _RuntimeOutputLock.release()

            methodName = "%s.%s:%s" % (callerModule, callerClass, callerMethod)
            logger.info('Duration %s (%s) = %s, %s' % (methodName, '-' if actionName is None else actionName,
                        datetimeUtils.getDurationStr(startTime), description))
        except Exception as e:
            logger.error(e, exc_info=True)


def getCurrentView() -> AuthAPIView:
    '''
        return django_backend.core.view.authView.AuthAPIView
    '''
    screenView = None
    stacks = inspect.stack()
    for stack in stacks:
        caller = stack.frame.f_locals.get('self', None)
        if caller is not None:
            if isinstance(caller, AuthAPIView):
                screenView = caller
                break
            elif isinstance(caller, WSGIHandler):
                break
    if screenView is None:
        raise IkException('Unsupport session caller.')
    return screenView
