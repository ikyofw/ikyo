import copy
import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from threading import Lock

from django.db import models
from django.db.models.query import QuerySet

import core.core.http as ikhttp
import core.db.model as ikDbModels
import core.models as ikModels
import core.utils.djangoUtils as ikDjangoUtils
import core.utils.httpUtils as ikHttpUtils
import core.utils.modelUtils as modelUtils
from core.core.exception import IkValidateException
from core.models import ScreenFgType, ScreenFieldWidget
from core.utils.langUtils import convertStr2Json, isNotNullBlank, isNullBlank
from django_backend.settings import BASE_DIR
from iktools import IkConfig

from . import uiCache as ikuiCache
from . import uidb as ikuidb

logger = logging.getLogger('ikyo')


SCREEN_FIELD_TYPE_TABLE                 = 'table'
SCREEN_FIELD_TYPE_RESULT_TABLE          = 'resultTable'
SCREEN_FIELD_TYPE_FIELDS                = 'fields'
SCREEN_FIELD_TYPE_SEARCH                = 'search'
SCREEN_FIELD_TYPE_ICON_BAR              = 'iconBar'
SCREEN_FIELD_TYPE_HTML                  = 'html'
SCREEN_FIELD_TYPE_IFRAME                = 'iframe'
SCREEN_FIELD_TYPE_UDF_VIEWER            = 'viewer'              

SCREEN_FIELD_GROUP_TYPES_TABLE  = (SCREEN_FIELD_TYPE_TABLE,        SCREEN_FIELD_TYPE_RESULT_TABLE)
SCREEN_FIELD_GROUP_TYPE_DETAILS = (SCREEN_FIELD_TYPE_FIELDS,       SCREEN_FIELD_TYPE_SEARCH)
SCREEN_FIELD_NORMAL_GROUP_TYPES = (SCREEN_FIELD_TYPE_TABLE,        SCREEN_FIELD_TYPE_RESULT_TABLE,
                                   SCREEN_FIELD_TYPE_FIELDS,       SCREEN_FIELD_TYPE_SEARCH,
                                   SCREEN_FIELD_TYPE_ICON_BAR,     SCREEN_FIELD_TYPE_HTML,
                                   SCREEN_FIELD_TYPE_IFRAME,       SCREEN_FIELD_TYPE_UDF_VIEWER)

SCREEN_FIELD_WIDGET_LABEL               = 'Label'
SCREEN_FIELD_WIDGET_TEXT_BOX            = 'TextBox'
SCREEN_FIELD_WIDGET_TEXT_AREA           = 'TextArea'
SCREEN_FIELD_WIDGET_PASSWORD            = 'Password'
SCREEN_FIELD_WIDGET_DATE_BOX            = 'DateBox'
SCREEN_FIELD_WIDGET_COMBO_BOX           = 'ComboBox'
SCREEN_FIELD_WIDGET_LIST_BOX            = 'ListBox'
SCREEN_FIELD_WIDGET_ADVANCED_COMBOBOX   = 'AdvancedComboBox'
SCREEN_FIELD_WIDGET_ADVANCED_SELECTION  = 'AdvancedSelection'
SCREEN_FIELD_WIDGET_CHECK_BOX           = 'CheckBox'
SCREEN_FIELD_WIDGET_BUTTON              = 'Button'
SCREEN_FIELD_WIDGET_ICON_AND_TEXT       = 'IconAndText'
SCREEN_FIELD_WIDGET_FILE                = 'File'
SCREEN_FIELD_WIDGET_PLUGIN              = 'Plugin'
SCREEN_FIELD_WIDGET_HTML                = 'Html'

SCREEN_FIELD_SELECT_WIDGETS = (SCREEN_FIELD_WIDGET_COMBO_BOX, SCREEN_FIELD_WIDGET_LIST_BOX, SCREEN_FIELD_WIDGET_ADVANCED_COMBOBOX, SCREEN_FIELD_WIDGET_ADVANCED_SELECTION)
SCREEN_FIELD_NORMAL_WIDGETS = (SCREEN_FIELD_WIDGET_LABEL, SCREEN_FIELD_WIDGET_TEXT_BOX, SCREEN_FIELD_WIDGET_TEXT_AREA, SCREEN_FIELD_WIDGET_PASSWORD, SCREEN_FIELD_WIDGET_DATE_BOX,
                               SCREEN_FIELD_WIDGET_COMBO_BOX, SCREEN_FIELD_WIDGET_LIST_BOX, SCREEN_FIELD_WIDGET_ADVANCED_COMBOBOX, SCREEN_FIELD_WIDGET_ADVANCED_SELECTION,
                               SCREEN_FIELD_WIDGET_CHECK_BOX, SCREEN_FIELD_WIDGET_BUTTON, SCREEN_FIELD_WIDGET_ICON_AND_TEXT, SCREEN_FIELD_WIDGET_FILE, SCREEN_FIELD_WIDGET_PLUGIN,
                               SCREEN_FIELD_WIDGET_HTML)

SCREEN_FIELD_GROUP_SELECTION_MODE_SINGLE = 'single'
SCREEN_FIELD_GROUP_SELECTION_MODE_MULTIPLE = 'multiple'

SCREEN_FIELD_GROUP_PAGE_TYPE_SERVER = 'server'
SCREEN_FIELD_GROUP_PAGE_TYPE_CLIENT = 'client'
GET_DATA_URL_FLAG_PARAMETER_NAME = 'GETDATAREQUEST'

MAIN_SCREEN_NAME = 'Main Screen'

REFRESH_INTERVAL = 1  # seconds


def getRelativeScreenFileFolder() -> Path:
    return Path(os.path.join('var', 'sys', 'screen'))


def getScreenFileFolder() -> Path:
    return Path(os.path.join(BASE_DIR, 'var', 'sys', 'screen'))


def getScreenCsvFileFolder() -> Path:
    return Path(os.path.join(BASE_DIR, 'var', 'sys', 'screen-csv'))


def getScreenFileTemplateFolder() -> Path:
    return Path(os.path.join(BASE_DIR, 'var', 'sys', 'screen-template'))


def getScreenFieldGroupType(typeName) -> str:
    if not isNullBlank(typeName) and type(typeName) == str:
        fgTypeRc = ScreenFgType.objects.filter(type_nm=typeName).first()
        if isNotNullBlank(fgTypeRc):
            return fgTypeRc.type_nm
    raise IkValidateException('Unsupported screen field group type: %s' % typeName)


def getScreenFieldWidget(widgetName) -> str:
    if not isNullBlank(widgetName) and type(widgetName) == str:
        fieldWidgetRc = ScreenFieldWidget.objects.filter(widget_nm=widgetName).first()
        if isNotNullBlank(fieldWidgetRc):
            return fieldWidgetRc.widget_nm
    raise IkValidateException('Unsupported screen field widget: %s' % widgetName)


def getScreenFieldGroupSelectionMode(selectionMode) -> str:
    if isNullBlank(selectionMode):
        return None
    if type(selectionMode) == str:
        if selectionMode.upper() == SCREEN_FIELD_GROUP_SELECTION_MODE_MULTIPLE.upper():
            return SCREEN_FIELD_GROUP_SELECTION_MODE_MULTIPLE
        elif selectionMode.upper() == SCREEN_FIELD_GROUP_SELECTION_MODE_SINGLE.upper():
            return SCREEN_FIELD_GROUP_SELECTION_MODE_SINGLE
    raise IkValidateException('Unknown screen field group selection mode: %s' % selectionMode)


def getScreenFieldGroupDataPageType(pageType) -> str:
    if isNullBlank(pageType):
        return None
    if type(pageType) == str:
        if pageType.upper() == SCREEN_FIELD_GROUP_PAGE_TYPE_SERVER.upper():
            return SCREEN_FIELD_GROUP_PAGE_TYPE_SERVER
        elif pageType.upper() == SCREEN_FIELD_GROUP_PAGE_TYPE_CLIENT.upper():
            return SCREEN_FIELD_GROUP_PAGE_TYPE_CLIENT
    raise IkValidateException('Unknown screen field group page type: %s' % pageType)


def isTableFieldGroup(fieldGroupType) -> bool:
    return fieldGroupType in SCREEN_FIELD_GROUP_TYPES_TABLE


def isDetailFieldGroup(fieldGroupType) -> bool:
    return fieldGroupType in SCREEN_FIELD_GROUP_TYPE_DETAILS


RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME = 'EditIndexField'
RESULT_TABLE_EDIT_FIELD_RECORD_SET_FIELD_NAME = 'id'


def getResultTableEditFieldName(resultTableName) -> str:
    return resultTableName + '_' + RESULT_TABLE_EDIT_COLUMN_PARAMETER_NAME


def getResultTableEditButonDefaultEventName(fieldName) -> str:
    return '%s_Click' % fieldName


def _getSceenFieldName(fieldName: str, actionName: str, parentFieldGroupName: str) -> str:
    if isNotNullBlank(fieldName):
        return fieldName
    else:
        if actionName:
            actionName = actionName.split('/')[-1]
            return '%s_%s' % (parentFieldGroupName, actionName)
        else:
            return '%s_%s' % (parentFieldGroupName, time.perf_counter_ns())


class ScreenRecordSet:
    '''
        Used for "Recordset" table.
    '''

    def __init__(self) -> None:
        self.name = None
        self.modelNames = None
        self.distinct = False
        self.queryFields = None
        self.queryWhere = None
        self.queryOrder = None
        self.queryLimit = None
        # YL.ikyo, 2023-04-20 database no use - start
        self.rmk = None
        # self.queryPageSize = None
        # self.readOnly = False
        # YL.ikyo, 2023-04-20 - end

    # def getData(self) -> dict:
    #    pass


class ScreenField:
    '''
        table fields, toobar icons
    '''

    def __init__(self, parent) -> None:
        self.parent = parent
        self.name = None
        self.caption = None
        self.tooltip = None
        self.widget = None
        self.widgetParameter = None
        self.editable = True
        self.visible = True
        self.required = False
        self.unique = False
        self.dataField = None
        # YL.ikyo, 2023-04-20 database no use - start
        # self.dataKeyField = None
        self.dataFormat = None
        self.dataValidation = None
        self.eventHandler = None
        self.eventHandlerParameter = None
        self.style = None
        self.footer = None
        self.rmk = None
        # YL.ikyo, 2023-04-20 - end

    def getEventHandlerName(self) -> str:
        return None if self.eventHandler is None else self.eventHandler.split('/')[-1]

    def _initData(self, fieldIndexInFieldGroup, getFieldWidgetDataFn=None) -> None:
        if getFieldWidgetDataFn is not None:
            getFieldWidgetDataFn(self, fieldIndexInFieldGroup)

    def toJson(self) -> dict:
        '''
            screen field to json
        '''
        fgType = self.parent.groupType
        # screen, fieldGroup and field
        isEditable = self.parent.parent.editable and self.editable  # just match screen editable & button editable, ignore toolbar
        jField = {}
        # YL.ikyo, 2023-04-20 database no use - start
        fieldName = _getSceenFieldName(self.name, self.getEventHandlerName(), self.parent.name)
        if isTableFieldGroup(fgType) or isDetailFieldGroup(fgType):
            jField = {'name': fieldName,
                      'caption': self.caption,
                      'tooltip': self.tooltip,
                      'widget': self.widget,
                      'widgetParameter': self.widgetParameter,
                      'editable': isEditable,
                      'visible': self.visible,
                      'required': self.required,
                      'dataField': self.dataField,
                      # 'dataKeyField': self.dataKeyField,
                      'dataFormat': self.dataFormat,
                      'dataValidation': self.dataValidation,
                      'eventHandler': self.eventHandler,
                      'eventHandlerParameter': self.eventHandlerParameter,
                      'style': self.style,
                      'rmk': self.rmk,
                      'footer': self.footer
                      }
        # YL.ikyo, 2023-04-20 - end
        elif fgType == SCREEN_FIELD_TYPE_ICON_BAR:
            jField = {'name': fieldName,
                      'caption': self.caption,
                      'tooltip': self.tooltip,
                      'widget': self.widget,
                      'widgetParameter': self.widgetParameter,
                      'visible': self.visible,
                      'enable': isEditable,
                      'eventHandler': self.eventHandler,
                      'eventHandlerParameter': self.eventHandlerParameter
                      }
        return jField


class FieldGroupLink:
    '''
        a fieldGroup's link
    '''
    # YL.ikyo, 2023-04-20 - start

    def __init__(self, parentFieldGroup, parentKey, localKey) -> None:
        self.__parentFieldGroup = parentFieldGroup
        self.__parentKey = parentKey
        self.__localKey = localKey
        self.__rmk = None

    @property
    def parentFieldGroup(self) -> object:
        '''
            ScreenFieldGroup
        '''
        return self.__parentFieldGroup

    @property
    def parentKey(self) -> str:
        return self.__parentKey

    @property
    def localKey(self) -> str:
        return self.__localKey

    def __str__(self) -> str:
        return 'Field Group=%s, Parent Key=%s, Local Key=%s' % \
            (self.__parentFieldGroup.name if self.__parentFieldGroup else '',
             self.__parentKey if self.__parentKey else '',
             self.__localKey if self.__localKey else '',
             self.__rmk if self.__rmk else '')
    # YL.ikyo, 2023-04-20 - start


class ScreenFieldGroup:
    '''
        Used for "FieldGroups" table.
    '''

    def __init__(self, parent) -> None:
        self.parent = parent
        self.name = None
        self.groupType = None
        self.caption = None
        self.recordSetName = None
        self.deletable = None
        self.editable = None
        self.visible = True
        self.insertable = None
        self.highlightRow = None
        # self.selectable = None
        self.selectionMode = None
        self.cols = None
        self.pageType = None  # client/server/None
        self.pageSize = None
        self.beforeDisplayAdapter = None  # javascript function for react
        self.fields = []  # [ScreenField, ...]
        self.data = None  # Used for HtmlFieldGroup
        self.style = []
        self.additionalProps = None
        self.rmk = None  # YL.ikyo, 2023-04-20
        self.outerLayoutParams = None
        self.innerLayoutType = None
        self.innerLayoutParams = None
        self.fieldGroupLink = None
        self.__dataUrl = None

    def isTable(self) -> bool:
        '''table, resultTable...
        '''
        return isTableFieldGroup(self.groupType)

    def isResultTable(self) -> bool:
        '''
            result table
        '''
        return self.groupType == SCREEN_FIELD_TYPE_RESULT_TABLE

    def isDetail(self) -> bool:
        return isDetailFieldGroup(self.groupType)

    def getField(self, name) -> ScreenField:
        if isNullBlank(name):
            raise IkValidateException('Field name is mandatory.')
        for field in self.fields:
            if field.name == name:
                return field
        raise IkValidateException('Field does not exist. Screen=[%s], fieldGroup=[%s], field=[%s].' % (self.parent.parent.id, self.parent.name, name))

    def getFields(self, fieldNames) -> list:
        return [self.getField(name) for name in fieldNames]

    def getFieldNames(self) -> list:
        return [f.name for f in self.fields]

    def getResultTableEditColumnField(self) -> ScreenField:
        if self.groupType == SCREEN_FIELD_TYPE_RESULT_TABLE:
            defaultName = getResultTableEditButonDefaultEventName(getResultTableEditFieldName(self.name))
            for i in range(len(self.fields) - 1, -1, -1):
                field = self.fields[i]
                if field.getEventHandlerName() == defaultName:
                    return field
        return None

    def _initData(self, getFieldGroupDataFn=None, getHtmlDataUrlFn=None, getPDFDataUrlFn=None, getFieldWidgetDataFn=None) -> None:
        if isTableFieldGroup(self.groupType) or isDetailFieldGroup(self.groupType):
            jTableColumns = []
            fieldCounter = -1
            eventHandler = None
            eventHandlerParameter = None
            # YL.ikyo, 2023-02-15 CHANGE bugfix add eventHandler & eventHandlerParameter to fields after field[0](when searchFg set fields[0] un-visible will bug) - start
            if self.groupType == SCREEN_FIELD_TYPE_SEARCH:
                eventHandler = self.fields[0].eventHandler
                eventHandlerParameter = self.fields[0].eventHandlerParameter
            for field in self.fields:
                fieldCounter += 1
                if field.visible:
                    jTableColumns.append(field._initData(fieldCounter, getFieldWidgetDataFn))
                if self.groupType == SCREEN_FIELD_TYPE_SEARCH:
                    field.eventHandler = eventHandler
                    field.eventHandlerParameter = eventHandlerParameter
            # YL.ikyo, 2023-02-15 - end

            fgData, fgDataUrl = None, None
            if getFieldGroupDataFn is not None:
                fgData, fgDataUrl = getFieldGroupDataFn(self)
            if isTableFieldGroup(self.groupType) and isinstance(fgData, dict):
                self.data = fgData[self.name] if self.name in fgData else []
                self.style = fgData['style'] if 'style' in fgData else []
            else:
                self.data = fgData
                self.__dataUrl = fgDataUrl

        elif self.groupType == SCREEN_FIELD_TYPE_HTML or self.groupType == SCREEN_FIELD_TYPE_IFRAME:
            self.__dataUrl = getHtmlDataUrlFn(self.name)
        elif self.groupType == SCREEN_FIELD_TYPE_UDF_VIEWER:
            self.__dataUrl = getPDFDataUrlFn(self.name)

    def toJson(self) -> dict:
        '''
            field group to json
        '''
        jFg = None
        editable = self.parent.editable and self.editable  # need to check the parent screen can be edit or not

        if isTableFieldGroup(self.groupType) or isDetailFieldGroup(self.groupType):
            jTableColumns = []
            for field in self.fields:
                if field.visible:
                    jTableColumns.append(field.toJson())

            jFg = {'caption': self.caption,
                   'name': self.name,
                   'type': self.groupType,
                   'data': self.data,
                   'dataUrl': self.__dataUrl,
                   'editable': editable,
                   'deletable': self.deletable,
                   'visible': self.visible,  # YL.ikyo, 2022-12-23 bugfix
                   'insertable': self.insertable,
                   'highlightRow': self.highlightRow,
                   'cols': self.cols,  # YL.ikyo, 2022-09-27 add field group columns define
                   'fields': jTableColumns,
                   'pageType': self.pageType,
                   'pageSize': self.pageSize,
                   'additionalProps': self.additionalProps,
                   'rmk': self.rmk,  # YL.ikyo, 2023-04-20
                   'beforeDisplayAdapter': self.beforeDisplayAdapter
                   }
            if isTableFieldGroup(self.groupType):
                jFg['showRowNo'] = True
                jFg['style'] = self.style
            if self.groupType == SCREEN_FIELD_TYPE_RESULT_TABLE:
                # jFg['editable'] = False
                jFg['insertable'] = False
                jFg['deletable'] = False
                jFg['selectionMode'] = self.selectionMode
            elif self.groupType == SCREEN_FIELD_TYPE_FIELDS:
                del jFg['insertable']
                del jFg['deletable']
                # del jFg['beforeDisplayAdapter']
                pass
            elif self.groupType == SCREEN_FIELD_TYPE_SEARCH:
                del jFg['insertable']
                del jFg['deletable']
                # del jFg['beforeDisplayAdapter']
        elif self.groupType == SCREEN_FIELD_TYPE_ICON_BAR:
            jIcons = []
            for button in self.fields:
                if button.visible:
                    jIcons.append(button.toJson())
            jFg = {'name': self.name,
                   'type': self.groupType,
                   'icons': jIcons,
                   'editable': editable
                   }
        elif self.groupType == SCREEN_FIELD_TYPE_HTML or self.groupType == SCREEN_FIELD_TYPE_IFRAME:
            jFg = {'name': self.name,
                   'type': self.groupType,
                   'caption': self.caption,
                   'data': self.html,
                   'dataUrl': self.__dataUrl
                   }
        elif self.groupType == SCREEN_FIELD_TYPE_UDF_VIEWER:
            jFg = {'name': self.name,
                   'type': self.groupType,
                   'caption': self.caption,
                   'data': self.data,
                   'dataUrl': self.__dataUrl
                   }
        else:
            # other types: E.g. viewer
            jFg = {
                'caption': self.caption,
                'name': self.name,
                'type': self.groupType,
                'data': self.data,
                'dataUrl': self.__dataUrl,
                'editable': editable,
                'visible': self.visible,  # YL, 2022-12-23 bugfix
                'rmk': self.rmk,  # YL, 2023-04-20
                'beforeDisplayAdapter': self.beforeDisplayAdapter
            }

        jFg['outerLayoutParams'] = self.outerLayoutParams
        if not isNullBlank(self.innerLayoutType):
            jFg['innerLayoutType'] = self.innerLayoutType
            jFg['innerLayoutParams'] = self.innerLayoutParams

        if len(self.fields) > 0:
            jFg['maxFieldsNum'] = len(self.fields)
        return jFg


class TableHeaderFooterRow:
    def __init__(self, fieldName) -> None:
        self.fieldName = fieldName
        self.headers = []
        self.footer = None
        self.rmk = None  # YL.ikyo, 2023-04-20


class TableHeaderFooter:
    def __init__(self) -> None:
        self.fieldGroupName = None
        self.fields = []

    def getTotalHeaderRows(self) -> int:
        if len(self.fields) == 0:
            return None
        return len(self.fields[0].headers)

    def getField(self, fieldName) -> TableHeaderFooterRow:
        if isNullBlank(fieldName):
            return None
        for field in self.fields:
            if field.fieldName == fieldName:
                return field
        return None


class Screen:
    def __init__(self, screenDefinition) -> None:
        self.__screenDefinition = screenDefinition
        self.subScreenName = None
        self.apiVersion = None
        self.id = None
        self.title = None
        self.description = None
        self.layoutType = None
        self.layoutParams = None
        self.className = None
        self.editable = True
        self.autoRefreshInterval = None  # seconds
        self.autoRefreshAction = None
        self.rmk = None  # YL.ikyo, 2023-04-20
        self.recordsets = []
        self.fieldGroups = []
        self.fieldGroupLinks = {}
        self.tableHeaderFooters = {}
        self.__staticFiles = []  # static files. E.g. js, css, images
        self.__helpUrl = None

    def addStaticFile(self, staticFile) -> None:
        '''
            static files in templates/static/ folder
        '''
        if staticFile:
            self.__staticFiles.append(staticFile)

    def getStaticFiles(self) -> list:
        return self.__staticFiles

    def getRecordset(self, name) -> ScreenRecordSet:
        for rs in self.recordsets:
            if rs.name == name:
                return rs
        return None

    def getFieldGroup(self, name) -> ScreenFieldGroup:
        for rs in self.fieldGroups:
            if rs.name == name:
                return rs
        return None

    def getFieldGroupLink(self, fieldGroupName) -> FieldGroupLink:
        return self.fieldGroupLinks.get(fieldGroupName, None)

    def getFieldGroupsByTypes(self, types) -> list:
        g = []
        for fg in self.fieldGroups:
            if fg.groupType in types:
                g.append(fg)
        return g

    def getFieldGroups(self, names) -> list:
        return [self.getFieldGroup(name) for name in names]

    def getFieldGroupNames(self) -> list:
        return [fg.name for fg in self.fieldGroups]

    def getField(self, fieldGroupName, fieldName) -> ScreenField:
        fg = self.getFieldGroup(name=fieldGroupName)
        if fg is None:
            raise IkValidateException('Field group does not exist. Screen=[%s], FieldGroup=[%s]' % (self.id, fieldGroupName))
        return fg.getField(fieldName)

    def getRecordSet(self, recordName) -> ScreenRecordSet:
        for rs in self.recordsets:
            if rs.name == recordName:
                return rs
        return None

    def getFieldGroupRecordSet(self, fieldGroupName) -> ScreenRecordSet:
        fg = self.getFieldGroup(fieldGroupName)
        if fg is None:
            raise IkValidateException('Field group does not exist. Screen=[%s], FieldGroup=[%s]' % (self.id, fieldGroupName))
        if isNullBlank(fg.recordSetName):
            return None
        return self.getRecordSet(fg.recordSetName)

    def _initData(self, getFieldGroupDataFn=None, getHtmlDataUrlFn=None, getPDFDataUrlFn=None, getFieldWidgetDataFn=None,
                  getScreenHelpFn=None) -> None:
        self.__helpUrl = None if getScreenHelpFn is None else getScreenHelpFn(self.id)
        for fg in self.fieldGroups:
            if fg.visible:
                fg._initData(getFieldGroupDataFn, getHtmlDataUrlFn, getPDFDataUrlFn, getFieldWidgetDataFn)

    def toJson(self) -> dict:
        '''
            screen to json
        '''
        screenId = self.id
        jScreen = {}
        jScreen['viewID'] = screenId
        jScreen['viewTitle'] = self.title
        jScreen['viewDesc'] = self.description
        jScreen['layoutType'] = self.layoutType
        jScreen['layoutParams'] = self.layoutParams
        jScreen['helpUrl'] = self.__helpUrl
        jScreen['autoRefreshInterval'] = self.autoRefreshInterval
        jScreen['autoRefreshAction'] = self.autoRefreshAction
        jScreen['editable'] = self.editable
        jScreen['rmk'] = self.rmk  # YL.ikyo, 2023-04-20
        # TODO: change to 'fieldGroups': []
        for fg in self.fieldGroups:
            if fg.visible:
                jScreen[fg.name] = fg.toJson()
        return jScreen

    def setVisible(self, visible) -> None:
        for fg in self.fieldGroups:
            fg.visible = visible

    def setEditable(self, editable) -> None:
        self.setFieldGroupsEnable(self.fieldGroups, isInsertable=False, isDeletable=False, isEditable=False)

    def setTitle(self, value) -> None:
        self.title = value

    '''
        Field Groups
    '''

    def setFieldGroupsVisible(self, fieldGroupNames, visible) -> None:
        '''
            fieldGroupNames(str/list): field group names
        '''
        if fieldGroupNames is None or visible is None:
            return
        if type(visible) != bool:
            raise IkValidateException('Parameter "visible" should be a bool value.')
        if type(fieldGroupNames) == str:
            fieldGroupNames = [fieldGroupNames]
        for obj in fieldGroupNames:
            fg = None
            if type(obj) == ScreenFieldGroup:
                fg = obj
            elif type(obj) == str:
                fg = self.getFieldGroup(obj)
            if fg is None:
                raise IkValidateException('Field group [%s] is not found in screen [%s], please check.' % (obj, self.id))
            fg.visible = visible

    def setFieldGroupsEnable(self, fieldGroupNames, isInsertable=None, isDeletable=None, isEditable=None) -> None:
        '''
            fieldGroupNames(str/list): field group names
        '''
        if type(fieldGroupNames) == str:
            fieldGroupNames = [fieldGroupNames]
        if isInsertable is not None and type(isInsertable) != bool:
            raise IkValidateException('Parameter "isInsertable" should be a bool value.')
        if isDeletable is not None and type(isDeletable) != bool:
            raise IkValidateException('Parameter "isDeletable" should be a bool value.')
        if isEditable is not None and type(isEditable) != bool:
            raise IkValidateException('Parameter "isEditable" should be a bool value.')
        for obj in fieldGroupNames:
            fg = None
            if type(obj) == ScreenFieldGroup:
                fg = obj
            elif type(obj) == str:
                fg = self.getFieldGroup(obj)
            if fg is None:
                raise IkValidateException('Field group [%s] is not found in screen [%s], please check.' % (obj, self.id))
            if isInsertable is not None:
                fg.insertable = isInsertable
            if isDeletable is not None:
                fg.deletable = isDeletable
            if isEditable is not None:
                fg.editable = isEditable

    # YL.ikyo, 2023-03-29, update field group caption
    def setFieldGroupCaption(self, fieldGroupName, value) -> None:
        '''
            fieldGroupName(str): field group name
        '''
        if fieldGroupName is None or value is None:
            return
        if type(fieldGroupName) != str:
            raise IkValidateException('Parameter "fieldGroupName" should be a str value.')
        if type(value) != str:
            raise IkValidateException('Parameter "value" should be a str value.')
        fg = self.getFieldGroup(fieldGroupName)
        if fg is None:
            raise IkValidateException('Field group [%s] is not found in screen [%s], please check.' % (fieldGroupName, self.id))
        fg.caption = value

    # YL.ikyo, 2023-05-16 set field group page size
    def setFieldGroupPageSize(self, fieldGroupName, pageSize) -> None:
        '''
            fieldGroupName(str): field group name
        '''
        '''
            pageSize(int): page size
        '''
        if fieldGroupName is None or pageSize is None:
            return
        if type(pageSize) != str and type(pageSize) != int:
            raise IkValidateException('Parameter "pageSize" should be a bool value.')
        pageSize = int(pageSize)
        if type(fieldGroupName) != str:
            raise IkValidateException('Parameter "fieldGroupName" should be a str value.')
        fg = self.getFieldGroup(fieldGroupName)
        if fg is None:
            raise IkValidateException('Field group [%s] is not found in screen [%s], please check.' % (fieldGroupName, self.id))
        fg.pageSize = pageSize

    '''
        Field
    '''
    # YL.ikyo, 2022-12-21 set fields visible - start

    def setFieldsVisible(self, fieldGroupName, fieldNames, visible) -> None:
        '''
            fieldGroupName(str): field group name
        '''
        '''
            fieldNames(str/list): field names
        '''
        if fieldGroupName is None or fieldNames is None or visible is None:
            return
        if type(visible) != bool:
            raise IkValidateException('Parameter "visible" should be a bool value.')
        if type(fieldGroupName) != str:
            raise IkValidateException('Parameter "fieldGroupName" should be a str value.')
        fg = self.getFieldGroup(fieldGroupName)
        if fg is None:
            raise IkValidateException('Field group [%s] is not found in screen [%s], please check.' % (fieldGroupName, self.id))
        if type(fieldNames) == str:
            fieldNames = [fieldNames]
        for name in fieldNames:
            f = self.getField(fg.name, name)
            if f is None:
                raise IkValidateException('Field [%s] is not found in Field group [%s], please check.' % (name, fieldGroupName))
            f.visible = visible

    def setFieldsEditable(self, fieldGroupName, fieldNames, editable) -> None:
        '''
            fieldGroupName(str): field group name
        '''
        '''
            fieldNames(str/list): field names
        '''
        if fieldGroupName is None or fieldNames is None or editable is None:
            return
        if type(editable) != bool:
            raise IkValidateException('Parameter "editable" should be a bool value.')
        if type(fieldGroupName) != str:
            raise IkValidateException('Parameter "fieldGroupName" should be a str value.')
        fg = self.getFieldGroup(fieldGroupName)
        if fg is None:
            raise IkValidateException('Field group [%s] is not found in screen [%s], please check.' % (fieldGroupName, self.id))
        if type(fieldNames) == str:
            fieldNames = [fieldNames]
        if not fg.editable and editable:  # field group editable is False, some fields is True
            for field in fg.fields:
                field.editable = fg.editable
            fg.editable = editable
        for name in fieldNames:
            f = self.getField(fg.name, name)
            if f is None:
                raise IkValidateException('Field [%s] is not found in Field group [%s], please check.' % (name, fieldGroupName))
            f.editable = editable
    # YL.ikyo, 2022-12-21 - end

    # XH, 2022-03-28 set fields visible - start
    def setFieldsRequired(self, fieldGroupName, fieldNames, required) -> None:
        '''
            fieldGroupName(str): field group name
        '''
        '''
            fieldNames(str/list): field names
        '''
        if fieldGroupName is None or fieldNames is None or required is None:
            return
        if type(required) != bool:
            raise IkValidateException('Parameter "required" should be a bool value.')
        if type(fieldGroupName) != str:
            raise IkValidateException('Parameter "fieldGroupName" should be a str value.')
        fg = self.getFieldGroup(fieldGroupName)
        if fg is None:
            raise IkValidateException('Field group [%s] is not found in screen [%s], please check.' % (fieldGroupName, self.id))
        if type(fieldNames) == str:
            fieldNames = [fieldNames]
        for name in fieldNames:
            f = self.getField(fg.name, name)
            if f is None:
                raise IkValidateException('Field [%s] is not found in Field group [%s], please check.' % (name, fieldGroupName))
            f.required = required
    # XH, 2023-03-28 - end

    # update field caption
    def setFieldCaption(self, fieldGroupName, fieldName, value) -> None:
        '''
            fieldGroupName(str): field group name
        '''
        '''
            fieldName(str): field name
        '''
        if fieldGroupName is None or fieldName is None or value is None:
            return
        if type(fieldGroupName) != str:
            raise IkValidateException('Parameter "fieldGroupName" should be a str value.')
        if type(fieldName) != str:
            raise IkValidateException('Parameter "fieldName" should be a str value.')
        # if type(value) != str:
        #     raise IkValidateException('Parameter "value" should be a str value.')
        f = self.getField(fieldGroupName, fieldName)
        if f is None:
            raise IkValidateException('Field [%s] is not found in field group [%s], please check.' % (fieldName, fieldGroupName))
        f.caption = value

    # update field value
    def setFieldValue(self, fieldGroupName, fieldName, value) -> None:
        '''
            fieldGroupName(str): field group name
        '''
        '''
            fieldName(str): field name
        '''
        if fieldGroupName is None or fieldName is None or value is None:
            return
        if type(fieldGroupName) != str:
            raise IkValidateException('Parameter "fieldGroupName" should be a str value.')
        if type(fieldName) != str:
            raise IkValidateException('Parameter "fieldName" should be a str value.')
        if type(value) != str:
            raise IkValidateException('Parameter "value" should be a str value.')
        f = self.getField(fieldGroupName, fieldName)
        if f is None:
            raise IkValidateException('Field [%s] is not found in field group [%s], please check.' % (fieldName, fieldGroupName))
        f.value = value

    # update html field group data
    def setHtmlFgValue(self, fieldGroupName, value) -> None:
        '''
            fieldGroupName(str): html field group name
        '''
        if fieldGroupName is None or fieldName is None or value is None:
            return
        if type(fieldGroupName) != str:
            raise IkValidateException('Parameter "fieldGroupName" should be a str value.')
        if type(value) != str:
            raise IkValidateException('Parameter "value" should be a str value.')
        fg = self.getFieldGroup(fieldGroupName)
        if fg is None:
            raise IkValidateException('HTML field group [%s] is not found in screen [%s], please check.' % (fieldGroupName, self.id))
        fg.data = value
    # YL.ikyo, 2023-03-29 - end


class ScreenDefinition:
    def __init__(self, name, fullName, filePath, definition) -> None:
        self.name = name
        self.fullName = fullName
        self.filePath = filePath
        self.definition = definition


class __DFN_Summary():
    '''
        used for developing
    '''

    def __init__(self) -> None:
        self.groupTypes = {}
        self.fieldWidgets = {}
        self.fieldWidgetParameters = {}
        self.fieldEventHandler = {}
        self.__hasPrintOnce = False

    def hasPrintOnce(self) -> bool:
        return self.__hasPrintOnce

    def __isExists(self, nameList, key) -> bool:
        for i in nameList:
            if type(i) == str and type(key) == str and i.upper() == key.upper():
                return True
        return False

    def addGroupType(self, screenName, groupType) -> None:
        if not isNullBlank(groupType) and groupType not in self.groupTypes.keys():
            if not self.__isExists(self.groupTypes.keys(), groupType):
                self.groupTypes[groupType] = screenName
        if not isNullBlank(groupType) and 'devdemo.' in screenName and groupType in self.groupTypes.keys():
            self.groupTypes[groupType] = screenName

    def addFieldWidget(self, screenName, widget) -> None:
        if not isNullBlank(widget) and widget not in self.fieldWidgets.keys():
            if not self.__isExists(self.fieldWidgets.keys(), widget):
                self.fieldWidgets[widget] = screenName
        if not isNullBlank(widget) and 'devdemo.' in screenName and widget in self.groupTypes.keys():
            self.fieldWidgets[widget] = screenName

    def addFieldWidgetParameters(self, screenName, parameters) -> None:
        if not isNullBlank(parameters) and parameters not in self.fieldWidgetParameters.keys():
            if not self.__isExists(self.fieldWidgetParameters.keys(), parameters):
                self.fieldWidgetParameters[parameters] = screenName
        if not isNullBlank(parameters) and 'devdemo.' in screenName and parameters in self.groupTypes.keys():
            self.fieldWidgetParameters[parameters] = screenName

    def addFieldEventHandler(self, screenName, event) -> None:
        if not isNullBlank(event) and event not in self.fieldEventHandler.keys():
            if not self.__isExists(self.fieldEventHandler.keys(), event):
                self.fieldEventHandler[event] = screenName
        if not isNullBlank(event) and 'devdemo.' in screenName and event in self.groupTypes.keys():
            self.fieldEventHandler[event] = screenName

    def reset(self) -> None:
        self.groupTypes.clear()
        self.fieldWidgets.clear()
        self.fieldWidgetParameters.clear()
        self.fieldEventHandler.clear()

    def print(self) -> None:
        if not self.__hasPrintOnce:
            print('----------------------- Screen Developing Tools Output Start ------------------')
            self.__print(self.groupTypes, 'Group Types')
            self.__print(self.fieldWidgets, 'Widgets')
            self.__print(self.fieldWidgetParameters, 'Widget Parameters')
            self.__print(self.fieldEventHandler, 'Event Handlers')
            print('----------------------- Screen Developing Tools Output End --------------------')
            self.__hasPrintOnce = True

    def __print(self, printDict, name) -> None:
        printList = []
        for item in printDict.keys():
            printList.append(item)
        printList.sort()
        print()
        print('------------ %s Start ------------' % name)
        print('------------ TOTAL = %s ---------' % len(printDict))
        i = 0
        for item in printList:
            i += 1
            screen = printDict.get(item, None)
            print('%s,%s,%s' % (i, item, screen))
        print('------------ %s End  ------------' % name)
        print()


DNF_Summary = __DFN_Summary()


def acceptScreenFile(filename) -> bool:
    # ~$ is temp file, . is a hide file
    return filename.lower().endswith('.xlsx') and filename[0:2] != '~$' and ' - Copy.' not in filename and filename[0] != '-' and filename[0] != '_' and filename[0] != '.'


def acceptScreenFolder(foldername) -> bool:
    return foldername[0] != '-' and foldername[0] != '_' and foldername[0] != '.' and not foldername.endswith(' - Copy')


class __ScreenManager:
    def __init__(self):
        self.__screenDefinitions = {}  # {screen name: screen definition}
        self.__screenFileFolder = self.getScreenFileFolder()
        self.__readLock = Lock()

    def refresh(self) -> None:
        """
            Load screen spreadsheet files to database and then update the spreadsheet files from database.
        """
        if ikDjangoUtils.isRunDjangoServer():
            self.__parseScreenFiles()

    def getScreenFileFolder(self) -> Path:
        return getScreenFileFolder()

    def getScreenFileTemplateFolder(self) -> Path:
        return getScreenFileTemplateFolder()

    def getScreenFileExampleFolder(self) -> Path:
        return getScreenFileTemplateFolder()

    def __parseScreenFiles(self):
        global DNF_Summary
        try:
            self.__readLock.acquire()
            DNF_Summary.reset()
            self.__screenDefinitions.clear()
            screenFiles = {}

            # Restart Server Run
            ikuidb.syncScreenDefinitions()
            ikuiCache.clearAllCache()

            if not DNF_Summary.hasPrintOnce():
                for screenName in screenFiles.keys():
                    self.getScreen(screenName)
                if IkConfig.getSystem('printScreenSpreadsheetSummaryInfo', 'false').lower() == 'true':
                    DNF_Summary.print()

        except Exception as e:
            logger.error(e, exc_info=True)
            raise e
        finally:
            self.__readLock.release()

    # YL.ikyo, 2023-04-18 get screen from database
    def _getScreenDefinitionFromDB(self, name) -> ScreenDefinition:
        dfn = None
        if "." in name:
            name = name.split(".")[1]
        screenRc = ikModels.Screen.objects.filter(screen_sn__iexact=name).order_by("-rev").first()
        if screenRc:
            dfn = {}
            dfn['viewAPIRev'] = screenRc.api_version
            dfn['viewID'] = screenRc.screen_sn
            dfn['viewTitle'] = screenRc.screen_title
            dfn['viewDesc'] = screenRc.screen_dsc
            dfn['layoutType'] = screenRc.layout_type
            dfn['layoutParams'] = screenRc.layout_params
            dfn['viewName'] = screenRc.class_nm
            dfn['editable'] = screenRc.editable
            # YL, 2024-02-28, Bugfix for auto refresh - start
            if isNotNullBlank(screenRc.auto_refresh_interval):
                dfn['autoRefresh'] = str(screenRc.auto_refresh_interval)
                if isNotNullBlank(screenRc.auto_refresh_action):
                    dfn['autoRefresh'] = dfn['autoRefresh'] + ";" + screenRc.auto_refresh_action
            # YL, 2024-02-28 - end

            # Recordset
            dfn['recordsetTable'] = []
            recordsetRcs = ikModels.ScreenRecordset.objects.filter(screen=screenRc).order_by("id")
            for rc in recordsetRcs:
                data = []
                data.append(rc.recordset_nm)
                data.append(rc.sql_fields)
                data.append(rc.sql_models)
                data.append(rc.sql_where)
                data.append(rc.sql_order)
                data.append(rc.sql_limit)
                # data.append('') # old page size(no use)
                # data.append('') # old ReadOnly(no use)
                data.append(rc.rmk)
                dfn['recordsetTable'].append(data)

            # Field Groups
            dfn['fieldGroupTable'] = []
            fieldGroupRcs = ikModels.ScreenFieldGroup.objects.filter(screen=screenRc).order_by("seq")
            for rc in fieldGroupRcs:
                data = []
                data.append(rc.fg_nm)
                data.append(rc.fg_type.type_nm if rc.fg_type else None)
                data.append(rc.caption)
                data.append(rc.recordset.recordset_nm if rc.recordset else None)
                data.append(rc.deletable)
                data.append(rc.editable)
                data.append(rc.insertable)
                data.append(rc.highlight_row)
                data.append(rc.selection_mode)
                data.append(rc.cols)
                # data.append(rc.sort_new_rows)
                data.append(rc.data_page_type)
                data.append(rc.data_page_size)
                data.append(rc.outer_layout_params)
                data.append(rc.inner_layout_type)
                data.append(rc.inner_layout_params)
                data.append(rc.html)
                data.append(rc.additional_props)
                data.append(rc.rmk)
                dfn['fieldGroupTable'].append(data)

            # Fields
            dfn['fieldTable'] = []
            fieldRcs = ikModels.ScreenField.objects.filter(screen=screenRc).order_by("seq")
            lastFgNm = None
            for rc in fieldRcs:
                data = []
                fgNm = rc.field_group.fg_nm if rc.field_group else None
                data.append(fgNm)
                # data.append(fgNm if lastFgNm != fgNm else None)
                # lastFgNm = fgNm

                data.append(rc.field_nm)
                data.append(rc.caption)
                data.append(rc.tooltip)
                data.append(rc.visible)
                data.append(rc.editable)
                data.append(rc.widget.widget_nm if rc.widget else None)
                data.append(rc.widget_parameters)
                data.append(rc.db_field)
                data.append(rc.md_format)
                data.append(rc.md_validation)
                data.append(rc.event_handler)
                data.append(rc.styles)
                data.append(rc.rmk)
                dfn['fieldTable'].append(data)

            # Sub Screen
            dfn['subScreenTable'] = []
            dfnRcs = ikModels.ScreenDfn.objects.filter(screen=screenRc)
            for rc in dfnRcs:
                data = []
                data.append(rc.sub_screen_nm)
                data.append(rc.field_group_nms)
                dfn['subScreenTable'].append(data)

            # Field Group Links
            dfn['fieldGroupLinkTable'] = []
            fgLinkRcs = ikModels.ScreenFgLink.objects.filter(screen=screenRc).order_by("field_group__seq")
            for rc in fgLinkRcs:
                data = []
                data.append(rc.field_group.fg_nm if rc.field_group else None)
                data.append(rc.parent_field_group.fg_nm if rc.parent_field_group else None)
                data.append(rc.parent_key)
                data.append(rc.local_key)
                data.append(rc.rmk)
                dfn['fieldGroupLinkTable'].append(data)

            # Table Header and Footer
            dfn['headerFooterTable'] = []
            fgHeaderFooterRcs = ikModels.ScreenFgHeaderFooter.objects.filter(screen=screenRc).order_by("field_group__seq", "field__seq")
            for rc in fgHeaderFooterRcs:
                data = []
                data.append(rc.field_group.fg_nm if rc.field_group else None)
                data.append(rc.field.field_nm if rc.field else None)
                data.append(rc.header_level1)
                data.append(rc.header_level2)
                data.append(rc.header_level3)
                data.append(rc.footer)
                data.append(rc.rmk)
                dfn['headerFooterTable'].append(data)
        if dfn is None:
            logger.debug('getScreenDefinitionFromDB(%s) from database is empty.' % name)
            return None

        return dfn

    def getScreen(self, screenName: str, subScreenNm=None, globalRequestUrlParameters: dict = None) -> Screen:
        '''
            screenName (str): screen's name
            globalRequestUrlParameters (dict, optional):  add parameters to all request urls (e.g. get data request, button action ...)
        '''
        global DNF_Summary
        # screenDfn = self.__getScreenDefinition(screenName)
        screenDfn = ikuiCache.getPageDefinitionFromCache(screenName)
        if isNullBlank(screenDfn):
            screenDfn = self._getScreenDefinitionFromDB(screenName)  # YL.ikyo, 2023-04-18 get screen from database
            ikuiCache.setPageDefinitionCache(screenName, screenDfn)
        dfn = copy.deepcopy(screenDfn)

        if dfn is None:
            logger.error('getScreenDefinition(%s).data=None' % screenName)
            return None

        screen = Screen(screenDefinition=dfn)
        # 1. screen information
        screen.apiVersion = dfn['viewAPIRev']
        screen.id = dfn['viewID']
        screen.title = dfn['viewTitle']
        screen.description = dfn['viewDesc']
        screen.layoutType = dfn['layoutType']
        screen.layoutParams = dfn['layoutParams']
        screen.className = dfn['viewName']
        # YL.ikyo, 2023-04-20 - start
        # screen.editable = ('yes' == dfn.get('editable', '').lower())
        screen.editable = self.__toBool(dfn.get('editable'))
        # YL.ikyo, 2023-04-20 - end

        autoRefreshInterval, autoRefreshAction = self.__getScreenAutoRefreshInfo(dfn.get('autoRefresh', None))
        screen.autoRefreshInterval = autoRefreshInterval
        screen.autoRefreshAction = ikHttpUtils.setQueryParameter(autoRefreshAction, globalRequestUrlParameters)

        # 2. Recordset
        for recordsetRecord in dfn['recordsetTable']:
            srs = ScreenRecordSet()
            srs.name = recordsetRecord[0]
            srs.queryFields = recordsetRecord[1]
            srs.modelNames = recordsetRecord[2]
            srs.queryWhere = recordsetRecord[3]
            srs.queryOrder = recordsetRecord[4]
            srs.queryLimit = None if recordsetRecord[5] is None else int(recordsetRecord[5])
            # YL.ikyo, 2023-04-20 from database no use - start
            # srs.queryPageSize = recordsetRecord[6]
            # srs.readOnly = recordsetRecord[7] is not None and 'yes' == recordsetRecord[7].lower()
            # YL.ikyo, 2023-04-20 - end
            screen.recordsets.append(srs)

        # 3. FieldGroups
        # for fgName, fgType, caption, recordsetName, deletable, editable, insertable, selectable, cols, pageType, pageSize in dfn['fieldGroupTable']: # old from excel
        subScreenTable = dfn['subScreenTable']
        displayFgs = None  # None:  default display all field group, []: have not subScreen, [xxx]: the field group display in sub screen
        if subScreenNm is None:
            subScreenNm = MAIN_SCREEN_NAME
        for i in subScreenTable:
            if i[0].strip().lower() == subScreenNm.strip().lower():
                displayFgs = [item.strip() for item in i[1].split(',')]
        if displayFgs is None and subScreenNm is not None and subScreenNm.strip().lower() != MAIN_SCREEN_NAME.lower():
            displayFgs = []
        screen.subScreenName = subScreenNm

        for fgName, fgType, caption, recordsetName, deletable, editable, insertable, highlightRow, selectionMode, cols, pageType, \
                pageSize, outerLayoutParams, innerLayoutType, innerLayoutParams, html, additionalProps, rmk in dfn['fieldGroupTable']:  # from database
            if displayFgs is not None and fgName not in displayFgs:
                continue
            sfg = ScreenFieldGroup(parent=screen)
            sfg.name = fgName
            sfg.groupType = getScreenFieldGroupType(fgType)
            sfg.caption = caption
            sfg.recordSetName = recordsetName
            sfg.deletable = self.__toBool(deletable)
            sfg.editable = self.__toBool(editable)
            sfg.insertable = self.__toBool(insertable)
            sfg.highlightRow = self.__toBool(highlightRow)
            sfg.selectionMode = getScreenFieldGroupSelectionMode(selectionMode)
            sfg.cols = None if cols is None else int(cols)
            sfg.pageType = getScreenFieldGroupDataPageType(pageType)
            sfg.pageSize = None if isNullBlank(pageSize) else pageSize
            sfg.outerLayoutParams = outerLayoutParams
            sfg.innerLayoutType = innerLayoutType
            sfg.innerLayoutParams = innerLayoutParams
            sfg.html = html
            sfg.additionalProps = None if isNullBlank(additionalProps) else self.parseWidgetPrams(additionalProps)
            sfg.beforeDisplayAdapter = None  # a javascript function for react

            DNF_Summary.addGroupType(screenName, sfg.groupType)

            if isTableFieldGroup(fgType) or isDetailFieldGroup(fgType):
                if isNullBlank(sfg.beforeDisplayAdapter):
                    sfg.beforeDisplayAdapter = None
                if fgType == SCREEN_FIELD_TYPE_RESULT_TABLE:
                    # sfg.editable = False
                    sfg.insertable = False
                    sfg.deletable = False
                    sfg.selectionMode = getScreenFieldGroupSelectionMode(selectionMode)
                elif fgType == SCREEN_FIELD_TYPE_FIELDS:
                    sfg.beforeDisplayAdapter = None
                elif fgType == SCREEN_FIELD_TYPE_SEARCH:
                    sfg.insertable = None
                    sfg.deletable = None
                    sfg.beforeDisplayAdapter = None
            screen.fieldGroups.append(sfg)

        currentFieldGroupName = None
        for fieldDfn in dfn['fieldTable']:
            fieldGroupName, name, caption, tooltip, visible, editable, widget, widgetPrms, dataField, dataFormat, dataValidation, eventHandler, style, rmk = fieldDfn
            if displayFgs is not None and fieldGroupName not in displayFgs:
                continue
            if currentFieldGroupName is None or not isNullBlank(fieldGroupName) and fieldGroupName != currentFieldGroupName:
                currentFieldGroupName = fieldGroupName
            sfg = screen.getFieldGroup(currentFieldGroupName)
            if sfg is None:
                raise IkValidateException('Field group [%s] is not found in screen [%s].' % (currentFieldGroupName, screen.id))
            field = ScreenField(parent=sfg)
            sfg.fields.append(field)

            eventHandlerUrl, eventHandlerPrms = self.__getEventHandler(screen, eventHandler)
            if isNullBlank(widget):
                if sfg.groupType == SCREEN_FIELD_TYPE_ICON_BAR:
                    widget = SCREEN_FIELD_WIDGET_ICON_AND_TEXT
                else:
                    widget = SCREEN_FIELD_WIDGET_LABEL

            field.name = _getSceenFieldName(name, dataField if isNotNullBlank(dataField) else eventHandlerUrl, fieldGroupName)
            field.caption = caption
            field.tooltip = tooltip
            field.widget = getScreenFieldWidget(widget)
            field.editable = self.__toBool(editable, default=True)
            # field.visible = not self.__toBool(visible, default=False) # YL.ikyo, 2023-04-20 old from excel
            field.visible = self.__toBool(visible, default=True)  # YL.ikyo, 2023-04-20 from data database(visible)
            field.required = self.__toBool(None, default=False)  # TODO: reference to recordset
            field.dataField = dataField
            # field.dataKeyField = dataKeyField # XH, 2023-04-20 old from excel
            field.dataFormat = dataFormat
            field.dataValidation = dataValidation
            field.eventHandler = ikHttpUtils.setQueryParameter(eventHandlerUrl, globalRequestUrlParameters)
            field.eventHandlerParameter = eventHandlerPrms
            field.style = self.__getStylePrms(style)
            # field is an input parameter, then put this line at the end.
            # TODO:....
            field.widgetParameter = self.__getWidgetPramsOnly(widgetPrms)

            DNF_Summary.addFieldWidget(screenName, field.widget)
            DNF_Summary.addFieldWidgetParameters(screenName + ' -> ' + str(widget), widgetPrms)
            DNF_Summary.addFieldEventHandler(screenName, field.eventHandler)

            if isTableFieldGroup(sfg.groupType) or isDetailFieldGroup(sfg.groupType):
                if isNullBlank(field.widget):
                    field.widget = SCREEN_FIELD_WIDGET_LABEL
                if field.widget == SCREEN_FIELD_WIDGET_LABEL:
                    field.editable = False
                # TODO:
            elif sfg.groupType == SCREEN_FIELD_TYPE_ICON_BAR:
                if isNullBlank(field.widget):
                    field.widget = SCREEN_FIELD_WIDGET_ICON_AND_TEXT
                # TODO:
        for sfg in screen.fieldGroups:
            if sfg.groupType == SCREEN_FIELD_TYPE_RESULT_TABLE and sfg.editable:
                # result table add edit field
                sfg.fields.append(self.__getResultTableEditButtonField(sfg))

        # 4. FieldGroupLinks
        fieldGroupLinkTable = dfn.get('fieldGroupLinkTable', None)
        if fieldGroupLinkTable is not None and len(fieldGroupLinkTable) > 0:
            # TODO
            # for fieldGropName, parentFieldGroupName, parentKey, localKeyin fieldGroupLinkTable: # rmk
            for fieldGropName, parentFieldGroupName, parentKey, localKey, rmk in fieldGroupLinkTable:  # rmk
                if isNullBlank(fieldGropName) and isNullBlank(parentKey) and isNullBlank(localKey):
                    continue  # ignore the blank row
                # 1) check the field group is exists or not
                fieldGroup = screen.getFieldGroup(fieldGropName)
                if fieldGroup is None:
                    raise IkValidateException(
                        'Field group [%s] is not found in Field Group Link table. Please check screen [%s].' % (fieldGropName, screen.id))
                parentFieldGroup = screen.getFieldGroup(parentFieldGroupName)
                if parentFieldGroup is None:
                    raise IkValidateException(
                        'Field group [%s] is not found in Field Group Link table. Please check screen [%s].' % (parentFieldGroupName, screen.id))
                # 2) check the parent field gorup is exists or not
                # 2) check the parent key and local key
                if isNullBlank(parentKey) and isNullBlank(localKey):
                    raise IkValidateException(
                        'Parent Key and Local Key are mandatory in Field Group Link table: Field group [%s], screen [%s].' % (fieldGropName, screen.id))
                # screen.getFieldGroupRecordSet()
                fgl = FieldGroupLink(parentFieldGroup, parentKey, localKey)
                fieldGroup.fieldGroupLink = fgl
                screen.fieldGroupLinks[fieldGropName] = fgl

        # 5. table header / footers
        headerFooterTable = dfn.get('headerFooterTable', None)
        if headerFooterTable is not None and len(headerFooterTable) > 0:
            tableFgNames = []
            for fg in screen.fieldGroups:
                if fg.isTable():
                    tableFgNames.append(fg.name)

            lastFgName = None
            hfMap = {}  # header footer table detail map
            rowIndex = -1
            for row in headerFooterTable:
                fgName = row[0]
                if displayFgs is not None and fgName not in displayFgs:
                    continue
                if len(tableFgNames) == 0:
                    raise IkValidateException(
                        'No table field group found in current screen. Please check screen: [%s] sub screen: [%s].' % (screen.id, screen.subScreenName))
                if isNullBlank(fgName):
                    fgName = lastFgName
                    rowIndex += 1
                else:
                    lastFgName = fgName
                    rowIndex = 0
                if not isNullBlank(fgName) and fgName not in tableFgNames:
                    raise IkValidateException(
                        'Field Group [%s] is not found in FieldGroups table in [Table Header and Footer for inline tables]. Please check screen [%s].' % (fgName, screen.id))
                if isNullBlank(fgName):
                    raise IkValidateException(
                        'Field Group Name is mandatory in [Table Header and Footer for inline tables]. Please check screen [%s].' % (screen.id))
                tableHf = hfMap.get(fgName, None)
                if tableHf is None:  # new table
                    tableHf = TableHeaderFooter()
                    hfMap[fgName] = tableHf

                tableFieldNames = screen.getFieldGroup(fgName).getFieldNames()
                fieldName = row[1]
                if isNullBlank(fieldName):
                    fieldName = tableFieldNames[rowIndex]

                tableHfRow = TableHeaderFooterRow(fieldName)
                # # The first two columns are 'fg_nm' and 'field_nm', with several columns in the middle as 'header', the second-to-last column as 'footer', and the last column as 'rmk' (rmk is not used for now).
                for i in range(2, len(row) - 2):
                    tableHfRow.headers.append(convertStr2Json(row[i], defaultKey="text"))
                tableHfRow.footer = convertStr2Json(row[-2], defaultKey="text")
                tableHf.fields.append(tableHfRow)
            # validate total fields for each table
            for fgName, tableHf in hfMap.items():
                totalFields = len(tableHf.fields)
                fg = screen.getFieldGroup(fgName)
                totalFgFields = len(fg.fields)
                if totalFields == totalFgFields:
                    # the field name in header-footer table shoulbe the the same as defined in fields table for a field group
                    # if it's empty, then update it
                    for i in range(totalFgFields):
                        tableHfRowField = tableHf.fields[i]
                        fgFieldName = fg.fields[i].name
                        if tableHfRowField.fieldName != fgFieldName:
                            if isNullBlank(tableHfRowField.fieldName):
                                tableHfRowField.fieldName = fgFieldName
                            else:
                                raise IkValidateException('Field [%s] is incorrect in FieldGroups table in [Table Header and Footer for inline tables] for field group [%s]. Please check screen [%s].' % (
                                    tableHfRowField.fieldName, fgName, screen.id))
                elif totalFields < totalFgFields:
                    # the field name is mandatory if total fields is not the same as total fields defined in fields table.
                    fgFieldNames = [field.name for field in fg.fields]
                    for i in range(len(tableHf.fields)):
                        tableHfRowField = tableHf.fields[i]
                        if tableHfRowField.fieldName not in fgFieldNames:
                            raise IkValidateException('Field [%s] is incorrect in FieldGroups table in [Table Header and Footer for inline tables] for field group [%s]. Please check screen [%s].' % (
                                tableHfRowField.fieldName, fgName, screen.id))
                else:
                    raise IkValidateException(
                        'Total fields s incorrect in FieldGroups table in [Table Header and Footer for inline tables] for field group [%s]. Please check screen [%s].' % (fgName, screen.id))
                # update field group's header and footer
                for fgField in fg.fields:
                    tableHfRow = tableHf.getField(fgField.name)
                    if tableHfRow is not None:
                        totalHeaderRows = tableHf.getTotalHeaderRows()
                        headerCaptions = tableHfRow.headers
                        if len(headerCaptions) > 0:
                            if not (len(headerCaptions) == 1 and isNullBlank(headerCaptions[0])):
                                fgField.caption = headerCaptions
                        footer = tableHfRow.footer
                        if not isNullBlank(footer):
                            fgField.footer = footer
        return screen  # end of getScreen

    def initScreenData(self, screen, initDataCallBack=None, globalRequestUrlParameters: dict = None) -> None:
        '''
            globalRequestUrlParameters(dict, option): add parameters to event handller url. E.g. save?a=b&c=d
        '''
        url = None
        url2 = url if url is not None else screen.id.lower()

        recordSetDataMap = {}  # get recordset data once

        def getFieldGroupDataFn(screenFieldGroup):
            recordSetName = screenFieldGroup.recordSetName
            if recordSetName in recordSetDataMap.keys():
                data, dataUrl = recordSetDataMap[recordSetName]
                if data is not None and screenFieldGroup.groupType == SCREEN_FIELD_TYPE_FIELDS \
                    and (type(data) == list or isinstance(data, QuerySet)) \
                        and len(data) > 0:
                    # for master detail
                    # find cursor first if exists
                    screen = screenFieldGroup.parent
                    oneRc = None
                    for rc in data:
                        if isinstance(rc, ikDbModels.Model):
                            if rc.ik_is_cursor():
                                oneRc = rc
                                break
                        elif type(rc) == dict:
                            if rc.get(ikDbModels.MODEL_RECORD_DATA_CURRENT_KEY_NAME, False):
                                oneRc = rc
                                break
                    oneRc = data[0] if oneRc is None else oneRc
                    return oneRc, dataUrl
                return data, dataUrl
            functionName = None if recordSetName is None else self.__getDataCallBackMethod(recordSetName)
            # 2023-06-06 XH for server pagination - start
            if screenFieldGroup.pageType == SCREEN_FIELD_GROUP_PAGE_TYPE_SERVER:
                data = None
                dataUrl = self.__getDataUrl(url2, recordSetName)
            else:
                data, dataUrl = self.__initData(screenFieldGroup, None, screenFieldGroup.recordSetName, functionName, initDataCallBack)
                if dataUrl is not None:
                    dataUrl = self.__getDataUrl(url2, recordSetName)
            # 2023-06-06 XH for server pagination - end
            recordSetDataMap[recordSetName] = (data, dataUrl)
            return data, ikHttpUtils.setQueryParameter(dataUrl, globalRequestUrlParameters)

        def getHtmlDataUrlFn(fieldGroupName):
            return ikHttpUtils.setQueryParameter(self.__getHtmlDataUrl(url2, fieldGroupName), globalRequestUrlParameters)

        def getPDFDataUrlFn(fieldGroupName):
            return ikHttpUtils.setQueryParameter(self.__getDataUrl(url2, fieldGroupName), globalRequestUrlParameters)

        def getFieldWidgetDataFn(field, tableFieldIndex=None):
            self.__getWidgetData(field, initDataCallBack, globalRequestUrlParameters)

        def getScreenHelpFn(screenID):
            return ikHttpUtils.setQueryParameter(self.__getHelpUrl(viewID=screenID), globalRequestUrlParameters)

        return screen._initData(getFieldGroupDataFn, getHtmlDataUrlFn, getPDFDataUrlFn, getFieldWidgetDataFn, getScreenHelpFn)

    def screen2Json(self, screen) -> dict:
        return screen.toJson()

    def __getResultTableEditButtonField(self, fieldGroup) -> ScreenField:
        screen = fieldGroup.parent
        field = ScreenField(parent=fieldGroup)
        field.name = getResultTableEditFieldName(fieldGroup.name)
        field.caption = ''
        field.tooltip = ''
        field.widget = getScreenFieldWidget(SCREEN_FIELD_WIDGET_PLUGIN)
        field.editable = True
        field.visible = True
        field.required = False
        field.dataField = RESULT_TABLE_EDIT_FIELD_RECORD_SET_FIELD_NAME
        field.dataKeyField = None
        field.dataFormat = None
        field.dataValidation = None

        eventHandlerUrl, eventHandlerPrms = self.__getEventHandler(screen,
                                                                   getResultTableEditButonDefaultEventName(field.name)
                                                                   + '(@%s)' % RESULT_TABLE_EDIT_FIELD_RECORD_SET_FIELD_NAME)
        field.eventHandler = eventHandlerUrl
        field.eventHandlerParameter = eventHandlerPrms

        field.style = None
        return field

    def __isScreenExists(self, name) -> bool:
        return name in self.__screenDefinitions.keys()

    def __getBaseUrl(self) -> str:
        '''
            /api/
        '''
        return '/api/'

    def __getDataUrl(self, name, dataName, isAddBaseUrlOnly=False) -> str:
        if dataName is None or len(dataName) == 0:
            return None
        elif dataName.startswith(self.__getBaseUrl()):
            return dataName
        screenId = name.replace('.', '/')
        fn = dataName if isAddBaseUrlOnly else self.__getDataCallBackMethod(dataName)
        url = self.__getBaseUrl() + screenId + '/' + fn
        url = self.__addGetDataFlag(url)
        return url

    def __getHtmlDataUrl(self, name, dataName) -> str:
        if dataName is None or len(dataName) == 0:
            return None
        screenId = name.replace('.', '/')
        fn = 'getHtml' + dataName[0:1].upper() + dataName[1:]
        return self.__getBaseUrl() + screenId + '/' + fn

    def __getFunctionUrl(self, screenId, functionName) -> str:
        return self.__getBaseUrl() + screenId.lower() + '/' + functionName

    def __addGetDataFlag(self, url) -> str:
        '''
         used for data cursor
        '''
        newUrl = url
        newUrl += '?' if '?' not in url else '&'
        newUrl += GET_DATA_URL_FLAG_PARAMETER_NAME + '=' + datetime.strftime(datetime.now(), '%Y%m%d%Y%m%d%H%M%S%f')
        return newUrl

    def __getDataCallBackMethod(self, dataName) -> str:
        return 'get' + dataName[0:1].upper() + dataName[1:]  # change abc to getAbc

    def __getHelpUrl(self, viewID) -> str:
        '''
            return None if viewID is empty
        '''
        if isNullBlank(viewID):
            return None
        return self.__getBaseUrl() + 'help/screen/' + str(viewID.strip())

    def __getEventHandler(self, screen, eventHandler) -> tuple:
        return self.__getEventHandler2(screen.id.lower(), eventHandler)

    def __getEventHandler2(self, name, eventHandler) -> tuple:
        '''
            eventHandler:  Example: "save", "save(table1)", "save(table1, table2)", "save(*)"
                            1) (xxx,xxx): field group name list the handler need to submit to server, it's optional
                            2) (*) means submit the whole screen
                            3) save() or save means no ned to submit anything to server
        '''
        handlerUrl, submitFieldgroupList = None, []
        if eventHandler is not None and len(eventHandler) > 0:
            eventHandler = eventHandler.strip()
            if eventHandler != '':
                if '(' in eventHandler:
                    if ')' not in eventHandler and eventHandler[-1] != ')':
                        raise Exception('Event Handler define is incorect. Please check: %' % eventHandler)
                    i = eventHandler.index('(')
                    handlerUrl = eventHandler[0:i]
                    fieldGroups = eventHandler[i + 1: -1].strip()
                    if fieldGroups != '':
                        for fg in fieldGroups.split(','):
                            fg = fg.strip()
                            if fg != '' and fg not in submitFieldgroupList:
                                submitFieldgroupList.append(fg)
                else:
                    handlerUrl = eventHandler

        handlerUrl = self.__getEventHandlerUrl(name, handlerUrl)
        return handlerUrl, {'fieldGroups': None if handlerUrl is None else submitFieldgroupList}

    def __getEventHandlerUrl(self, name, eventHandler) -> str:
        if eventHandler is None or len(eventHandler) == 0:
            return None
        projectName = name.replace('.', '/')
        return self.__getBaseUrl() + projectName + '/' + eventHandler

    def __toBool(self, yesNo, default=None) -> bool:
        if isNullBlank(yesNo) and default is not None:
            return default
        # YL.ikyo, 2023-04-20 from database will have bool value - start
        elif not isNullBlank(yesNo) and isinstance(yesNo, bool):
            return yesNo
        # YL.ikyo, 2023-04-20 - end
        return yesNo is not None and yesNo.lower() == 'yes'

    def __getWidgetPramsOnly(self, parameters) -> dict:
        prms = {}
        if not isNullBlank(parameters):
            for kv in parameters.splitlines():  # YL.ikyo, 2022-08-05 split by line breaks
                if not isNullBlank(kv):
                    ss = kv.split(':')
                    k = ss[0].strip()
                    v = None
                    if len(ss) > 1:
                        v = ''
                        for j in range(1, len(ss)):
                            if j > 1:
                                v += ':'
                            v += ss[j]
                        v = v.strip()
                    if v and 'value' in v and 'display' in v:
                        v = self.__addQuotes(v)
                    prms[k] = v
        return prms

    def parseWidgetPrams(self, parameters):
        return self.__getWidgetPramsOnly(parameters)

    def __addQuotes(self, s):
        # Add double quotes to keys only when they are not already surrounded by quotes
        s = re.sub(r'(?<!["\'])(\w+)(?=\s*:)', r'"\1"', s)
        # Add double quotes to values only when they are not already surrounded by quotes
        s = re.sub(r'(?<=:)\s*(?<!["\'])(\w+)(?![\'"])\s*(?=[,}])', r' "\1"', s)
        return s

    def __getWidgetData(self, field, initDataCallBack=None, globalRequestUrlParameters: dict = None) -> dict:
        widget = field.widget
        parameters = field.widgetParameter
        if (widget in SCREEN_FIELD_SELECT_WIDGETS or widget == SCREEN_FIELD_WIDGET_LABEL) and parameters is not None and len(parameters) > 0:  # TODO: lower() for old to json method
            self.__updateComboxPrms(field, initDataCallBack, globalRequestUrlParameters)

    def __updateComboxPrms(self, field, initDataCallBack=None, globalRequestUrlParameters: dict = None) -> None:
        '''
            comboxPrms: 
                Example 1:
                    {
                        data: [{"value": "No", "display": "No"}, {"value": "Yes", "display": "Yes"}],
                        values: {"value": "value", "display": "display"}
                    }
                Example 2:
                    {   dataUrl: getAppLeaverType   }
                Example 3:
                    {
                        dataUrl: getCode,
                        values: {"value": "key", "display": "value"}
                    }
                Example 4:
                    {
                        recordset: codeRcs,
                        values: {"value": "key", "display": "value"}
                    }
        '''
        comboxPrms = field.widgetParameter
        screenID = field.parent.parent.id
        comboxData = comboxPrms.get('data', None)
        if comboxData is not None:
            if type(comboxData) == str:
                comboxData = json.loads(comboxData.replace("'", '"'))
        else:
            dataUrl = comboxPrms.get('dataUrl', None)
            recordSetName = comboxPrms.get('recordset', None)
            if not isNullBlank(dataUrl) and not isNullBlank(recordSetName):
                raise IkValidateException(
                    'Parameter [recordset] and [dataUrl] cannot be defined for a combox at the same time. Please check the screen [%s].' % screenID)
            fieldDefine = comboxPrms.get('values', None)  # {'value': 'dbField1', 'display': 'dbField2'}
            fieldDefine = None if isNullBlank(fieldDefine) else (json.loads(fieldDefine.replace("'", '"'))
                                                                 if type(fieldDefine) == str else fieldDefine)

            getDataFunctionName = None
            if not isNullBlank(recordSetName):
                getDataFunctionName = self.__getDataCallBackMethod(recordSetName)
            else:
                getDataFunctionName = dataUrl
            if isNullBlank(getDataFunctionName):
                fgName = field.parent.name
                if field.widget != SCREEN_FIELD_WIDGET_LABEL:
                    logger.warn('Combox [%s].[%s].[%s] data and dataUrl parameter is not found.' % (screenID, fgName, field.name))
            else:
                comboxData, comboxDataUrl = self.__initData(field.parent, field, recordSetName, getDataFunctionName, initDataCallBack)
                if comboxDataUrl is not None and len(comboxDataUrl) > 0 and comboxDataUrl[0] != '/' and screenID[0] != '/':
                    comboxDataUrl = self.__getFunctionUrl(screenID, comboxDataUrl)
                if not isNullBlank(comboxDataUrl):
                    comboxDataUrl = self.__addGetDataFlag(comboxDataUrl)
                if fieldDefine is not None and comboxData is not None and len(comboxData) > 0:
                    if isinstance(comboxData[0], models.Model) or type(comboxData[0]) == dict:
                        # combox data is a dict list. E.g. [{"a": 1, "b":2}, {...}]
                        valueField = fieldDefine.get('value', None)
                        displayField = fieldDefine.get('display', None)
                        if type(comboxData) != list:
                            comboxData = [comboxData]
                        comboxData2 = []
                        if isinstance(comboxData, QuerySet):
                            for rc in comboxData:
                                comboxData2.append({'value': getattr(rc, valueField), 'display': getattr(rc, displayField)})
                        else:
                            for rc in comboxData:
                                if isinstance(comboxData[0], models.Model):
                                    comboxData2.append({'value': getattr(rc, valueField), 'display': getattr(rc, displayField)})
                                else:
                                    comboxData2.append({'value': rc.get(valueField, None), 'display': rc.get(displayField, None)})
                        comboxData = comboxData2
                    else:
                        # combox data is a list. E.g. ['aa', 'bb']
                        pass
                elif fieldDefine is None:
                    if type(comboxData) == list:
                        comboxData2 = []
                        for dataItem in comboxData:
                            if type(dataItem) == dict and len(dataItem) == 2 and 'value' in dataItem.keys() and 'display' in dataItem.keys():
                                comboxData2.append(dataItem)
                            elif type(dataItem) == dict and len(dataItem) == 1:  # {'name': 'abc'}
                                for _key, value in dataItem.items():
                                    comboxData2.append({'value': value, 'display': value})
                            elif type(dataItem) == int or type(dataItem) == float or type(dataItem) == str:
                                comboxData2.append({'value': dataItem, 'display': dataItem})
                            elif type(dataItem) == tuple and len(dataItem) == 1:
                                comboxData2.append({'value': dataItem[0], 'display': dataItem[0]})
                        comboxData = comboxData2
                comboxPrms['data'] = comboxData
                comboxPrms['dataUrl'] = ikHttpUtils.setQueryParameter(comboxDataUrl, globalRequestUrlParameters)
                if isNullBlank(comboxDataUrl):
                    comboxPrms['values'] = None
        onChangeEvent = comboxPrms.get('onChange', None)
        if onChangeEvent is not None and len(onChangeEvent) > 0 and onChangeEvent[0] != '/' and screenID[0] != '/':
            onChangeEvent = self.__getFunctionUrl(screenID, onChangeEvent)
            comboxPrms['onChange'] = ikHttpUtils.setQueryParameter(onChangeEvent, globalRequestUrlParameters)

    def __getStylePrms(self, parameters) -> dict:
        prms = {}
        if not isNullBlank(parameters):
            for kv in parameters.split(";"):
                if not isNullBlank(kv):
                    ss = kv.split(':')
                    if len(ss) > 1:
                        k = ss[0].strip()
                        v = ''
                        for j in range(1, len(ss)):
                            if j > 1:
                                v += ':'
                            v += ss[j]
                        v = v.strip()
                    elif len(ss) == 1:
                        k = 'class'
                        v = ss[0].strip()
                    prms[k] = v
        return prms

    def __getScreenAutoRefreshInfo(self, autoRefreshDfn) -> list:
        '''
            autoRefreshDfn: interval;action

            return interval, action
        '''
        interval = None
        action = None
        if not isNullBlank(autoRefreshDfn):
            # YL, 2024-02-28, Bugfix for auto refresh - start
            autoRefreshPrp = []
            if ";" in autoRefreshDfn:
                autoRefreshPrp = autoRefreshDfn.split(';')
            elif "," in autoRefreshDfn:
                autoRefreshPrp = autoRefreshDfn.split(',')
            if len(autoRefreshPrp) > 0:
                interval = int(autoRefreshPrp[0].strip())
                if len(autoRefreshPrp) > 1:
                    action = autoRefreshPrp[1].strip()
            # YL, 2024-02-28 - end
        return interval, action

    def getAutoRefreshInfo(self, interval=None, action=None) -> str:
        '''
            autoRefreshDfn: interval;action

            return None or interval, action
        '''
        if isNullBlank(interval) and isNullBlank(action):
            return None
        s = ''
        if not isNullBlank(interval):
            s = str(int(str(interval).strip()))
        if not isNullBlank(action):
            s += ', %s' % str(action).strip()
        return s

    def __initData(self, fieldGroup, field, recordsetName, getDataFunctionName, initDataCallBack=None) -> tuple:
        '''
            if field is None then means get the field group data, otherwise get the field data. e.g. combox data.
        '''
        data = None
        dataUrl = None
        useAjax = True
        queryPageType = fieldGroup.pageType

        if initDataCallBack is not None:
            getDataDone, returnData = initDataCallBack(fieldGroup, field, recordsetName, getDataFunctionName)
            if getDataDone:
                data = returnData
            else:
                # get data from recordset
                if recordsetName is not None:
                    data = self._getRecordSetData(fieldGroup, field, recordsetName)
                    useAjax = False
                else:
                    useAjax = True
        if not data or useAjax or queryPageType == SCREEN_FIELD_GROUP_PAGE_TYPE_SERVER:
            dataUrl = getDataFunctionName
        return data, dataUrl

    def _getRecordSetData(self, fieldGroup, field, recordsetName) -> dict:
        screen = fieldGroup.parent
        recordset = screen.getRecordSet(recordsetName)
        # YL.ikyo, 2023-04-23 no use in database - start
        # pageType = SCREEN_FIELD_GROUP_PAGE_TYPE_SERVER if (field is not None or isNullBlank(fieldGroup.pageType)) else fieldGroup.pageType
        # pageSize = None if pageType != SCREEN_FIELD_GROUP_PAGE_TYPE_SERVER else fieldGroup.pageSize
        # if not pageSize:
        #     pageSize = recordset.queryPageSize
        return modelUtils.queryModel(modelNames=recordset.modelNames,
                                     distinct=recordset.distinct,
                                     queryFields=None if (isNullBlank(recordset.queryFields)
                                                          or recordset.queryFields == '*') else recordset.queryFields,
                                     queryWhere=recordset.queryWhere,
                                     orderBy=recordset.queryOrder,
                                     limit=recordset.queryLimit,
                                     # pageSize = pageSize,
                                     page=None)
        # YL.ikyo, 2023-04-23 - end


IkUI = __ScreenManager()


class DialogMessage():
    def __init__(self, title='', message='') -> None:
        self.title = title
        self.message = message

    @property
    def data(self) -> dict:
        '''
            json
        '''
        j = {}
        j['title'] = self.title
        j['content'] = self.message
        return j

    def __str__(self) -> str:
        return 'title=%s,message=%s' % (self.title, self.message)

    def getSuccessResponse(message, title=None) -> ikhttp.IkSccJsonResponse:
        return ikhttp.IkSccJsonResponse(data=DialogMessage(title=title, message=message).data)

    def getErrorResponse(message, title=None) -> ikhttp.IkErrJsonResponse:
        return ikhttp.IkErrJsonResponse(data=DialogMessage(title=title, message=message).data)


'''
def setScreenvisible(screenDfnJson, isvisible) -> None:
    if not isvisible:
        screenDfnJson['fieldGroupTable'].clear()

def setScreenEditable(screenDfnJson, isEditable) -> None:
    screenDfnJson['editable'] = isEditable
'''


def setScreenFieldGroupvisible(screenDfnJson, fieldGroupNames, isvisible) -> None:
    if isvisible:
        return  # do nothing
    if type(fieldGroupNames) == str:
        fieldGroupNames = [fieldGroupNames]
    for fieldGroupName in fieldGroupNames:
        for name, fieldGroup in screenDfnJson.items():
            if type(fieldGroup) == dict and name == fieldGroupName and fieldGroup.get('type', None) is not None:
                if not isvisible:
                    del screenDfnJson[name]
                    break


def isScreenFieldGroupvisible(screenDfnJson, fieldGroupName) -> bool:
    if fieldGroupName in screenDfnJson.keys():
        fg = screenDfnJson[fieldGroupName]
        return fg.get('visible', True)
    return False


def setScreenFieldGroupEditable(screenDfnJson, fieldGroupNames, isEditable) -> None:
    if type(fieldGroupNames) == str:
        fieldGroupNames = [fieldGroupNames]
    for fieldGroupName in fieldGroupNames:
        for name, fieldGroup in screenDfnJson.items():
            if type(fieldGroup) == dict and name == fieldGroupName and fieldGroup.get('type', None) is not None:
                fieldGroup['editable'] = isEditable
                break


def setScreenFieldGroupEnable(screenDfnJson, fieldGroupNames, isInsertable, isDeletable, isEditable) -> None:
    if type(fieldGroupNames) == str:
        fieldGroupNames = [fieldGroupNames]
    for fieldGroupName in fieldGroupNames:
        for name, fieldGroup in screenDfnJson.items():
            if type(fieldGroup) == dict and name == fieldGroupName and fieldGroup.get('type', None) is not None:
                fieldGroup['insertable'] = isInsertable
                fieldGroup['deletable'] = isDeletable
                fieldGroup['editable'] = isEditable
                break


def isScreenFieldGroupEditable(screenDfnJson, fieldGroupName) -> bool:
    if fieldGroupName in screenDfnJson.keys():
        fg = screenDfnJson[fieldGroupName]
        return fg.get('editable', True)
    return False

# YL.ikyo, 2022-12-02 - start
# set field visible


def setScreenFieldsvisible(screenDfnJson, fieldGroupName, fieldNames, isvisible) -> None:
    if type(fieldNames) == str:
        fieldNames = [fieldNames]
    for fieldName in fieldNames:
        for name, fieldGroup in screenDfnJson.items():
            if type(fieldGroup) == dict and name == fieldGroupName and fieldGroup.get('type', None) == SCREEN_FIELD_TYPE_FIELDS:
                fields = fieldGroup.get('fields', [])
                for i in range(len(fields)):
                    field = fields[i]
                    if field.get('name', None) == fieldName:
                        if not isvisible:
                            fields.pop(i)
                            break

# update field group caption


def setScreenFieldGroupCaption(screenDfnJson, fieldGroupName, value) -> None:
    if fieldGroupName in screenDfnJson.keys():
        fg = screenDfnJson[fieldGroupName]
        fg['caption'] = value

# update field caption


def setScreenFieldGroupFieldCaption(screenDfnJson, fieldGroupName, fieldName, value) -> None:
    for name, fieldGroup in screenDfnJson.items():
        if type(fieldGroup) == dict and name == fieldGroupName:  # and fieldGroup.get('type', None) == SCREEN_FIELD_TYPE_FIELDS:
            fields = fieldGroup.get('fields', [])
            for i in range(len(fields)):
                field = fields[i]
                if field.get('name', None) == fieldName:
                    field['caption'] = value
                    break

# update html field group data


def setScreenHtmlFgValue(screenDfnJson, fieldGroupName, value) -> None:
    if fieldGroupName in screenDfnJson.keys():
        fg = screenDfnJson[fieldGroupName]
        if type(fg) == dict and fg.get('name', None) == fieldGroupName and fg.get('type', None).lower() == 'html':
            fg['data'] = value

# YL.ikyo, 2022-12-02 - end


def setScreenButtonEnable(screenDfnJson, toolbarName, buttonNames, isEnable) -> None:
    if type(buttonNames) == str:
        buttonNames = [buttonNames]
    for buttonName in buttonNames:
        for name, fieldGroup in screenDfnJson.items():
            if type(fieldGroup) == dict and name == toolbarName and fieldGroup.get('type', None) == SCREEN_FIELD_TYPE_ICON_BAR:
                icons = fieldGroup.get('icons', [])
                for i in range(len(icons)):
                    icon = icons[i]
                    if icon.get('name', None) == buttonName:
                        icon['enable'] = isEnable


def isScreenButtonEnable(screenDfnJson, toolbarName, buttonName) -> bool:
    if toolbarName in screenDfnJson.keys():
        toolbar = screenDfnJson[toolbarName]
        icons = toolbar.get('icons', [])
        for i in range(len(icons)):
            icon = icons[i]
            if icon.get('name', None) == buttonName:
                return icon.get('enable', True)
    return False


def setScreenButtonvisible(screenDfnJson, toolbarName, buttonNames, isvisible) -> None:
    if type(buttonNames) == str:
        buttonNames = [buttonNames]
    for buttonName in buttonNames:
        for name, fieldGroup in screenDfnJson.items():
            if type(fieldGroup) == dict and name == toolbarName and fieldGroup.get('type', None) == SCREEN_FIELD_TYPE_ICON_BAR:
                icons = fieldGroup.get('icons', [])
                for i in range(len(icons)):
                    icon = icons[i]
                    if icon.get('name', None) == buttonName:
                        if not isvisible:
                            icons.pop(i)
                            break


def setScreenSchFgvisible(screenDfnJson, schFgName, schNames, isvisible) -> None:
    if type(schNames) == str:
        schNames = [schNames]
    for schName in schNames:
        for name, fieldGroup in screenDfnJson.items():
            if type(fieldGroup) == dict and name == schFgName and fieldGroup.get('type', None) == SCREEN_FIELD_TYPE_SEARCH:
                fields = fieldGroup.get('fields', [])
                for i in range(len(fields)):
                    field = fields[i]
                    if field.get('name', None) == schName:
                        if not isvisible:
                            fields.pop(i)
                            break


def setScreenComboboxRequire(screenDfnJson, FgName, schNames, isRequired) -> None:
    if type(schNames) == str:
        schNames = [schNames]
    for schName in schNames:
        for name, fieldGroup in screenDfnJson.items():
            if type(fieldGroup) == dict and name == FgName:  # and fieldGroup.get('type', None) == SCREEN_FIELD_TYPE_SEARCH: YL.ikyo, 2022-12-13, More than just searchFg
                fields = fieldGroup.get('fields', [])
                for i in range(len(fields)):
                    field = fields[i]
                    if field.get('name', None) == schName:
                        field['required'] = isRequired


def setScreenTableFgFieldDict(screenDfnJson, tableFgName, fieldName, key, value) -> None:
    for name, fieldGroup in screenDfnJson.items():
        if type(fieldGroup) == dict and name == tableFgName and fieldGroup.get('type', None) == SCREEN_FIELD_TYPE_TABLE:
            fields = fieldGroup.get('fields', [])
            for i in range(len(fields)):
                field = fields[i]
                if field.get('name', None) == fieldName:
                    field[key] = value
