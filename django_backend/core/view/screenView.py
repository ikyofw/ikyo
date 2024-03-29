import datetime
import inspect
import logging
import os
import pathlib
import random
import string
import traceback
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import sqlparse
from django.core.handlers.wsgi import WSGIHandler
from django.db import connection
from django.db.models.query import QuerySet
from django.db.utils import DatabaseError, DataError, IntegrityError, ProgrammingError
from django.http.response import HttpResponseBase, StreamingHttpResponse
import core.core.fs as ikfs
import core.core.http as ikhttp
import core.db.model as ikDbModels
import core.models as ikModels
import core.ui.ui as ikui
import core.utils.db as dbUtils
import core.utils.modelUtils as modelUtils
import core.utils.spreadsheet as spreadsheet
from core.core.code import MessageType
from core.core.exception import IkException, IkMessageException, IkValidateException
from core.core.lang import Boolean2
from core.db.model import DummyModel, Model
from core.db.transaction import IkTransaction, IkTransactionForeignKey
from core.menu.menuManager import MenuManager
from core.sys.accessLog import addAccessLog
from core.utils.langUtils import isNotNullBlank, isNullBlank
from core.view.authView import AuthAPIView
from iktools import IkConfig

logger = logging.getLogger('ikyo')

REQUEST_PRM_ACTION = 'action'
REQUEST_SYSTEM_ACTION_INIT_SCREEN = 'initScreen'
REQUEST_SYSTEM_ACTION_GET_SCREEN = 'getScreen'
REQUEST_SYSTEM_ACTION_LOAD_SCREEN_COMPLETED = 'LOAD_SCREEN_DONE'
REQUEST_SYSTEM_ACTION_UNLOADED_SCREEN = 'UNLOADED_SCREEN'

SCREEN_INIT_PRM_MENU_NAME = 'MenuName'
'''
    ik_menu.menu_nm
'''

SCREEN_INIT_PRM_FNC_CATEGORY = 'FunctionCategory'
'''
    function category. E.g. GP/SC
'''

SCREEN_INIT_PRM_FNC_CODE = 'FunctionCode'
'''
    function code. E.g. GP020. 
'''

PARAMETER_KEY_NAME_LAST_REQUEST_DATA = 'lastRequestData'
PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_NAME = 'LAST_RESULT_TABLE_FIELD_GROUP_NAME'
PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_NAME = 'LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_VALUE'
PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_DATA_NAME = 'LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_DATA_FIELD_NAME'
PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_NAME = 'LAST_RESULT_TABLE_FIELD_GROUP_EDIT_VALUE'
PARAMETER_KEY_NAME_SCREEN_UUID = 'SUUID'
PARAMETER_KEY_NAME_SUB_SCREEN_NAME = 'SUB_SCREEN_NAME'

_OPEN_SCREEN_KEY_NAME = 'OPEN_SCREEN'
_OPEN_SCREEN_PARAM_KEY_NAME = 'OPEN_SCREEN_PARAM'


class TableCursorInfo:
    '''
        used for result table
    '''

    def __init__(self, requestData) -> None:
        fgName = requestData.get(PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_NAME, None) if requestData else None
        fieldName = requestData.get(PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_NAME, None) if requestData else None
        dataName = requestData.get(PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_DATA_NAME, None) if requestData else None
        dataValue = requestData.get(PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_NAME, None) if requestData else None
        if dataName == 'id':
            # TODO: get data field's data type
            dataValue = None if isNullBlank(dataValue) else int(dataValue)
        self.__fgName = fgName
        self.__fieldName = fieldName
        self.__dataName = dataName
        self.__dataValue = dataValue

    @property
    def fieldGroupName(self) -> str:
        return self.__fgName

    @property
    def fieldName(self) -> str:
        return self.__fieldName

    @property
    def dataFieldName(self) -> str:
        return self.__dataName

    @property
    def dataValue(self) -> object:
        return self.__dataValue


class ScreenAPIView(AuthAPIView):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._menuName = None  # ik_menu.menu_nm
        self._menuID = None
        self._screen = None
        self._functionCategory = None
        self._functionCode = None
        self._httpMethod = None
        self._SUUID = None
        '''
            post/get/delete/put (lower case)
        '''
        self._requestAction = None
        '''
            http request action
        '''

        self._isGetDataRequest = False
        '''
            http get data request flag
        '''

        self._messages = []
        '''
            response messages
        '''

        self._staticResources = []
        '''
            static resource files. Reference to django_backend/core/core/http.py.IkResponseStaticResource
        '''

        self.beforeDisplayAdapter = None
        '''
            call this method in _getScreenResponse().
            parameters: screen
        '''

        self.beforeDisplayResponseAdapter = None
        '''
            call this method in _getScreenResponse().
            parameters: screenJson
        '''

        self._requestData = None
        self._lastRequestData = None  # dict, can be None

        self._fieldGroupData = {}

        for key, value in kwargs.items():
            if SCREEN_INIT_PRM_MENU_NAME == key:
                self._menuName = None
            elif SCREEN_INIT_PRM_FNC_CATEGORY == key:
                self._functionCategory = value
            elif SCREEN_INIT_PRM_FNC_CODE == key:
                self._functionCode = value
        self._initMenu(**kwargs)
        if not isNullBlank(self._menuName) and (isNullBlank(self._functionCategory) or isNullBlank(self._functionCode)):
            self.__updateFunctionInfoFromMenu()

    def _initMenu(self, **kwargs) -> None:
        """Initialize variable self._menuName and self._menuID when instantiate a view class.
        
        Get the menu name and by class name.
        """
        menuName = self.getMenuName()
        if isNullBlank(menuName):
            screenName = self.__class__.__name__
            menuNames = MenuManager.getMenuNamesByScreenName(screenName)
            if len(menuNames) > 2:
                logger.warning("Too many screen [%s] found in menu table for view class [%s]." % (screenName, self.__class__.__module__, self.__class__.__qualname__))
            elif len(menuNames) == 0:
                logger.warning("Screen [%s] doesn't find in menu table for view class [%s.%s]." % (screenName, self.__class__.__module__, self.__class__.__qualname__))
            else: # find one screen
                menuName = menuNames[0]
                menuInfoDict = MenuManager.getMenuInfoByMenuName(menuName)
                self._menuID = menuInfoDict['id']
        else:
            self._menuID = MenuManager.getMenuId(menuName=menuName)
        self.setMenuName(menuName)

    # override
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

    def _getTableDataIndex(self, fieldGroupName) -> any:
        return self.getSessionParameter(fieldGroupName + '_EditIndexField')

    def _removeTableDataIndex(self, fieldGroupName) -> None:
        self.deleteSessionParameters(fieldGroupName + '_EditIndexField')

    def _setTableDataIndex(self, fieldGroupName, value) -> None:
        self.setSessionParameter(fieldGroupName + '_EditIndexField', value)

    def _getEditIndexField(self) -> int:
        idStr = self.getRequestData().get('EditIndexField')
        return None if isNullBlank(idStr) else int(idStr)

    def __updateFunctionInfoFromMenu(self) -> None:
        if not isNullBlank(self._menuName) and (isNullBlank(self._functionCategory) or isNullBlank(self._functionCode)):
            menuInfoDict = MenuManager.getMenuInfoByMenuName(self._menuName)
            if menuInfoDict is None:
                raise IkMessageException('System error: menu [%s] does not exist.' % self._menuName)
            if isNullBlank(self._functionCategory):
                ctg = menuInfoDict.get('ctg', None)
                self._functionCategory = None if ctg == '' else ctg
            if isNullBlank(self._functionCode):
                code = menuInfoDict.get('cd', None)
                self._functionCode = None if code == '' else code

    def setMenuName(self, menuName: str) -> None:
        self._menuName = menuName
        self.__updateFunctionInfoFromMenu()

    def getMenuName(self) -> str:
        return self._menuName

    # YL.ikyo, 2023-06-20 get user menu acl - start
    def isACLWriteable(self) -> bool:
        userID = self.getCurrentUserId()
        if not userID:
            return False
        menuName = self.getMenuName()
        if isNullBlank(menuName):
            return False
        menuID = MenuManager.getMenuId(menuName)
        if not menuID:
            return False
        groupsIDs = ikModels.UserGroup.objects.filter(usr_id=userID).values_list('grp_id', flat=True)
        if len(groupsIDs) == 0:
            return False
        aclPermissions = ikModels.GroupMenu.objects.filter(grp__in=groupsIDs, menu__id=menuID).values_list('acl', flat=True)
        return False if aclPermissions is None else 'W' in aclPermissions

    def isACLReadOnly(self) -> bool:
        userID = self.getCurrentUserId()
        if not userID:
            return False
        menuName = self.getMenuName()
        if isNullBlank(menuName):
            return False
        menuID = MenuManager.getMenuId(menuName)
        if not menuID:
            return False
        groupsIDs = ikModels.UserGroup.objects.filter(usr_id=userID).values_list('grp_id', flat=True)
        if len(groupsIDs) == 0:
            return False
        aclPermissions = ikModels.GroupMenu.objects.filter(grp__in=groupsIDs, menu__id=menuID).values_list('acl', flat=True)
        return False if aclPermissions is None else 'R' in aclPermissions
    
    def isACLDeny(self) -> bool:
        """User doesn't have write and read rights.
        """
        return not self.isACLWriteable() and not self.isACLReadOnly()

    # YL.ikyo, 2023-06-20 - end

    def setFunctionCategory(self, category) -> None:
        self._functionCategory = category

    def getFunctionCategory(self) -> str:
        '''
            function category. E.g. ABC, EFG
        '''
        return self._functionCategory

    def setFunctionCode(self, code) -> None:
        self._functionCode = code

    def getFunctionCode(self) -> str:
        '''
            return function code. E.g. ABC999.
        '''
        return self._functionCode

    def getScreen(self) -> ikui.Screen:
        return self._screen

    def beforeInitScreenData(self, screen: ikui.Screen) -> None:
        pass

    def beforeDisplayScreen(self, screen: ikui.Screen) -> None:
        pass

    def _getScreenResponse(self) -> ikhttp.IkSccJsonResponse:
        _startTime = datetime.datetime.now()
        screen = self._screen
        try:
            self.beforeInitScreenData(screen)
            ikui.IkUI.initScreenData(screen, initDataCallBack=self.initScreenData)
            if self.beforeDisplayAdapter:
                self.beforeDisplayAdapter(screen)
            self.beforeDisplayScreen(screen=screen)
            screenJson = ikui.IkUI.screen2Json(screen)
            if self.beforeDisplayResponseAdapter:
                self.beforeDisplayResponseAdapter(screenJson)
            logger.debug(screenJson)
            return ikhttp.IkSccJsonResponse(data=screenJson)
        except Exception as e:
            logger.error('_getScreenResponse error. screen=%s, error=%s' % (self._menuID, str(e)))
            logger.error(e, exc_info=True)
            return ikhttp.IkErrJsonResponse(message='System error.')
        finally:
            self._logDuration(_startTime, description='_getScreenResponse')

    def initScreenData(self, fieldGroup, field, recordsetName, getDataMethodName) -> tuple:
        '''
            return (getDataDone, returnData)
        '''
        _startTime = datetime.datetime.now()
        try:
            r = None
            getDataDone = False
            if fieldGroup.visible:
                if getDataMethodName is not None:
                    for i in dir(self):
                        if i == getDataMethodName and callable(getattr(self, i)):
                            getDataDone = True
                            fn = getattr(self, i)
                            r = None
                            try:
                                r = fn()
                            except IkException as pye:
                                self._addErrorMessage(str(pye))
                            break
                if not getDataDone:
                    # if the method is not found, then get data from recordset defination
                    if recordsetName is not None:
                        r = self.__getRecordSetData(fieldGroup, field, recordsetName)
                    getDataDone = True
            else:
                getDataDone = True  # no need to get data for invisible field group
            data = None
            if r is None:
                if fieldGroup.isTable():
                    data = []
                elif fieldGroup.isDetail():
                    data = {}
                else:
                    data = None
            else:
                tableModelAdditionalFields = []
                for field in fieldGroup.fields:
                    if field.dataField and (ikDbModels.FOREIGN_KEY_VALUE_FLAG in field.dataField \
                        or field.dataField.startswith(ikDbModels.MODEL_PROPERTY_ATTRIBUTE_NAME_PREFIX)):
                        tableModelAdditionalFields.append(field.dataField)
                if isinstance(r, ikhttp.IkJsonResponse):
                    self._addMessages(r.messages)
                    self.__updateDataCursor(fieldGroup, r.data)
                    data = r.getJsonData(modelAdditionalFields=tableModelAdditionalFields)
                else:
                    self.__updateDataCursor(fieldGroup, r)
                    data = ikhttp.IkSccJsonResponse(data=r).getJsonData(modelAdditionalFields=tableModelAdditionalFields)
            self._fieldGroupData[fieldGroup.name] = data
            if recordsetName is not None:
                self.setSessionParameter(recordsetName, data)
            return getDataDone, data
        finally:
            self._logDuration(_startTime, description='FieldGroup=%s, field=%s, recordsetName=%s, getDataMethodName=%s'
                              % ('' if fieldGroup is None else fieldGroup.name,
                                 '' if field is None else field.name,
                                 recordsetName, getDataMethodName))

    def _getTableCurrentRecordInfo(self) -> TableCursorInfo:
        '''
            return table cursor data info(resultTable, user click the EditColumn)
        '''
        return TableCursorInfo(self.getLastRequestData())

    def _getFieldGroupData(self, fieldGroupName) -> object:
        return self._fieldGroupData.get(fieldGroupName, None)

    def __updateDataCursor(self, fieldGroup, data) -> None:
        if data is not None and fieldGroup.groupType == ikui.SCREEN_FIELD_TYPE_RESULT_TABLE and fieldGroup.editable:
            cursorInfo = self._getTableCurrentRecordInfo()
            if cursorInfo.fieldGroupName == fieldGroup.name:
                if isinstance(data, Model):
                    data.ik_set_cursor(isCursor=getattr(data, cursorInfo.dataFieldName) == cursorInfo.dataValue)
                elif type(data) == list or isinstance(data, QuerySet):
                    for rc in data:
                        if isinstance(rc, Model):
                            rc.ik_set_cursor(isCursor=getattr(rc, cursorInfo.dataFieldName) == cursorInfo.dataValue)

    def _initScreen(self) -> ikhttp.IkSccJsonResponse:
        '''
            used for react ScreenRender
        '''
        # XH, 2023-12-20 for forward screen - start

        # When jumping to open a new page, save the initial parameters(if any).
        oldSUUID = self.request.GET.get(PARAMETER_KEY_NAME_SCREEN_UUID, None)
        openScreenKey = "%s_%s" % (_OPEN_SCREEN_PARAM_KEY_NAME, oldSUUID)
        openScreenParams = self.getSessionParameter(openScreenKey, delete=True, isGlobal=True)
        if isNotNullBlank(openScreenParams):
            for key, value in openScreenParams.items():
                self.setSessionParameter(key, value)
        # XH, 2023-12-20 - end
        screen = self.getScreen()
        fieldGroupNames = []
        if screen is not None:
            fieldGroupNames = screen.getFieldGroupNames()
        characters = string.ascii_letters + string.digits
        SUUID = ''.join(random.choice(characters) for i in range(20))
        logLevel = IkConfig.get('System', "browserLogLevel")
        return ikhttp.IkSccJsonResponse(data={'fieldGroupNames': fieldGroupNames, PARAMETER_KEY_NAME_SCREEN_UUID: SUUID, 'logLevel': logLevel})

    def getLastTemplateRevisionFile(self, filename=None, category=None, code=None) -> str:
        ''' 
            filename: if filename is None, then try to find the last file named [code].xlsx, then [code]-Template.xlsx file if exists.
            return tempate file. E.g. var/templates/ikyo/GP/GP020/xxxx-v99.xlsx
        '''
        templateFilename = filename
        if templateFilename is None and self._functionCode is not None:
            templateFilename = self._functionCode + "-Template.xlsx"
        f = self.__getLastTemplateRevisionFile(templateFilename, category, code)
        if f is None and filename is None and self._functionCode is not None:
            templateFilename = self._functionCode + ".xlsx"
            f = self.__getLastTemplateRevisionFile(templateFilename, category, code)
        return f

    def __getLastTemplateRevisionFile(self, filename, category=None, code=None) -> str:
        '''
            return tempate file. E.g. var/templates/ikyo/GP/GP020/xxxx-v99.xlsx
        '''
        return self.__getLastTemplateRevisionFile2(filename, rootFolder=self.getTemplateFolderName(), category=category, code=code)

    def getTemplateFolderName(self) -> str:
        '''
            return templates/ikyo
        '''
        return 'templates/ikyo'

    def __getLastTemplateRevisionFile2(self, filename, rootFolder, category=None, code=None) -> str:
        '''
            return tempate file. E.g. var/{rootFolder}/ikyo/GP/GP020/xxxx-v99.xlsx
        '''
        category = self._functionCategory if category is None else category
        code = self._functionCode if code is None else code
        path = rootFolder
        if code is not None and category is None:
            raise IkValidateException('Parameter [category] is mandatory if the [code] is not null.')
        if category is not None:
            path += '/' + str(category)
        if code is not None:
            path += '/' + str(code)
        if category is None and code is None:
            path += '/' + str(self.__class__.__name__)
        templateFile = ikfs.getLastRevisionFile(ikfs.getVarFolder(path), filename)
        return templateFile

    def downloadFile(self, file, filename: str = None) -> HttpResponseBase:
        if file is None:
            msg = 'Download file cannot be empty. Please ask administrator to check.'
            logger.error(msg)
            return ikhttp.IkErrJsonResponse(message=msg)
        elif not Path(file).is_file():
            logger.error('File does not exist: %s' % Path(file).absolute())
            return ikhttp.IkErrJsonResponse(message="File does not exist.")
        else:
            try:
                return ikhttp.responseFile(file, filename=filename)
            except Exception as e:
                return ikhttp.IkErrJsonResponse(message="Download file failed: %s" % str(e))

    def downloadLastTemplateRevisionFile(self, filename, category=None, code=None) -> HttpResponseBase:
        '''
            return StreamingHttpResponse if file exists otherwise return IkErrJsonResponse
        '''
        f = self.getLastTemplateRevisionFile(filename, category, code)
        return self.downloadFile(file=f)

    def getUploadFolder(self, user) -> str:
        '''
            return var/upload/00001/GP/GP020/username/2022/08/02/093651543
        '''
        return ikfs.getVarFolder('upload/%s/%s/%s' %
                                 ('NA' if self._functionCategory is None else self._functionCategory,
                                  'NA' if self._functionCode is None else self._functionCode, user.usr_nm),
                                 withTimeStampFolders=True)

    def downloadExampleFn(self, filename) -> ikhttp.IkJsonResponse:
        try:
            templateFile = self.getLastTemplateRevisionFile(filename)
            if not pathlib.Path(templateFile).is_file():
                return ikhttp.IkSysErrJsonResponse(message='Example file [%s] does not exist. Please ask administrator to check.' % filename)
            return self.downloadFile(file=templateFile)
        except IkException as pe:
            traceback.print_exc()
            return ikhttp.IkErrJsonResponse(message=str(pe))
        except Exception as e:
            traceback.print_exc()
            return ikhttp.IkSysErrJsonResponse(message=str(e))

    def getUploadSpreadsheetFile(self, parameterName, savePath) -> tuple:
        '''
            return (clientSideFilename, uploadFile)
        '''
        if isNullBlank(savePath):
            raise IkValidateException('Parameter "savePath" is mandatory.')
        uploadFile = self.getRequestData().getFile(parameterName)
        if uploadFile is None:
            raise IkValidateException('Please select a spreadsheet file to upload.')
        fileExtension = pathlib.Path(uploadFile.name).suffix  # YL.ikyo, 2022-07-18 bug fix
        if fileExtension is None or (fileExtension.lower() != '.xlsx'
                                     and fileExtension.lower() != '.xls' and fileExtension.lower() != '.xlsm'):
            raise IkValidateException('Only supports xls, xlsx and xlsm types.')
        # save file to temp folder
        ikfs.mkdirs(savePath)
        # save
        savedFile = ikfs.getFileWithTimestamp(os.path.join(savePath, pathlib.Path(uploadFile.name)))  # YL.ikyo, 2022-07-18 bug fix
        f = open(savedFile, 'wb')
        for chunk in uploadFile.chunks():
            f.write(chunk)
        f.close()
        return uploadFile.name, savedFile

    def getUploadSpreadsheet(self, parameterName, savePath=None, tableNames=None) -> tuple:
        '''
            return (clientSideFilename, uploadFile, SpreadsheetParser)
        '''
        if savePath is None:
            savePath = self.getUploadFolder(self.getCurrentUser())
        clientSideFilename, uploadFile = self.getUploadSpreadsheetFile(parameterName, savePath)
        # read spreadsheet
        sp = spreadsheet.SpreadsheetParser(uploadFile, tableNames=tableNames)
        return clientSideFilename, uploadFile, sp

    def getRequestAction(self, **kwargs) -> str:
        return kwargs.get(REQUEST_PRM_ACTION, '')

    def __init_subclass__(cls) -> None:
        return super().__init_subclass__()

    def get(self, request, *args, **kwargs):
        return self.__proecessRequest('get', *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.__proecessRequest('post', *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.__proecessRequest('delete', *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.__proecessRequest('put', *args, **kwargs)

    def __proecessRequest(self, httpMethod, *args, **kwargs):
        _startTime = datetime.datetime.now()
        r = None
        try:
            r = self.__proecessRequest__(httpMethod, *args, **kwargs)
            if isinstance(r, Boolean2):
                r = r.toIkJsonResponse1()
            if not isinstance(r, HttpResponseBase) and not isinstance(r, StreamingHttpResponse):
                # StreamingHttpResponse: download file
                r = ikhttp.IkSccJsonResponse(data=r)
            isUpdateContent = False
            if self._messages is not None and len(self._messages) > 0 \
                    and r is not None and isinstance(r, ikhttp.IkJsonResponse):
                for msgItem in self._messages:
                    if type(msgItem) == list:  # self message
                        r.addMessage(msgItem[0], msgItem[1])
                    elif type(msgItem) == dict:  # IkJsonResponse message
                        r.addMessage(msgItem['type'], msgItem['message'])
                isUpdateContent = True
            if self._staticResources is not None and len(self._staticResources) > 0 \
                    and r is not None and isinstance(r, ikhttp.IkJsonResponse):
                for s in self._staticResources:
                    r.addStaticResource(s)
                isUpdateContent = True
            if isUpdateContent:
                r.updateContent()
        finally:
            try:
                self._freeRequestResource()
            except Exception as e:
                logger.error(e, exc_info=True)
            self._logDuration(_startTime)
        return r

    def __proecessRequest__(self, httpMethod, *args, **kwargs):
        '''
            call get action
        '''
        _startTime = datetime.datetime.now()
        _loggerDesc = None

        self._httpMethod = httpMethod
        className = self.__class__.__name__
        try:
            if not self.__permissionCheck():
                _loggerDesc = 'Permission Deny'
                return ikhttp.IkErrJsonResponse(message='Permission Deny')

            if self._screen is None:
                _getScreenStartTime = datetime.datetime.now()

                parsedUrl = urlparse(self.request.get_full_path())
                queryParams = parse_qs(parsedUrl.query)
                subScreenNm = queryParams.get(PARAMETER_KEY_NAME_SUB_SCREEN_NAME, [None])[0]

                self._screen = MenuManager.getScreen2(self.request, self, menuName=self._menuName, subScreenNm=subScreenNm)
                self._logDuration(_getScreenStartTime, description='MenuManager.getScreen2, menuName=%s, screen=%s'
                                  % (self._menuName, None if self._screen is None else self._screen.id))
            #_getRequestDataStartTime = datetime.datetime.now()
            self._requestData = self._getRequestData()
            self._logDuration(_getScreenStartTime, description='_getRequestData, screen=%s' % (None if self._screen is None else self._screen.id))
            self._lastRequestData = self.getSessionParameter(PARAMETER_KEY_NAME_LAST_REQUEST_DATA, default=None)
            action = self.getRequestAction(**kwargs)  # E.g. userFg_EditIndexField_Click
            _loggerDesc = action
            self._requestAction = action
            if not isNullBlank(action):
                getDataFlag = kwargs.get(ikui.GET_DATA_URL_FLAG_PARAMETER_NAME, None)  # TODO: error, need to check and test
                if not isNullBlank(getDataFlag):
                    self._isGetDataRequest = True
            # get uuid from request data or url
            suuid = self.getRequestData().get(PARAMETER_KEY_NAME_SCREEN_UUID, None)
            if suuid is None:
                # parsedUrl = urlparse(self.request.get_full_path())
                # queryParams = parse_qs(parsedUrl.query)
                suuid = queryParams.get(PARAMETER_KEY_NAME_SCREEN_UUID, [None])[0]
            self._SUUID = suuid
            self._viewUUID = suuid
            # get uuid end
            logger.debug('%s process %s action:[%s] suuid=[%s]' % (className, httpMethod, action, suuid))

            additionalRequestParameters = {}
            # check the edit button function for result table - start
            isResultTableClickColumnDefaultEvent = False
            if not isNullBlank(action):
                screen = self.getScreen()
                for resultTable in screen.getFieldGroupsByTypes(types=[ikui.SCREEN_FIELD_TYPE_RESULT_TABLE]):
                    field = resultTable.getResultTableEditColumnField()
                    if field is not None and field.editable:
                        if action == field.getEventHandlerName():
                            isResultTableClickColumnDefaultEvent = True
                            value = self.getRequestData().get(ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME, None)
                            if value is not None:
                                additionalRequestParameters[PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_NAME] = field.parent.name
                                additionalRequestParameters[PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_NAME] = field.name
                                additionalRequestParameters[PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_DATA_NAME] = field.dataField
                                additionalRequestParameters[PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_NAME] = value
                            self.setSessionParameter(field.name, value)
                            break

            # YL.ikyo, 2023-05-08 for forward screen - start
            # delete session data before save request data
            if httpMethod == 'get' and action == REQUEST_SYSTEM_ACTION_INIT_SCREEN and (isNullBlank(subScreenNm) or subScreenNm == ikui.MAIN_SCREEN_NAME):
                # delete the old session parameters
                self.cleanSessionParameters()
            # YL.ikyo, 2023-05-08 - end

            # check the edit button function for result table - end
            self._saveRequestData(additionParameterDict=additionalRequestParameters)

            if action != REQUEST_SYSTEM_ACTION_GET_SCREEN and action != REQUEST_SYSTEM_ACTION_LOAD_SCREEN_COMPLETED:
                self._addAccessLog(self.request, menuID=self._menuID, pageName=className, actionName=action, remarks='%s' % httpMethod)
            if action is not None and len(action) > 0 and action[0] == '_':
                return ikhttp.IkErrJsonResponse(message='%s process %s action:[%s]: permission deny.' % (className, httpMethod, action))
            if httpMethod == 'get' and action == REQUEST_SYSTEM_ACTION_INIT_SCREEN:
                _initScreenStartTime = datetime.datetime.now()
                try:
                    return self._initScreen()
                finally:
                    self._logDuration(_initScreenStartTime, description='_initScreen screen=%s' % (None if self._screen is None else self._screen.id))
            elif httpMethod == 'get' and action == REQUEST_SYSTEM_ACTION_GET_SCREEN:
                return self._getScreenResponse()
            elif httpMethod == 'post' and action == REQUEST_SYSTEM_ACTION_UNLOADED_SCREEN:
                self.cleanSessionParameters()
                return ikhttp.IkSccJsonResponse()
            elif httpMethod == 'post' and action == REQUEST_SYSTEM_ACTION_LOAD_SCREEN_COMPLETED:
                return self._afterLoadScreenCompleted()
            else:
                actionFn = None
                # format:
                # fieldGroupName%action
                # e.g.
                # 1) save
                # 2) %save
                #    save as 1)
                # 3) fieldGroup1%save
                #    this is system defined method
                #
                actionPrms = action.split('$')
                actionFnName = actionPrms[-1]
                callViewFn = False
                try:
                    actionFn = getattr(self, actionFnName)
                    if len(inspect.getfullargspec(actionFn).args) > 1:
                        raise AttributeError('Function is not found: %s' % actionFnName)  # the action function only has one parameter - "self"
                    callViewFn = True
                except AttributeError as ae:
                    if not isResultTableClickColumnDefaultEvent:
                        if len(actionPrms) != 1 and len(actionPrms) != 2:
                            logger.error('%s process %s action:[%s] - function is not found', className, httpMethod, actionFnName)
                            return ikhttp.IkErrJsonResponse(message='%s process %s action:[%s]: function is not found' % (className, httpMethod, action))
                        elif len(actionPrms) == 2:
                            # system default method
                            logger.debug('%s process %s action:[%s] - function is not found, then try system build-in function...', className, httpMethod, action)
                            return self._processBuildInFunction(actionPrms[0], actionPrms[1])
                if callViewFn:
                    if actionFn is None and isResultTableClickColumnDefaultEvent:
                        # this method is optional for user's controller
                        return ikhttp.IkSccJsonResponse()
                    _callActionFnStartTime = datetime.datetime.now()
                    try:
                        return actionFn()
                    finally:
                        self._logDuration(_callActionFnStartTime, actionName=actionFnName, description='Screen=%s' % (None if self._screen is None else self._screen.id))
        except DatabaseError as e:
            logger.error(e, exc_info=True)
            msg = str(e)
            if type(e) == ProgrammingError or type(e) == DataError:
                msg = str(e).split('\n')[0]
            elif 'DETAIL: ' in msg:  # e.g. IntegrityError
                msg = msg[msg.index('DETAIL: '):-1]
            msgTitle = ''
            if type(e) == ProgrammingError:
                msgTitle = 'System error.'
            elif type(e) == IntegrityError or type(e) == DataError:
                msgTitle = 'Save data failed.'
            else:
                msgTitle = 'Data error.'
            return ikhttp.IkErrJsonResponse(message='%s. %s' % (msgTitle, msg))
        except IkMessageException as e:
            logger.error(e, exc_info=True)
            return ikhttp.IkErrJsonResponse(message=str(e))
        except Exception as e:
            logger.error(e, exc_info=True)
            return ikhttp.IkErrJsonResponse(message='System error. Please ask administrator to check.')
        finally:
            self._logDuration(_startTime, description=_loggerDesc)

    def isGetDataRequest(self, action, recordsetName) -> bool:
        ''' 
            action: client request action. E.g. get + recordSetName[0].upper() + recordSetName[1:]
            TODO: validate recordset from screen
        '''
        if action is None or len(action) < 4:
            return False
        return action == ('get' + recordsetName[0].upper() + recordsetName[1:])

    def __permissionCheck(self) -> bool:
        return True  # TODO:

    def _freeRequestResource(self) -> None:
        '''
            call this method after get/post/delete/put method 
        '''
        self._messages.clear()
        self._staticResources.clear()

    def getRequestData(self) -> ikhttp.IkRequestData:
        return self._requestData

    def _getRequestValue(self, name: str, fgName: str = None, default: any = None) -> any:
        if fgName is None:
            return self._requestData.get(name, default)
        fg = self._requestData.get(fgName)
        return None if fg is None else fg.get(name, default)

    def _getRequestValueAsDate(self, name: str, fgName: str = None, default: datetime.date = None, format="%Y-%m-%d") -> datetime.date:
        value = self._getRequestValue(name, fgName, default)
        if isNullBlank(value):
            return None
        elif isinstance(value, datetime.date):
            return value
        return datetime.datetime.strptime(str(value), format).date()

    def _getRequestValueAsTime(self, name: str, fgName: str = None, default: datetime.date = None, format="%H:%M:%S") -> datetime.time:
        value = self._getRequestValue(name, fgName, default)
        if isNullBlank(value):
            return None
        elif isinstance(value, datetime.time):
            return value
        return datetime.datetime.strptime(str(value), format).time()

    def _getRequestValueAsDatetime(self, name: str, fgName: str = None, default: datetime.date = None, format="%Y-%m-%d %H:%M:%S") -> datetime.datetime:
        value = self._getRequestValue(name, fgName, default)
        if isNullBlank(value):
            return None
        elif isinstance(value, datetime.datetime):
            return value
        return datetime.datetime.strptime(str(value), format)

    def _getRequestData(self) -> ikhttp.IkRequestData:
        '''
            2022-08-30, still in developing .... (Li)
        '''
        screen = self.getScreen()
        screenTableGroupNames = []
        screenFieldsGroupNames = []
        parameterModelMap = {}
        if screen is None:
            raise IkException('Screen[%s] is null, please ask administrator to check.' % self.getMenuName())
        for fg in screen.fieldGroups:
            if fg.isTable():
                screenTableGroupNames.append(fg.name)
                if not isNullBlank(screen.getRecordset(fg.recordSetName)) \
                    and not isNullBlank(screen.getRecordset(fg.recordSetName).modelNames):
                    parameterModelMap[fg.name] = screen.getRecordset(fg.recordSetName).modelNames
            elif fg.isDetail():
                screenFieldsGroupNames.append(fg.name)
                if not isNullBlank(fg.recordSetName) \
                    and not isNullBlank(screen.getRecordset(fg.recordSetName)) \
                    and not isNullBlank(screen.getRecordset(fg.recordSetName).modelNames):
                    parameterModelMap[fg.name] = screen.getRecordset(fg.recordSetName).modelNames
        for _fgName, recordName in parameterModelMap.items():
            if recordName is not None and ',' in recordName:
                raise IkValidateException('Unsupport more than on model: %s' % recordName)

        requestData = ikhttp.GetRequestData(self.request, parameterModelMap=parameterModelMap, screen=screen)
        return requestData

    def _saveRequestData(self, additionParameterDict=None):
        data = self.getRequestData()
        if not data:
            return
        jData = {}
        for key, value in additionParameterDict.items():
            jData[key] = value
        for name, value in data.items():
            t = type(value)
            if t == str or t == int or t == float or t == None:
                jData[name] = value
        self.setSessionParameter(PARAMETER_KEY_NAME_LAST_REQUEST_DATA, jData)

    def getLastRequestData(self) -> dict:
        return {} if self._requestData is None else self._lastRequestData

    def getLastRequestDataAsInt(self, name) -> int:
        v = self.getLastRequestData().get(name, None)
        return None if isNullBlank(v) else int(v)

    def __updateSessionParameters(self, parameterNames=None) -> bool:
        '''
            parameterNames means all. Types (str (parameter name), list (parameter names), dict (prameter name, parameter value))
        '''
        if parameterNames is not None and type(parameterNames) == dict:
            for key, value in parameterNames.items():
                self.setSessionParameter(key, value)
            return True
        if parameterNames is not None:
            if type(parameterNames) == list and len(parameterNames) == 0:
                return True
            if type(parameterNames) == str:
                parameterNames = [parameterNames]
        data = self.getRequestData()
        foundNames = []
        for name, value in data.items():
            if parameterNames is not None and name not in parameterNames:
                continue
            self.setSessionParameter(name, value)
            if parameterNames is not None and name not in foundNames:
                foundNames.append(name)
        return parameterNames is None or len(parameterNames) == len(foundNames)

    def readWebTemplateFile(self, filename) -> str:
        '''
            return file content with \n
        '''
        rootFolder = 'webTemplates'
        templateFilename = filename
        f = self.__getLastTemplateRevisionFile2(templateFilename, rootFolder)
        if f is None or not pathlib.Path(f).is_file():
            raise IkException('Web template file [%s] does not exist. Please ask administrator to check.' % filename)
        content = None
        with open(f, newline='', encoding='utf-8') as f:
            content = f.read()
        return content

    def _afterLoadScreenCompleted(self) -> ikhttp.IkJsonResponse:
        if self._isCleanSessionDataWhenScreenLoadCompleted():
            self.cleanSessionParameters()
        return ikhttp.IkSccJsonResponse()

    def _isCleanSessionDataWhenScreenLoadCompleted(self) -> bool:
        return False

    def _addDebugMessage(self, message) -> None:
        self._messages.append([MessageType.DEBUG, message])

    def _addInfoMessage(self, message) -> None:
        self._messages.append([MessageType.INFO, message])

    def _addWarnMessage(self, message) -> None:
        self._messages.append([MessageType.WARNING, message])

    def _addErrorMessage(self, message) -> None:
        self._messages.append([MessageType.ERROR, message])

    def _addFatalMessage(self, message) -> None:
        self._messages.append([MessageType.FATAL, message])

    def _addExceptionMessage(self, message) -> None:
        self._messages.append([MessageType.EXCEPTION, message])

    def _addMessages(self, messages) -> None:
        if messages is not None:
            if type(messages) != list:
                raise IkException('Parameter [messages] should be a list.')
            self._messages.extend(messages)

    def _getMessageCount(self, messageType: MessageType = None) -> int:
        if not messageType:
            return len(self._messages)
        c = 0
        for mt, _msg in self._messages:
            if mt == messageType:
                c += 1
        return c

    def _getMessageDebugCount(self) -> int:
        return self._getMessageCount(messageType=MessageType.DEBUG)

    def _getMessageInfoCount(self) -> int:
        return self._getMessageCount(messageType=MessageType.INFO)

    def _getMessageErrorCount(self) -> int:
        return self._getMessageCount(messageType=MessageType.ERROR)

    def _getMessageFatalCount(self) -> int:
        return self._getMessageCount(messageType=MessageType.FATAL)

    def _getMessageExceptionCount(self) -> int:
        return self._getMessageCount(messageType=MessageType.EXCEPTION)

    def _addStaticResource(self, resource, properties=None) -> ikhttp.IkResponseStaticResource:
        r = ikhttp.IkResponseStaticResource(resource=resource, properties=properties)
        self._staticResources.append(r)
        return r

    def _returnQueryResult(self, name, data, style=None, message=None) -> ikhttp.IkSccJsonResponse:
        '''
            Used for Search Field Group
            name: screen field group's name (str)
            data: screen field group's data E.g. query results (list)
            style: screen field group's data style (list | None)
            message: return message (str | None)
            return IkSccJsonResponse 
        '''
        return self._returnQueryResults({name: data}, {name: style if not isNullBlank(style) else []}, message)

    def _returnQueryResults(self, resultDict, styleDict=None, message=None) -> ikhttp.IkSccJsonResponse:
        '''
            Used for Search Field Group
            resultDict: dict. E.g. {fg name: fg data(list)}
            styleDict: dict. E.g. {fg name: fg data style(list)}
            return IkSccJsonResponse 
        '''
        data = {}
        if resultDict is not None:
            for key, value in resultDict.items():
                style = styleDict[key] if not isNullBlank(styleDict) and key in styleDict else []
                data[key] = {'fgData': value, 'fgDataStyle': style}
        return ikhttp.IkSccJsonResponse(data=data, message=message)

    def _returnComboboxQueryResult(self, fgName, fgData, resultDict: dict, message=None) -> ikhttp.IkSccJsonResponse:
        '''
            Used for Search Field Group or Simple Field Group
            fgName: fg name
            fgData: fg data (list)
            resultDict: dict. E.g. {fg field name: fg field data}
            message: message (str)
            return IkSccJsonResponse 
        '''
        resultDict[fgName] = fgData
        return ikhttp.IkSccJsonResponse(data={fgName: resultDict}, message=message)

    def saveUploadFile(self, uploadFile, saveFilePath):
        '''
            if the parent folder does not exist, then create it
        '''
        ikfs.mkdirs(Path(saveFilePath).parent)
        f = open(saveFilePath, 'wb')
        for chunk in uploadFile.chunks():
            f.write(chunk)
        f.close()

    def _openScreen(self, menuName, parameters=None) -> ikhttp.IkSccJsonResponse:
        '''
            menuName (str): Screen SN
            parameters (dict): parameter(s)
        '''
        rspData = {_OPEN_SCREEN_KEY_NAME: menuName}
        if parameters is not None:
            self.setSessionParameter(name="%s_%s" % (_OPEN_SCREEN_PARAM_KEY_NAME, self._viewUUID), value=parameters, isGlobal=True)
        return ikhttp.IkSccJsonResponse(data=rspData)

    def convert2DummyModelRcs(self, dataList, initStatus=None) -> list:
        '''
            This is used to prepare "dummy" recordset data.

            dataList: a dict list. E.g. [{'name1': value1...}, {...} ...]
            initStatus: backend.core.model.ModelRecordStatus
        '''
        if dataList is None:
            return None
        rcs = []
        for r in dataList:
            rcs.append(DummyModel(values=r, status=initStatus))
        return rcs

    def convertDummyModelRcs2List(self, dummyModelRcs, ignoreNames=None) -> list:
        data = []
        for r in dummyModelRcs:
            r2 = []
            for k, v in r.items():
                if ignoreNames is not None and k in ignoreNames:
                    continue
                r2.append(v)
            data.append(r2)
        return data

    def __getRecordSetData(self, fieldGroup, field, recordsetName) -> object:
        if fieldGroup.isDetail() or fieldGroup.isTable():
            # if the field group is a detail field group, then check the link fields
            fgl = fieldGroup.parent.getFieldGroupLink(fieldGroup.name)
            if fgl is not None:
                mastTableRcs = self.getSessionParameter(fgl.parentFieldGroup.recordSetName)
                if fieldGroup.recordSetName == fgl.parentFieldGroup.recordSetName:
                    # use the same recordset for master-detail table
                    if fieldGroup.isDetail():
                        mastTableCursor = self.__getDataCursor(mastTableRcs)
                        return mastTableCursor
                    else:
                        return rcs
                if mastTableRcs is not None:
                    # get cursor
                    mastTableCursor = self.__getDataCursor(mastTableRcs)
                    if mastTableCursor is not None:
                        mastKeyValue = mastTableCursor.get(fgl.parentKey) \
                            if type(mastTableCursor) == dict \
                            else getattr(mastTableCursor, fgl.parentKey)
                        if mastKeyValue is not None:
                            rcs = self.__getRecordSetData4DetailFieldGroup(fieldGroup, fgl.localKey, mastKeyValue)
                            if fieldGroup.isDetail():
                                rc = None if len(rcs) == 0 else rcs[0]
                                if rc is not None:
                                    rc.ik_set_cursor(isCursor=True)  # used for master-detail field groups using link table.
                                return rc
                            else:
                                return rcs
                return None

        rcs = None if recordsetName is None else ikui.IkUI._getRecordSetData(fieldGroup, field, recordsetName)
        if rcs is not None:
            currentRecordID = self._getTableDataIndex(fieldGroup.name)
            if not isNullBlank(currentRecordID):
                modelUtils.locateToFirstByID(rcs, int(currentRecordID))
        if field is None and fieldGroup.isDetail():
            return rcs[0] if len(rcs) > 0 else None
        return rcs

    def __getRecordSetData4DetailFieldGroup(self, fieldGroup, keyField, value) -> dict:
        screen = fieldGroup.parent
        recordset = screen.getRecordSet(fieldGroup.recordSetName)
        recordSetWhere = recordset.queryWhere
        if recordSetWhere is None:
            recordSetWhere = ''
        else:
            recordSetWhere += ' AND '
        recordSetWhere += "%s='%s'" % (keyField, 'none' if value is None else (value.replace("'", "''") if type(value) == str else value))
        return modelUtils.queryModel(modelNames=recordset.modelNames,
                                     distinct=recordset.distinct,
                                     queryFields=None if (isNullBlank(recordset.queryFields) or recordset.queryFields == '*') else recordset.queryFields,
                                     queryWhere=recordSetWhere,
                                     orderBy=recordset.queryOrder,
                                     limit=recordset.queryLimit,
                                     page=None)

    def __getDataCursor(self, mastTableRcs) -> dict:
        mastTableCursor = None
        if type(mastTableRcs) == list:
            for rc in mastTableRcs:
                if self.__isCursorRecord(rc):
                    mastTableCursor = rc
                    break
        else:
            if self.__isCursorRecord(mastTableRcs):
                mastTableCursor = mastTableRcs
        return mastTableCursor

    def __isCursorRecord(self, rc) -> bool:
        isCursor = False
        try:
            isCursor = rc.ik_is_cursor()
        except:
            from core.db.model import MODEL_RECORD_DATA_CURRENT_KEY_NAME
            if type(rc) == dict:
                isCursor = rc.get(MODEL_RECORD_DATA_CURRENT_KEY_NAME, False)
        return isCursor

    def _processBuildInFunction(self, fieldGropName, functionName) -> ikhttp.IkJsonResponse:
        '''
            cancel/delete/save/new
        '''
        if functionName == 'new':
            return self._BIFNew(fieldGropName)
        elif functionName == 'cancel':
            return self._BIFCancel(fieldGropName)
        elif functionName == 'delete':
            return self._BIFDelete(fieldGropName)
        elif functionName == 'save':
            return self._BIFSave(fieldGropName)
        else:
            return ikhttp.IkErrJsonResponse(message='Unsupport system function [%s].' % functionName)

    def _BIFNew(self, fieldGropName) -> ikhttp.IkJsonResponse:
        '''
            build-in function: new
        '''
        if isNullBlank(fieldGropName):
            return ikhttp.IkErrJsonResponse(message='Fieldgroup Name is mandatory for build-in function [new].')
        screen = self._screen
        fg = screen.getFieldGroup(fieldGropName)
        if fg is None:
            return ikhttp.IkErrJsonResponse(message='Fieldgroup [%s] is not found for build-in function [new].' % fieldGropName)
        if isNullBlank(fg.recordSetName):
            return ikhttp.IkErrJsonResponse(message='RecordSet is not found for field group [%s] for build-in function [new].' % fieldGropName)
        self._setTableDataIndex(fg.name, 0)  # id = 0
        return ikhttp.IkSccJsonResponse()

    def _BIFCancel(self, fieldGropName) -> ikhttp.IkJsonResponse:
        '''
            build-in function: cancel
        '''
        if isNullBlank(fieldGropName):
            return ikhttp.IkErrJsonResponse(message='Fieldgroup Name is mandatory for build-in function [new].')
        screen = self._screen
        fg = screen.getFieldGroup(fieldGropName)
        if fg is None:
            return ikhttp.IkErrJsonResponse(message='Fieldgroup [%s] is not found for build-in function [new].' % fieldGropName)
        if isNullBlank(fg.recordSetName):
            return ikhttp.IkErrJsonResponse(message='RecordSet is not found for field group [%s] for build-in function [new].' % fieldGropName)
        self._removeTableDataIndex(fg.name)
        return ikhttp.IkSccJsonResponse()

    def _BIFDelete(self, __fieldGropName) -> ikhttp.IkJsonResponse:
        '''
            build-in function: delete
        '''
        # 1. get editable field groups
        fgTableNames = []
        fgDetailNames = []
        for fg in self._screen.fieldGroups:
            if fg.visible:
                if fg.groupType == ikui.SCREEN_FIELD_TYPE_TABLE:
                    fgTableNames.append(fg.name)
                elif fg.groupType == ikui.SCREEN_FIELD_TYPE_FIELDS:
                    fgDetailNames.append(fg.name)
        if len(fgTableNames) == 0 and len(fgDetailNames) == 0:
            return ikhttp.IkErrJsonResponse("No data saved (1).")
        # 2. get paramteres
        reqData = self.getRequestData()
        tableDataList = {}
        detailDataList = {}
        for fgName in fgTableNames:
            rcs = reqData.get(fgName)
            if rcs is not None:
                tableDataList[fgName] = rcs
        for fgName in fgDetailNames:
            rcs = reqData.get(fgName)
            if rcs is not None:
                detailDataList[fgName] = rcs
        if len(tableDataList) == 0 and len(detailDataList) == 0:
            return ikhttp.IkErrJsonResponse("No data saved (2).")
        # 3. save
        trn = IkTransaction()
        # a) save master field groups
        for name, rcs in tableDataList.items():
            trn.delete(rcs)
        for name, rcs in detailDataList.items():
            trn.delete(rcs)
        b = trn.save()
        if b.value:
            # update the master table's current record id if exists (locate to its current record)
            for fgName, rc in detailDataList.items():
                fgl = self._screen.getFieldGroupLink(fgName)
                if fgl is not None:
                    self._removeTableDataIndex(fgl.parentFieldGroup.name)
        return b

    def _BIFSave(self, __fieldGropName) -> ikhttp.IkJsonResponse:
        '''
            build-in function: save
        '''
        # 1. get editable field groups
        fgTableNames = []
        fgDetailNames = []
        for fg in self._screen.fieldGroups:
            if fg.editable and fg.visible:
                if fg.groupType == ikui.SCREEN_FIELD_TYPE_TABLE:
                    fgTableNames.append(fg.name)
                elif fg.groupType == ikui.SCREEN_FIELD_TYPE_FIELDS:
                    fgDetailNames.append(fg.name)
        if len(fgTableNames) == 0 and len(fgDetailNames) == 0:
            return ikhttp.IkErrJsonResponse("No data saved (1).")
        # 2. get paramteres
        reqData = self.getRequestData()
        tableDataList = {}
        detailDataList = {}
        for fgName in fgTableNames:
            rcs = reqData.get(fgName)
            if rcs is not None:
                tableDataList[fgName] = rcs
        for fgName in fgDetailNames:
            rcs = reqData.get(fgName)
            if rcs is not None:
                detailDataList[fgName] = rcs
        if len(tableDataList) == 0 and len(detailDataList) == 0:
            return ikhttp.IkErrJsonResponse("No data saved (2).")
        # 3. get table links
        masterFieldGroupNameDict = {}
        for fgName in tableDataList.keys():
            fgl = self._screen.getFieldGroupLink(fgName)
            if fgl is not None:
                if fgl.parentFieldGroup.name in tableDataList.keys() or fgl.parentFieldGroup.name in detailDataList.keys():
                    masterFieldGroupNameDict[fgName] = fgl
        for fgName in detailDataList.keys():
            fgl = self._screen.getFieldGroupLink(fgName)
            if fgl is not None:
                if fgl.parentFieldGroup.name in tableDataList.keys() or fgl.parentFieldGroup.name in detailDataList.keys():
                    if fgl.parentFieldGroup.name in masterFieldGroupNameDict.keys():
                        return ikhttp.IkErrJsonResponse(
                            "Field group [%s] cannot have more then one parent field group should be in the same data post from browser. Please check field group [%s]." %
                            (fgName, fgl.fieldGroup.name))
                    masterFieldGroupNameDict[fgName] = fgl
        # 4. save
        trn = IkTransaction()
        # a) save master field groups
        for name, rcs in tableDataList.items():
            if name not in masterFieldGroupNameDict.keys():
                trn.add(rcs)
        for name, rcs in detailDataList.items():
            if name not in masterFieldGroupNameDict.keys():
                trn.add(rcs)
        # b) save slave field groups
        for name, rcs in tableDataList.items():
            if name in masterFieldGroupNameDict.keys():
                fgl = masterFieldGroupNameDict.get(name)
                # get master data
                for name, rcs in tableDataList.items():
                    if name == fgl.parentFieldGroup.name:
                        # get current record
                        masterRc = self.__getDataCursor(rcs)
                        if masterRc is not None:
                            trn.add(rcs, foreignKeys=IkTransactionForeignKey(modelFieldName=fgl.localKey, foreignModelRecord=masterRc, foreignField=fgl.parentKey))
                        break
                for name, rc in detailDataList.items():
                    if name == fgl.parentFieldGroup.name:
                        trn.add(rcs, foreignKeys=IkTransactionForeignKey(modelFieldName=fgl.localKey, foreignModelRecord=rc, foreignField=fgl.parentKey))
                        break
        b = trn.save()
        if b.value:
            # update the master table's current record id if exists (locate to its current record)
            for fgName, rc in detailDataList.items():
                fgl = self._screen.getFieldGroupLink(fgName)
                if fgl is not None:
                    keyValue = None
                    if rc is not None:
                        keyValue = getattr(rc, fgl.localKey)
                    self._setTableDataIndex(fgl.parentFieldGroup.name, keyValue)
        return b

    def save1(self):
        '''
            Save author and books table.
        '''
        # 1. get post data
        reqData = self.getRequestData()
        authorRc = reqData.get('authorDetailFg')
        if authorRc is None:
            return ikhttp.IkErrJsonResponse(message='Please select an author first.')
        bookRcs = reqData.get('booksFg')

        # 2. check the author is new or not
        isSaveNewAuthor = authorRc.ik_is_status_new()
        if isSaveNewAuthor:
            authorRc.assignPrimaryID()

        # 3. save
        trn = IkTransaction(caller=self)
        trn.add(authorRc)
        trn.add(bookRcs, foreignKeys={'author': authorRc})
        b = trn.save()
        if b.value:
            self._setTableDataIndex('authorFg', authorRc.id)
        return b

    # YL.ikyo, 2023-06-06 for table pagination - start
    def _getPaginatorPageSize(self, tableName: str) -> int:
        screen = self._screen
        if screen.getFieldGroup(tableName) is None:
            logger.error('Field group: %s does not exist.' % tableName)
            raise IkValidateException('Field group: %s does not exist.' % tableName)
        if isNullBlank(screen.getFieldGroup(tableName).pageSize):
            logger.error('Page size does not exist. tableName=%s' % tableName)
            raise IkValidateException('Page size does not exist. tableName=%s' % tableName)
        return int(screen.getFieldGroup(tableName).pageSize)

    def _getPaginatorPageNumber(self, tableName: str) -> int:
        prmName = "PAGEABLE_%s_pageNum" % tableName
        pageNumStr = self.getRequestData().get(prmName)
        if isNullBlank(pageNumStr):
            logger.error('Page number does not exist. tableName=%s' % tableName)
            raise IkValidateException('Page number does not exist. tableName=%s' % tableName)
        return int(pageNumStr)

    def _getPaginatorTableDataAmount(self, sql: str) -> int:
        amount = 0
        try:
            if isNullBlank(sql):
                return amount
            # delete order by part
            # Parse the query statement
            parsed = sqlparse.parse(sql)
            # Iterate through each statement in the parsed results
            for statement in parsed:
                # Locate the ORDER BY clause
                order_by_clause = None
                for token in statement.tokens:
                    if isinstance(token, sqlparse.sql.Token) and token.value.upper() == "ORDER BY":
                        order_by_clause = token
                        break
                if order_by_clause:
                    # Remove the ORDER BY clause and everything that follows it from the statement
                    index = statement.tokens.index(order_by_clause)
                    del statement.tokens[index:]
            # Reconstruct the query statement
            parsedSql = str(parsed[0])
            fromIndex = parsedSql.upper().index("FROM")
            tmpSql = parsedSql[fromIndex:]
            parsedSql = "SELECT COUNT(*) %s" % tmpSql
            with connection.cursor() as cursor:
                cursor.execute(parsedSql)
                data = dbUtils.dictfetchall(cursor)
                if not dbUtils.isEmpty(data):
                    amount = data[0]['count']
            return amount
        except Exception as e:
            logger.error(e, exc_info=True)
            traceback.print_exc()
            raise IkException("Get sql amount failed.")

    def _getPaginatorTableData(self, sql: str, pageNum=None, pageSize=None) -> list:
        data = None
        if isNullBlank(sql):
            return data
        if isNotNullBlank(pageNum) and pageNum != 0:
            sql += " LIMIT %s" % pageSize
            if isNotNullBlank(pageSize):
                sql += " OFFSET %s" % (pageSize * (pageNum - 1))
        with connection.cursor() as cursor:
            cursor.execute(sql)
            data = dbUtils.dictfetchall(cursor)
        return data

    # YL.ikyo, 2023-06-06 for table pagination - end
    def _addAccessLog(self, request, menuID: int, pageName: str, actionName: str = None, remarks: str =None) -> None:
        """Add screen access log.

        Args:
            request: Django request.
            menuID (int): Menu ID.
            pageName (str): Django view class name.
            actionName (str, optional): Action name. It should be a method name defined in django view class.
            remarks (str, optional): Remarks.
        """    
        addAccessLog(request, menuID, pageName, actionName, remarks)


def getCurrentView() -> ScreenAPIView:
    '''
        return django_backend.core.view.screenView.ScreenAPIView
    '''
    screenView = None
    stacks = inspect.stack()
    for stack in stacks:
        caller = stack.frame.f_locals.get('self', None)
        if caller is not None:
            if isinstance(caller, ScreenAPIView):
                screenView = caller
                break
            elif isinstance(caller, WSGIHandler):
                break
    if screenView is None:
        raise IkException('Unsupport session caller.')
    return screenView
