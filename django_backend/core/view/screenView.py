import datetime
import inspect
import json
import logging
import os
import pathlib
import random
import re
import string
import traceback
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import sqlparse
from django.core.handlers.wsgi import WSGIHandler
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Model
from django.db.models.query import QuerySet
from django.db.utils import (DatabaseError, DataError, IntegrityError,
                             ProgrammingError)
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
from core.core.exception import (IkException, IkMessageException,
                                 IkValidateException)
from core.core.lang import Boolean2
from core.db.model import DummyModel, Model
from core.db.transaction import IkTransaction, IkTransactionForeignKey
from core.menu.menuManager import MenuManager
from core.sys.accessLog import addAccessLog
from core.utils import templateManager
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

PARAMETER_KEY_NAME_LAST_REQUEST_DATA = 'LAST_REQUEST_DATA'
PARAMETER_KEY_NAME_LAST_SEARCH_DATA = 'LAST_SEACH_DATA'
PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_NAME = 'LAST_RESULT_TABLE_FIELD_GROUP_NAME'
PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_NAME = 'LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_VALUE'
PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_DATA_NAME = 'LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_DATA_FIELD_NAME'
PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_NAME = 'LAST_RESULT_TABLE_FIELD_GROUP_EDIT_VALUE'
PARAMETER_KEY_NAME_SCREEN_UUID = 'SUUID'
PARAMETER_KEY_NAME_SUB_SCREEN_NAME = 'SUB_SCREEN_NAME'
PARAMETER_KEY_NAME_PREVIOUS_SCREEN_NAME = 'PREVIOUS_SCREEN_NAME'

_OPEN_SCREEN_KEY_NAME = 'OPEN_SCREEN'
_OPEN_SCREEN_PARAM_KEY_NAME = 'OPEN_SCREEN_PARAM'

_EDIT_INDEX_FIELD_NEW_RECORD_VALUE = 0

_SESSION_NAME_API_CALL_REQUEST_DATA = 'API_CALL_REQUEST_DATA'


class TableCursorInfo:
    '''
        used for result table
    '''

    def __init__(self, requestData: dict) -> None:
        self.__requestData = requestData
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
        self.__isCallViewAPI = False

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

    def clean(self, fieldGroupName: str = None) -> None:
        if self.__requestData is not None:
            if fieldGroupName is None or self.__fgName == fieldGroupName:
                self.__requestData[PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_NAME] = None
                self.__requestData[PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_NAME] = None
                self.__requestData[PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_FIELD_DATA_NAME] = None
                self.__requestData[PARAMETER_KEY_NAME_LAST_RESULT_TABLE_FIELD_GROUP_EDIT_NAME] = None


class ScreenAPIView(AuthAPIView):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._menuName = None  # ik_menu.menu_nm
        self._menuID = None
        self._screen = None
        self._functionCategory = None
        self._functionCode = None
        self._httpMethod = None
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
        if isNullBlank(self._functionCategory) or isNullBlank(self._functionCode):
            self.__updateFunctionInfoFromMenu()

    def _initMenu(self, **kwargs) -> None:
        """Initialize variable self._menuName and self._menuID when instantiate a view class.

        Get the menu name and by class name.
        """
        menuName = self.getMenuName()
        if isNullBlank(menuName):
            screenName = self.__class__.__name__
            menuName = MenuManager.getMenuNameByScreenName(screenName)
            if isNullBlank(menuName):
                logger.warning("Screen [%s] doesn't find in menu table for view class [%s.%s]." % (screenName, self.__class__.__module__, self.__class__.__qualname__))
            else:
                self._menuID = MenuManager.getMenuId(menuName=menuName)
        else:
            self._menuID = MenuManager.getMenuId(menuName=menuName)
        self.setMenuName(menuName)

    # override
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

    def __getEditIndexFieldGroupNames(self) -> tuple[str]:
        """"""
        sp = self.getSessionParameters()
        fgNames = []
        if sp:
            tableNames = [fg.name for fg in self.getScreen().fieldGroups if fg.groupType == ikui.SCREEN_FIELD_TYPE_RESULT_TABLE]
            for name, value in sp.items():
                if name.endswith('_%s' % ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME):
                    fieldGroupName = name[0:-len('_%s' % ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME)]
                    if fieldGroupName in tableNames:
                        fgNames.append(fieldGroupName)
        return fgNames

    def _deleteEditIndexFieldValue(self, fieldGroupName: str = None) -> None:
        if isNotNullBlank(fieldGroupName):
            self.deleteSessionParameters(fieldGroupName + '_%s' % ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME)
        else:
            sp = self.getSessionParameters()
            if sp is not None:
                tableNames = [fg.name for fg in self.getScreen().fieldGroups if fg.groupType == ikui.SCREEN_FIELD_TYPE_RESULT_TABLE]
                for name, _value in sp.items():
                    if name.endswith('_%s' % ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME):
                        fieldGroupName = name[0:-len('_%s' % ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME)]
                        if fieldGroupName in tableNames:
                            self.deleteSessionParameters(name)
        self._cleanTableCurrentRecordInfo(fieldGroupName)

    def _setEditIndexFieldValue(self, value: any, fieldGroupName: str = None) -> None:
        if fieldGroupName is None:
            fieldGroupNames = self.__getEditIndexFieldGroupNames()
            if len(fieldGroupNames) == 0:
                raise IkException('Please fill in parameter [fieldGroupName]')
            elif len(fieldGroupNames) > 1:
                raise IkException('Too many field group found: %s' % fieldGroupNames)
            fieldGroupName = fieldGroupNames[0]
        self.setSessionParameter(fieldGroupName + '_%s' % ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME, value)

    # def _getEditIndexField(self) -> int:
    #     idStr = self.getRequestData().get(ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME)
    #     return None if isNullBlank(idStr) else int(idStr)

    def _getTableSelectedValue(self, fieldGroupName: str = None) -> any:
        return self._getEditIndexField(fieldGroupName)

    def _getEditIndexField(self, fieldGroupName: str = None) -> any:
        """Get click value for a resultTable when the client call an API named %TableName%_EditIndexField_Click.

        If the parameter "fieldGroupName" is None, then return the first EditIndexField record.

        Example:
            "userTable_EditIndexField_Click".

        The request data name is "EditIndexField". 

        Example:
            self.getRequestData().get("EditIndexField", None).

        Args:
            fieldGroupName(str, optional): Screen field group's name.

        Returns:
            object: Return value. Normally it's an integer (ID field).
        """
        v = None
        if isNotNullBlank(fieldGroupName):
            v = self.getSessionParameter(fieldGroupName + '_%s' % ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME)
        else:
            tableNames = self.__getEditIndexFieldGroupNames()  # if more than 1 found, then ignore
            if len(tableNames) == 1 and isNotNullBlank(tableNames[0]):
                v = self.getSessionParameter(tableNames[0] + '_%s' % ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME)
        if v is None:
            # get index value directly for Plugin column
            v = self.getRequestData().get(ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME, None)
        try:
            return int(v) if v is not None else None
        except:
            return v

    def _getTableSelectedIndexes(self, fieldGroupName: str = None) -> list[int]:
        """Get resultTable's selected records' indexes. 

        If the fieldGroupName is None, then this method return the first data if found.

        Args:
            fieldGroupName (str, optional): Field group name. If it
            param2 (str): The second parameter.

        Returns:
            list[int]: selected records' index. The index starts from 0. None if the parameter is not exists.
        """
        if isNotNullBlank(fieldGroupName):
            return self.getRequestData().get('__%s_selected_indexes' % fieldGroupName, None)
        else:
            # find the first selected indexes
            tableNames = [fg.name for fg in self.getScreen().fieldGroups if fg.groupType == ikui.SCREEN_FIELD_TYPE_RESULT_TABLE]
            for key, value in self.getRequestData().items():
                if key.startswith('__') and key.endswith('_selected_indexes'):
                    fieldGroupName = key[len('__'):-len('_selected_indexe')]
                    if len(fieldGroupName) > 0 and fieldGroupName in tableNames:
                        return value
            return None

    def _getTableSelectedRecords(self, fieldGroupName: str = None) -> list[Model]:
        """Get resultTable's selected records. 

        If the fieldGroupName is None, then this method return the first data if found.

        Args:
            fieldGroupName (str, optional): Field group name. If it
            param2 (str): The second parameter.

        Returns:
            list[Model]: selected records. None if the parameter is not exists.
        """
        if isNotNullBlank(fieldGroupName):
            return self.getRequestData().get('__%s_selected_selected_rcs' % fieldGroupName, None)
        else:
            # find the first selected indexes
            tableNames = [fg.name for fg in self.getScreen().fieldGroups if fg.groupType == ikui.SCREEN_FIELD_TYPE_RESULT_TABLE]
            for key, value in self.getRequestData().items():
                if key.startswith('__') and key.endswith('_selected_rcs'):
                    fieldGroupName = key[len('__'):-len('_selected_rcs')]
                    if len(fieldGroupName) > 0 and fieldGroupName in tableNames:
                        return value
            return None

    def __updateFunctionInfoFromMenu(self) -> None:
        if isNullBlank(self._functionCategory) or isNullBlank(self._functionCode):
            self._functionCategory = self.__module__.split('.')[0]
            self._functionCode = self.__class__.__name__
        # if not isNullBlank(self._menuName) and (isNullBlank(self._functionCategory) or isNullBlank(self._functionCode)):
        #     from django.forms import model_to_dict
        #     menuInfoDict = model_to_dict(MenuManager.getMenuInfoByMenuName(self._menuName))
        #     if menuInfoDict is None:
        #         raise IkMessageException('System error: menu [%s] does not exist.' % self._menuName)
        #     if isNullBlank(self._functionCategory):
        #         ctg = menuInfoDict.get('ctg', None)
        #         self._functionCategory = None if ctg == '' else ctg
        #     if isNullBlank(self._functionCode):
        #         code = menuInfoDict.get('code', None)
        #         self._functionCode = None if code == '' else code

    def setMenuName(self, menuName: str) -> None:
        self._menuName = menuName
        self.__updateFunctionInfoFromMenu()

    def getMenuName(self) -> str:
        return self._menuName

    # YL.ikyo, 2023-06-20 get user menu acl - start
    def isACLWriteable(self) -> bool:
        userID = self.getCurrentUserId()
        if isNullBlank(userID):
            return False
        menuName = self.getMenuName()
        if isNullBlank(menuName):
            return False
        menuID = MenuManager.getMenuId(menuName)
        if isNullBlank(menuID):
            return False
        groupsIDs = ikModels.UserGroup.objects.filter(usr_id=userID).values_list('grp_id', flat=True)
        if len(groupsIDs) == 0:
            return False
        aclPermissions = ikModels.GroupMenu.objects.filter(grp__in=groupsIDs, menu__id=menuID).values_list('acl', flat=True)
        return False if aclPermissions is None else 'W' in aclPermissions

    def isACLReadOnly(self) -> bool:
        userID = self.getCurrentUserId()
        if isNullBlank(userID):
            return False
        menuName = self.getMenuName()
        if isNullBlank(menuName):
            return False
        menuID = MenuManager.getMenuId(menuName)
        if isNullBlank(menuID):
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

    # def setFunctionCategory(self, category) -> None:
    #     self._functionCategory = category

    def getFunctionCategory(self) -> str:
        '''
            function category. E.g. ABC, EFG
        '''
        return self._functionCategory

    # def setFunctionCode(self, code) -> None:
    #     self._functionCode = code

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
            screenClassName = '%s.%s.py:%s' % (self.__class__.__module__, self.__class__.__qualname__, self.__class__.__name__) if screen else None
            logger.error('_getScreenResponse error. Screen=%s, menuID=%s, error=%s' % (screenClassName, self._menuID, str(e)))
            logger.error(e, exc_info=True)
            return ikhttp.IkErrJsonResponse(message='System error.')
        finally:
            self._logDuration(_startTime, description='_getScreenResponse')

    def initScreenData(self, fieldGroup, field, recordsetName, getDataMethodName) -> tuple:
        '''
            return (getDataDone, returnData)
        '''
        snake_get_data_method_name = camel_to_snake(getDataMethodName) if isNotNullBlank(getDataMethodName) else getDataMethodName
        _startTime = datetime.datetime.now()
        try:
            r = None
            getDataDone = False
            if fieldGroup.visible:
                if getDataMethodName is not None:
                    for i in dir(self):
                        if (i == getDataMethodName or i == snake_get_data_method_name) and callable(getattr(self, i)):
                            getDataDone = True
                            fn = getattr(self, i)
                            r = None
                            try:
                                r = fn()
                            except IkException as e:
                                logger.warning('Call method [%s] error: %s' % (i, e), exc_info=True)
                                self._addErrorMessage(str(e))
                            break
                if getDataDone is False:
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
                if field is None:  # table, if field is not None, then ignore it, e.g. get combox data
                    for field2 in fieldGroup.fields:
                        if field2.dataField and (ikDbModels.FOREIGN_KEY_VALUE_FLAG in field2.dataField
                                                 or field2.dataField.startswith(ikDbModels.MODEL_PROPERTY_ATTRIBUTE_NAME_PREFIX)):
                            tableModelAdditionalFields.append(field2.dataField)
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

    def _cleanTableCurrentRecordInfo(self, fieldGroupName: str = None) -> None:
        '''
            Clean table cursor information for resultTable
        '''
        data = self.getLastRequestData()
        if data and len(data) > 0:
            TableCursorInfo(self.getLastRequestData()).clean(fieldGroupName)

    def _getFieldGroupData(self, fieldGroupName) -> object:
        return self._fieldGroupData.get(fieldGroupName, None)

    def __updateDataCursor(self, fieldGroup, data) -> None:
        if data is not None and fieldGroup.groupType == ikui.SCREEN_FIELD_TYPE_RESULT_TABLE and fieldGroup.editable:
            # 1. check upadte from client. E.g. user click the Edit button
            cursorName = None
            cursorValue = None
            cursorInfo = self._getTableCurrentRecordInfo()
            if cursorInfo.fieldGroupName == fieldGroup.name:
                cursorName = cursorInfo.dataFieldName
                cursorValue = cursorInfo.dataValue
            # 2. check the server side. E.g. create a new record and saved.
            if isNullBlank(cursorValue):
                cursorName = ikui.RESULT_TABLE_EDIT_FIELD_RECORD_SET_FIELD_NAME
                cursorValue = self._getEditIndexField(fieldGroup.name)
            # 3. check the model records. Update the first matched record.
            if isNotNullBlank(cursorValue):
                if isinstance(data, Model):
                    data.ik_set_cursor(isCursor=getattr(data, cursorName) == cursorValue)
                elif type(data) == list or isinstance(data, QuerySet):
                    for rc in data:
                        if isinstance(rc, Model):
                            rc.ik_set_cursor(isCursor=getattr(rc, cursorName) == cursorValue)

    def _initScreen(self) -> ikhttp.IkSccJsonResponse:
        '''
            used for react ScreenRender
        '''
        # When jumping to open a new page, save the initial parameters(if any).
        oldSUUID = self._SUUID  # self.request.GET.get(PARAMETER_KEY_NAME_SCREEN_UUID, None)
        openScreenKey = "%s_%s" % (_OPEN_SCREEN_PARAM_KEY_NAME, oldSUUID)
        openScreenParams = self.getSessionParameter(openScreenKey, delete=True, isGlobal=True)

        # reset suuid for a new screen
        characters = string.ascii_letters + string.digits
        SUUID = ''.join(random.choice(characters) for i in range(20))  # generate a new suuid
        self._SUUID = SUUID  # Reset

        if isNotNullBlank(openScreenParams):
            for key, value in openScreenParams.items():
                self.setSessionParameter(key, value)
        screen = self.getScreen()
        fieldGroupNames = []
        if screen is not None:
            fieldGroupNames = screen.getFieldGroupNames()
        logLevel = IkConfig.get('System', "browserLogLevel")
        return ikhttp.IkSccJsonResponse(data={'fieldGroupNames': fieldGroupNames, PARAMETER_KEY_NAME_SCREEN_UUID: SUUID, 'logLevel': logLevel})

    def get_static_folder(self) -> str:
        """
        Get the static folder path in the current app.

        :return: The full static folder path: resources/static.
        """
        app_name = self.__module__.split('.')[0]
        base_dir = Path(__file__).resolve().parent.parent.parent
        static_dir = base_dir / app_name / 'resources' / 'static'
        return static_dir

    def get_last_static_revision_file(self, filename=None, code=None) -> str:
        ''' 
            return static file. E.g. el/css/xxxx-v99.css
        '''
        code = self._functionCode if code is None else code
        path = self.get_static_folder()
        if code is not None:
            path = path / str(code)
        else:
            path = path / str(self.__class__.__name__)
        static_file = ikfs.getLastRevisionFile(path, filename)
        static_file = Path(static_file)
        try:
            parts = static_file.parts
            static_index = parts.index("static")
            return str(Path(*parts[static_index + 1:]))
        except ValueError:
            return str(static_file)

    def get_templates_folder(self) -> str:
        """
        Get the template folder path in the current app.

        :return: The full template folder path: resources/templates.
        """
        app_name = self.__module__.split('.')[0]
        base_dir = Path(__file__).resolve().parent.parent.parent
        template_dir = base_dir / app_name / 'resources' / 'templates'
        return template_dir

    def getLastTemplateRevisionFile(self, filename=None, code=None) -> str:
        ''' 
            filename: if filename is None, then try to find the last file named [code].xlsx, then [code]-Template.xlsx file if exists.
            return template file. E.g. var/templates/ikyo/GP/GP020/xxxx-v99.xlsx
        '''
        templateFilename = filename
        if templateFilename is None and self._functionCode is not None:
            templateFilename = self._functionCode + "-Template.xlsx"
        f = self.__getLastTemplateRevisionFile(templateFilename, code)
        if f is None and filename is None and self._functionCode is not None:
            templateFilename = self._functionCode + ".xlsx"
            f = self.__getLastTemplateRevisionFile(templateFilename, code)
        return f

    def __getLastTemplateRevisionFile(self, filename, code=None) -> str:
        '''
            return template file. E.g. var/templates/ikyo/GP/GP020/xxxx-v99.xlsx
        '''
        return self.__getLastTemplateRevisionFile2(filename, rootFolder=self.get_templates_folder(), code=code)

    def getTemplateFolderName(self) -> str:
        '''
            return templates/ikyo
        '''
        return 'templates/ikyo'

    def __getLastTemplateRevisionFile2(self, filename, rootFolder, code=None) -> str:
        '''
            return template file. E.g. var/{rootFolder}/ikyo/GP/GP020/xxxx-v99.xlsx
        '''
        code = self._functionCode if code is None else code
        path = rootFolder
        if code is not None:
            path = path / str(code)
        else:
            path = path / str(self.__class__.__name__)
        templateFile = ikfs.getLastRevisionFile(path, filename)
        return templateFile

    def downloadFile(self, file, filename: str = None) -> HttpResponseBase:
        if file is None:
            msg = 'Download file cannot be empty. Please ask administrator to check.'
            logger.error(msg)
            return ikhttp.IkErrJsonResponse(message=msg)
        elif not Path(file).is_file():
            logger.error("File doesn't exist. File=[%s]" % Path(file).resolve())
            return ikhttp.IkErrJsonResponse(message="File doesn't exist.")
        else:
            try:
                return ikhttp.responseFile(file, filename=filename)
            except Exception as e:
                return ikhttp.IkErrJsonResponse(message="Download file failed: %s" % str(e))

    def downloadLastTemplateRevisionFile(self, filename, code=None) -> HttpResponseBase:
        '''
            return StreamingHttpResponse if file exists otherwise return IkErrJsonResponse
        '''
        f = self.getLastTemplateRevisionFile(filename, code)
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
        self.__isCallViewAPI = False
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
            if self.__isCallViewAPI:
                # save the api request data for next get screen
                requestData = self.getRequestData()
                try:
                    if requestData is not None:
                        # test request data, because the session will convert data to string, if failed, system will get error.
                        # reference to django.core.signing.py:JSONSerializer.dumps
                        # TODO: fix performance problem.
                        requestData2 = {}
                        for key, value in requestData.items():
                            if isinstance(value, Model):
                                requestData2[key] = {
                                    field.name: getattr(value, field.name)
                                    for field in value._meta.fields
                                }
                            elif isinstance(value, QuerySet) or type(value) == list:
                                value2 = []
                                for item in value:
                                    if isinstance(item, Model):
                                        value2.append({
                                            field.name: getattr(item, field.name)
                                            for field in item._meta.fields
                                        })
                                    else:
                                        value2.append(item)
                                requestData2[key] = value2
                            else:
                                requestData2[key] = value
                        json.dumps(requestData2, ensure_ascii=False)  # test first
                    self.setSessionParameter(_SESSION_NAME_API_CALL_REQUEST_DATA, requestData2)
                except Exception as e:
                    className = '%s.%s.py:%s' % (self.__class__.__module__, self.__class__.__qualname__, self.__class__.__name__)
                    logger.error('%s Object [%s] cannot convert to json string.' % (className, self.getRequestData()))
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
            #  getRequestDataStartTime = datetime.datetime.now()
            self._requestData = self._getRequestData()
            self._logDuration(_getScreenStartTime, description='_getRequestData, screen=%s' % (None if self._screen is None else self._screen.id))
            self._lastRequestData = self.getSessionParameter(PARAMETER_KEY_NAME_LAST_REQUEST_DATA, default=None)
            action = self.getRequestAction(**kwargs)
            if httpMethod == 'post' and action not in [REQUEST_SYSTEM_ACTION_UNLOADED_SCREEN, REQUEST_SYSTEM_ACTION_LOAD_SCREEN_COMPLETED]:
                self.deleteSessionParameters(_SESSION_NAME_API_CALL_REQUEST_DATA)
            if isNotNullBlank(action) and str(action).endswith('_%s_Click' % ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME):  # E.g. userFg_EditIndexField_Click
                parameterName = action[0:-len('_Click')]
                self.setSessionParameter(parameterName, self.getRequestData().get(ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME, None))
            if isNotNullBlank(action) and ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME in self.getRequestData().keys():
                self.setSessionParameter(ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME, self.getRequestData().get(ikui.RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME, None))

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

            # check the edit button function for result table - end
            self._saveRequestData(additionParameterDict=additionalRequestParameters)

            if action != REQUEST_SYSTEM_ACTION_GET_SCREEN and action != REQUEST_SYSTEM_ACTION_LOAD_SCREEN_COMPLETED:
                self._addAccessLog(self.request, menuID=self._menuID, pageName=className, actionName=action, remarks='%s' % httpMethod)
            if action is not None and len(action) > 0 and action[0] == '_':
                return ikhttp.IkErrJsonResponse(message='%s process %s action:[%s]: permission deny.' % (className, httpMethod, action))
            if httpMethod == 'get' and action == REQUEST_SYSTEM_ACTION_INIT_SCREEN:
                if isNullBlank(subScreenNm) or subScreenNm == ikui.MAIN_SCREEN_NAME:
                    # delete the old session parameters
                    self.cleanSessionParameters()
                _initScreenStartTime = datetime.datetime.now()
                try:
                    return self._initScreen()
                finally:
                    self._logDuration(_initScreenStartTime, description='_initScreen screen=%s' % (None if self._screen is None else self._screen.id))
            elif httpMethod == 'get' and action == REQUEST_SYSTEM_ACTION_GET_SCREEN:
                return self._getScreenResponse()
            elif httpMethod == 'post' and action == REQUEST_SYSTEM_ACTION_UNLOADED_SCREEN:
                try:
                    return self._unloadScreen()
                finally:
                    self.cleanSessionParameters()
            elif httpMethod == 'post' and action == REQUEST_SYSTEM_ACTION_LOAD_SCREEN_COMPLETED:
                return self._unloadScreenDone()
            else:
                self.__isCallViewAPI = True
                actionFn = None
                # format:
                # action$fieldGroupName
                # e.g.
                # 1) save
                # 2) save$
                #    save as 1)
                # 3) save$fieldGroup1
                #    this is system defined method
                #
                actionPrms = action.split('$')
                actionFnName = actionPrms[0]
                callViewFn = False
                self._beforeProcessAction(actionFnName, {})  # TODO: actionParameters
                try:
                    actionFn = getattr(self, actionFnName, None)
                    if isNullBlank(actionFn):
                        snake_action_fn_name = camel_to_snake(actionFnName)
                        actionFn = getattr(self, snake_action_fn_name)
                    if len(inspect.getfullargspec(actionFn).args) > 1:
                        raise AttributeError('Function is not found: %s' % actionFnName)  # the action function only has one parameter - "self"
                    callViewFn = True
                except AttributeError as ae:
                    if actionFnName != '-':  # '-' can be used in search field group
                        if not isResultTableClickColumnDefaultEvent:
                            if len(actionPrms) != 1 and len(actionPrms) != 2:
                                logger.error('%s process %s action:[%s] - function is not found', className, httpMethod, actionFnName)
                                return ikhttp.IkErrJsonResponse(message='%s process %s action:[%s]: function is not found' % (className, httpMethod, action))
                            logger.debug('%s process %s action:[%s] - function is not found, then try system build-in function...', className, httpMethod, action)
                            return self._processBuildInFunction(actionPrms[0], actionPrms[1] if len(actionPrms) > 1 else None)
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

    def getUserRequestData(self) -> dict:
        data = self.getSessionParameter(_SESSION_NAME_API_CALL_REQUEST_DATA, {})
        return data if data else {}

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
        """
            Ignore Model data: Object of type Moele is not JSON serializable
        """
        data = self.getRequestData()
        if data is None:
            return
        jData = {}
        searchFgData = None
        for key, value in additionParameterDict.items():
            jData[key] = value
        for name, value in data.items():
            t = type(value)
            if t == str or t == int or t == float or t == None:
                jData[name] = value
            elif t == tuple or t == list:
                # iignore models
                isIgnore = False
                for item in value:
                    if isinstance(item, Model):
                        isIgnore = True
                        break
                if not isIgnore:
                    jData[name] = value
            if self._screen is not None:
                fg = self._screen.getFieldGroup(name)
                if fg is not None and fg.groupType == ikui.SCREEN_FIELD_TYPE_SEARCH:
                    if searchFgData is None:
                        searchFgData = {}
                    searchFgData[name] = value
        self.setSessionParameter(PARAMETER_KEY_NAME_LAST_REQUEST_DATA, jData)
        if searchFgData is not None:
            self.setSessionParameter(PARAMETER_KEY_NAME_LAST_SEARCH_DATA, searchFgData)

    def getLastRequestData(self) -> dict:
        return {} if self._lastRequestData is None else self._lastRequestData

    def getLastRequestDataAsInt(self, name) -> int:
        v = self.getLastRequestData().get(name, None)
        return None if isNullBlank(v) else int(v)

    def getSearchData(self, fieldGroupName: str = None, name: str = None, default: any = None) -> dict:
        data = self.getSessionParameter(PARAMETER_KEY_NAME_LAST_SEARCH_DATA, default=None)
        if data is None:
            return default
        data2 = data
        if fieldGroupName is not None:
            data2 = data.get(fieldGroupName, None)
        if name is None:
            return data2
        return data2.get(name, default)

    def read_template_file(self, filename, code=None) -> str:
        '''
            return file content with \n
        '''
        f = self.__getLastTemplateRevisionFile2(filename, self.get_templates_folder(), code=code)
        if f is None or not pathlib.Path(f).is_file():
            raise IkException('Web template file [%s] does not exist. Please ask administrator to check.' % filename)
        content = None
        with open(f, newline='', encoding='utf-8') as f:
            content = f.read()
        return content

    def read_template_file_with_prams(self, filename, code=None, pram=None) -> str:
        '''
            return file content 
            default template folder: [app_nm]/resources/templates/[class_nm]/[file_nm]
            example: el/resources/templates/EL001/xxxx-v99.xlsx
        '''
        file_path = (code if isNotNullBlank(code) else self._functionCode) + '/' + filename
        return templateManager.loadTemplateFile(file_path, pram)

    def _beforeProcessAction(self, action: str, parameters: list[str]) -> None:
        pass

    def _unloadScreen(self) -> ikhttp.IkJsonResponse:
        return ikhttp.IkSccJsonResponse()

    def _unloadScreenDone(self) -> ikhttp.IkJsonResponse:
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
            if type(messages) != list and type(messages) != tuple:
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
        if parameters is None:
            parameters = {}
        parameters[PARAMETER_KEY_NAME_PREVIOUS_SCREEN_NAME] = self.getMenuName()
        self.setSessionParameter(name=_OPEN_SCREEN_PARAM_KEY_NAME, value=parameters, isGlobal=True)
        return ikhttp.IkSccJsonResponse(data=rspData)

    def _getPreviousScreenRequestData(self) -> dict:
        """
            get previous screen's menu name from session
        """
        return self.getSessionParameter(name=_OPEN_SCREEN_PARAM_KEY_NAME, isGlobal=True)

    def _deletePreviousScreenRequestData(self) -> dict:
        """
            get previous screen's menu name from session
        """
        return self.getSessionParameter(name=_OPEN_SCREEN_PARAM_KEY_NAME, delete=True, isGlobal=True)

    def _getPreviousScreenName(self) -> str:
        """
            get previous screen's menu name from session
        """
        prms = self._getPreviousScreenRequestData()
        return prms.get(PARAMETER_KEY_NAME_PREVIOUS_SCREEN_NAME, None) if prms is not None else None

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
            currentRecordID = self._getEditIndexField(fieldGroup.name)
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

    def _processBuildInFunction(self, functionName: str, fieldGropName: str = None) -> ikhttp.IkJsonResponse:
        '''
            cancel/delete/save/new
        '''
        if functionName == 'new':
            return self._BIFNew(fieldGropName)
        elif functionName == 'cancel':
            return self._BIFCancel(fieldGropName)
        elif functionName == 'delete':
            return self._BIFDelete()
        elif functionName == 'save':
            return self._BIFSave()
        elif functionName == 'search':  # YL, 2024-04-28
            return self._BIFSearch()
        else:
            return ikhttp.IkErrJsonResponse(message='Unsupport system function [%s].' % functionName)

    def _BIFNew(self, fieldGropName: str = None) -> ikhttp.IkJsonResponse:
        '''
            build-in function: new
        '''
        if isNullBlank(fieldGropName):
            resultTables = [fg.name for fg in self.getScreen().fieldGroups if fg.groupType == ikui.SCREEN_FIELD_TYPE_RESULT_TABLE]
            if len(resultTables) == 1:
                fieldGropName = resultTables[0]
            if isNullBlank(fieldGropName):
                return ikhttp.IkErrJsonResponse(message='Fieldgroup Name is mandatory for build-in function [new].')
        screen = self._screen
        fg = screen.getFieldGroup(fieldGropName)
        if fg is None:
            return ikhttp.IkErrJsonResponse(message='Fieldgroup [%s] is not found for build-in function [new].' % fieldGropName)
        if isNullBlank(fg.recordSetName):
            return ikhttp.IkErrJsonResponse(message='RecordSet is not found for field group [%s] for build-in function [new].' % fieldGropName)
        self._setEditIndexFieldValue(_EDIT_INDEX_FIELD_NEW_RECORD_VALUE, fg.name)  # id = 0
        return ikhttp.IkSccJsonResponse()

    def _BIFCancel(self, fieldGropName: str = None) -> ikhttp.IkJsonResponse:
        '''
            build-in function: cancel
        '''
        if isNullBlank(fieldGropName):
            fieldGropNames = self.__getEditIndexFieldGroupNames()
            if len(fieldGropNames) == 0:
                return ikhttp.IkErrJsonResponse(message='Fieldgroup Name is mandatory for build-in function [new].')
            elif len(fieldGropNames) > 1:
                raise IkException('Too many fieldgroup Names found: %s' % fieldGropNames)
            fieldGropName = fieldGropNames[1]
        screen = self._screen
        fg = screen.getFieldGroup(fieldGropName)
        if fg is None:
            return ikhttp.IkErrJsonResponse(message='Fieldgroup [%s] is not found for build-in function [new].' % fieldGropName)
        if isNullBlank(fg.recordSetName):
            return ikhttp.IkErrJsonResponse(message='RecordSet is not found for field group [%s] for build-in function [new].' % fieldGropName)
        self._deleteEditIndexFieldValue(fg.name)
        return ikhttp.IkSccJsonResponse()

    def _BIFDelete(self) -> ikhttp.IkJsonResponse:
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
                    self._deleteEditIndexFieldValue(fgl.parentFieldGroup.name)
        return b.toIkJsonResponse1()

    def _BIFSave(self) -> ikhttp.IkJsonResponse:
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
                    self._setEditIndexFieldValue(keyValue, fgl.parentFieldGroup.name)
        return b.toIkJsonResponse1()

    # YL, 2024-04-28
    def _BIFSearch(self, fieldGropName: str = None) -> ikhttp.IkJsonResponse:
        pass

    # YL.ikyo, 2023-06-06 for table pagination - start
    def _getPaginatorPageSize(self, tableName: str) -> int:
        screen = self._screen
        if screen.getFieldGroup(tableName) is None:
            logger.error('Field group: %s does not exist.' % tableName)
            raise IkValidateException('Field group: %s does not exist.' % tableName)
        if isNullBlank(screen.getFieldGroup(tableName).pageSize):
            logger.error('Page size does not exist. tableName=%s' % tableName)
            return None
        return int(screen.getFieldGroup(tableName).pageSize)

    def _getPaginatorPageNumber(self, tableName: str) -> int:
        prmName = "PAGEABLE_%s_pageNum" % tableName
        pageNumStr = self.getRequestData().get(prmName)
        if isNullBlank(pageNumStr):
            logger.error('Page number does not exist. tableName=%s' % tableName)
            return 0
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

    def _getPaginattorRecords(self, fieldGroupName: str, queryFilter: QuerySet) -> tuple:
        """
            return [rc1, rc2, rc3...], totalAmount
        """
        rcs = None
        pageNum = self._getPaginatorPageNumber(fieldGroupName)
        total = queryFilter.count()
        if pageNum == 0:
            rcs = queryFilter
        else:
            pageSize = self._getPaginatorPageSize(fieldGroupName)
            paginator = Paginator(queryFilter, pageSize)
            rcs = paginator.get_page(pageNum)
        rcs = [r for r in rcs]
        return rcs, total

    # YL.ikyo, 2023-06-06 for table pagination - end
    def _addAccessLog(self, request, menuID: int, pageName: str, actionName: str = None, remarks: str = None) -> None:
        """Add screen access log.

        Args:
            request: Django request.
            menuID (int): Menu ID.
            pageName (str): Django view class name.
            actionName (str, optional): Action name. It should be a method name defined in django view class.
            remarks (str, optional): Remarks.
        """
        addAccessLog(request, menuID, pageName, actionName, remarks)

    def _saveModels(self, models: any = None, modifyModels: any = None, deleteModels: any = None, successMessage: str = None, errorMessage: str = None) -> Boolean2:
        """ Save models.

        Save order: 1. delete models. 2. update models. 3. models.

        Args:
            models(any, optional): A model or model list/tuple.
            modifyModels(any, optional): A model or model list/tuple.
            deleteModels(any, optional): A model or model list/tuple.
            successMessage(str, optional): Success message to replace the system success message.
            errorMessage(str, optional): Save failed message to replace the system error message.

        Returns:
            Boolean2: Save success or not. None if total models is 0.
        """
        if models is None and modifyModels is None and deleteModels is None:
            return None
        totalRecords = 0
        if models:
            totalRecords = (len(models) if (type(models) == list or type(models) == tuple) else 1)
        if modifyModels:
            totalRecords += (len(modifyModels) if (type(modifyModels) == list or type(modifyModels) == tuple) else 1)
        if deleteModels:
            totalRecords += (len(deleteModels) if (type(deleteModels) == list or type(deleteModels) == tuple) else 1)
        if totalRecords == 0:
            return None
        trn = IkTransaction()
        if deleteModels:
            if type(deleteModels) == list or type(deleteModels) == tuple:
                for m in deleteModels:
                    trn.delete(m)
            else:
                trn.delete(deleteModels)
        if modifyModels:
            if type(modifyModels) == list or type(modifyModels) == tuple:
                for m in modifyModels:
                    trn.modify(m)
            else:
                trn.modify(modifyModels)
        if models:
            if type(models) == list or type(models) == tuple:
                for m in models:
                    trn.add(m)
            else:
                trn.add(models)
        rst = trn.save()
        if rst.value:
            return Boolean2(True, successMessage) if successMessage else rst
        return Boolean2(False, errorMessage) if errorMessage else rst

    def getPagingResponse(self, table_name: str, table_data=None, table_sql=None, get_style_func=None, format_res_func=None, message: str = None):
        page_size = self._getPaginatorPageSize(table_name)
        page_num = self._getPaginatorPageNumber(table_name)
        total_len = 0
        results, css_style = [], []
        if isNotNullBlank(table_data):
            total_len = len(table_data)
            if isNullBlank(page_size) or page_num == 0:
                results = table_data
            else:
                paginator = Paginator(table_data, page_size)
                results = paginator.get_page(page_num).object_list
        elif isNotNullBlank(table_sql):
            total_len = self._getPaginatorTableDataAmount(table_sql)
            results = self._getPaginatorTableData(table_sql, pageNum=page_num, pageSize=page_size)

        tableModelAdditionalFields = []
        fields = self._screen.getFieldGroup(table_name).fields
        for field in fields:
            if field.dataField and (ikDbModels.FOREIGN_KEY_VALUE_FLAG in field.dataField
                                    or field.dataField.startswith(ikDbModels.MODEL_PROPERTY_ATTRIBUTE_NAME_PREFIX)):
                tableModelAdditionalFields.append(field.dataField)
        if len(tableModelAdditionalFields) > 0:
            results = ikhttp.IkSccJsonResponse(data=results).getJsonData(modelAdditionalFields=tableModelAdditionalFields)

        if isNotNullBlank(format_res_func):
            results = format_res_func(results)
        if isNotNullBlank(get_style_func):
            css_style = get_style_func(results)

        return self.getSccJsonResponse(data=results, cssStyle=css_style, paginatorDataAmount=total_len, message=message)

    def getSccJsonResponse(self, data: any = None, cssStyle: list[dict] = None, paginatorDataAmount: int = None, message: str = None) -> ikhttp.IkSccJsonResponse:
        return ikhttp.IkSccJsonResponse(data={"data": data, "cssStyle": cssStyle, "paginatorDataAmount": paginatorDataAmount}, message=message)


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


def camel_to_snake(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()
