import datetime
import decimal
import json
import logging
import os
from enum import Enum
from pathlib import Path
from urllib.parse import quote

import core.db.model as ikModels
import core.utils.modelUtils as modelUtils
import django.core.files.uploadedfile as djangoUploadedfile
from core.utils.langUtils import isNotNullBlank, isNullBlank
from django.core.exceptions import FieldDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse
from django.http.response import JsonResponse, StreamingHttpResponse

from .code import IkCode, MessageType
from .exception import IkMessageException, IkValidateException

logger = logging.getLogger('backend')


def isSupportSession(request) -> bool:
    '''
        return False if request from "http://localhost:3000"
    '''
    httpOrigin = request.META.get('HTTP_ORIGIN', None)
    httpReferer = request.META.get('HTTP_REFERER', None)
    isReactDev = httpOrigin is not None and httpOrigin.startswith('http://localhost:3000') \
        or httpReferer is not None and httpReferer.startswith('http://localhost:3000/')
    return not isReactDev


def getClientIP(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')  # Use proxy?
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # get IP from proxy
    else:
        ip = request.META.get('REMOTE_ADDR')  # get IP directly
    return ip


class RECORD_SET(Enum):
    STATUS_NO_CHANGE = ''
    STATUS_NEW = '+'
    STATUS_DELETE = '-'
    STATUS_UPDATE = '~'
    ATTR = 'attr'
    ATTR_DATA = 'data'
    ID = 'id'
    SELECTED = 'true'


class IkResponseStaticResource:

    def __init__(self, resource, properties=None) -> None:
        self.__resource = resource
        self.__properties = properties

    def toJson(self) -> dict:
        '''
            return {'resource': 'abc.js', 'properties': {'id': 'efg', 'title': 'description'}}
        '''
        return {'resource': self.__resource, 'properties': self.__properties}

    def __str__(self) -> str:
        return self.__resource


class IkResponseForwarder:

    def __init__(self, url, parameters=None, httpMethod='get') -> None:
        '''
            parameters: parameter dict
            httpMethod: get/post, default is get, None means get.
        '''
        self.url = url
        self.parameters = parameters
        self.httpMethod = httpMethod

    def toJson(self) -> dict:
        j = {}
        j['url'] = self.url
        if self.parameters is not None:
            j['parameters'] = self.parameters
        if self.httpMethod is not None:
            j['method'] = self.httpMethod
        return j


class IkJsonResponse(JsonResponse):

    def __init__(self, code=IkCode.I0, message=None, messageType=None, data=None, forwarder=None, encoder=DjangoJSONEncoder, safe=False, json_dumps_params=None, **kwargs):
        self.__code = code
        self.__data = data
        self.__messages = []
        self.__forwarder = forwarder
        self.__encoder = encoder
        if json_dumps_params is None:
            json_dumps_params = {}
        self.__json_dumps_params = json_dumps_params
        if not isNullBlank(messageType) or not isNullBlank(message):
            if messageType is None:
                messageType = MessageType.INFO
            self.addMessage(messageType, message)
        self.__staticResources = []
        super().__init__(self.__toJson(), encoder, safe, json_dumps_params, *kwargs)

    def addMessage(self, messageType: MessageType, message: str) -> None:
        self.__messages.append({'type': messageType.value if type(messageType) ==
                               MessageType else messageType, 'message': ('' if message is None else message)})

    # def addMessageDebug(self, message: str) -> None:
    #     self.addMessage(MessageType.DEBUG, message=message)

    # def addMessageInfo(self, message: str) -> None:
    #     self.addMessage(MessageType.INFO, message=message)

    # def addMessageError(self, message: str) -> None:
    #     self.addMessage(MessageType.ERROR, message=message)

    # def addMessageWarn(self, message: str) -> None:
    #     self.addMessage(MessageType.WARNING, message=message)

    # def addMessageFatal(self, message: str) -> None:
    #     self.addMessage(MessageType.FATAL, message=message)

    # def addMessageException(self, exception: object) -> None:
    #     self.addMessage(MessageType.EXCEPTION, message=exception)

    def addStaticResource(self, resource) -> None:
        '''
            resource: django_backend/core/core/http.py.IkResponseStaticResource class
        '''
        if resource:
            if isinstance(resource, IkResponseStaticResource):
                self.__staticResources.append(resource)
            elif type(resource) == 'str':
                self.__staticResources.append(IkResponseStaticResource(resource=resource))
            else:
                raise IkValidateException('Unsupport resource type: %s' % type(resource))

    def updateContent(self):
        # call JsonResponse method
        self.content = json.dumps(self.__toJson(), cls=self.__encoder, **self.__json_dumps_params).encode()

    @property
    def code(self) -> int:
        return self.__code

    def isSuccess(self) -> bool:
        return self.__code == IkCode.I1

    @property
    def messages(self) -> list:
        return self.__messages

    @property
    def data(self) -> object:
        return self.__data

    @property
    def forwarder(self) -> dict:
        return self.__forwarder

    def getJsonData(self) -> dict:
        data2 = self.__data
        return self.__getJsonData(data2)

    def __getJsonData(self, data2):
        if data2 is not None:
            if isinstance(data2, QuerySet):
                data2 = self.__getDataSetValues(data2)
            elif isinstance(data2, models.Model):
                data2 = self.__model2Json(data2)
            # YL.ikyo, 2023-03-07 bugfix, can't serialize when view get screen - start
            elif isinstance(data2, datetime.datetime):
                data2 = data2.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(data2, datetime.date):
                data2 = data2.strftime("%Y-%m-%d")
            elif isinstance(data2, datetime.time):
                data2 = data2.strftime("%H:%M:%S")
            elif isinstance(data2, decimal.Decimal):
                data2 = str(data2)
            # YL.ikyo, 2023-03-07 - end
            elif type(data2) == list:
                data3 = []
                for item in data2:
                    data3.append(self.__getJsonData(item))
                data2 = data3
            elif type(data2) == dict:
                data3 = {}
                for key, value in data2.items():
                    data3[key] = self.__getJsonData(value)
                data2 = data3
            elif isinstance(data2, ikModels.DummyModel):
                data2 = data2.getJson()
        return data2

    def __model2Json(self, r) -> dict:
        # YL.ikyo, 2023-03-29 bugfix, can't serialize when view get screen(return data is a querySet or model) - start
        for field in r._meta.get_fields():
            try:
                if isinstance(field, models.Field) and not isinstance(field, models.ForeignKey):
                    key = field.name
                    value = r.__dict__[field.name]
                    if isinstance(value, datetime.datetime):
                        r.__dict__[field.name] = value.strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(value, datetime.date):
                        r.__dict__[field.name] = value.strftime("%Y-%m-%d")
                    elif isinstance(value, datetime.time):
                        r.__dict__[field.name] = value.strftime("%H:%M:%S")
                    elif isinstance(value, decimal.Decimal):
                        r.__dict__[field.name] = str(value)
            except Exception as e:
                # this is not a model field or field is not a normal field. ignore it
                logger.error(str(e))
                continue
        # YL.ikyo, 2023-03-29 - end
        d = r.toJson()
        if r._meta.pk is not None and r._meta.pk.name is not None:
            primaryKey = r._meta.pk.name
            d['__PK_'] = primaryKey
        return d

    def __getDataSetValues(self, dataset) -> list:
        rs = []
        for r in dataset:
            if type(r) == dict:  # model.values(a,b)
                rs.append(r)
            elif type(r) == list:  # model.to_list()
                rs.append(r)
            else:
                rs.append(self.__model2Json(r))
        return rs

    def toJson(self) -> dict:
        return self.__toJson()

    def __toJson(self) -> dict:
        data = self.getJsonData()
        jsonData = {}
        jsonData['code'] = self.__code
        jsonData['messages'] = self.__messages
        if self.__forwarder is not None:
            jsonData['href'] = self.__forwarder.toJson()
        if len(self.__staticResources):
            jsonData['resources'] = [r.toJson() for r in self.__staticResources]
        jsonData['data'] = data

        if isinstance(data, dict) and 'logLevel' in data:
            jsonData['logLevel'] = data['logLevel']
            del data['logLevel']
        return jsonData

    def __str__(self):
        return str(self.__toJson())


class IkSccJsonResponse(IkJsonResponse):

    def __init__(self, code=IkCode.I1, message=None, messageType=None, data=None, forwarder=None, encoder=DjangoJSONEncoder, safe=False, json_dumps_params=None, **kwargs):
        super().__init__(code, message, messageType, data, forwarder, encoder, safe, json_dumps_params, *kwargs)


class IkErrJsonResponse(IkJsonResponse):

    def __init__(self,
                 code=IkCode.I0,
                 message=None,
                 messageType=MessageType.ERROR,
                 data=None,
                 forwarder=None,
                 encoder=DjangoJSONEncoder,
                 safe=False,
                 json_dumps_params=None,
                 **kwargs):
        super().__init__(code, message, messageType, data, forwarder, encoder, safe, json_dumps_params, *kwargs)


class IkSysErrJsonResponse(IkJsonResponse):

    def __init__(self,
                 code=IkCode.I0,
                 message='System error! Please contact with administrator for help.',
                 messageType=MessageType.EXCEPTION,
                 data=None,
                 forwarder=None,
                 encoder=DjangoJSONEncoder,
                 safe=False,
                 json_dumps_params=None,
                 **kwargs):
        super().__init__(code, message, messageType, data, forwarder, encoder, safe, json_dumps_params, *kwargs)


class IkRequestData(dict):

    def getSelectedTableIndexes(self, name) -> list:
        '''
            return ('__%s_selected_indexes' % name) for table group, if no found, then return None
        '''
        return super().get('__%s_selected_indexes' % name, None)

    def getSelectedTableRows(self, name) -> list:
        '''
            return ('__%s_selected_rcs' % name) for table group, if no found, then return None
        '''
        return super().get('__%s_selected_rcs' % name, None)

    def setRequest(self, request) -> None:
        self.__request = request

    def getRequest(self) -> HttpRequest:
        return self.__request

    def get2(self, name, default=None, dataTypes=None, recordToList=False, recordToListIgnoreFields=None) -> list:
        '''
            This method is call get method first, then parse data to specified type. This is only used for list data.

            default: default value

            dataTypes: data format by column. Format: 1) list: e.g. ['int', 'float', ...] 2). dict. E.g. {0: 'int', 3:'float'}. 
            Data type can be string or a type name. E.g. 'float', float
            recordToList: used for dict list
            recordToListIgnoreFields: used for recordToList
        '''
        data = self.get(name, default)
        if dataTypes is not None and (type(dataTypes) == list or type(dataTypes) == dict) and len(dataTypes) > 0 \
                and data is not None and type(data) == list:
            for r in data:
                if type(r) == list:
                    if type(dataTypes) == list:
                        for i in range(len(r)):
                            dataType = None if i >= len(dataTypes) else dataTypes[i]
                            if not isNullBlank(dataType):
                                r[i] = self.__parseData(r[i], dataType)
                    else:
                        # dict
                        for i, dataType in dataTypes.items():
                            if i < len(r) and not isNullBlank(dataType):
                                r[i] = self.__parseData(r[i], dataType)
                elif isinstance(r, dict):
                    if type(dataTypes) == list:
                        i = -1
                        for name, value in r.items():
                            i += 1
                            dataType = None if i >= len(dataTypes) else dataTypes[i]
                            if not isNullBlank(dataType):
                                r[name] = self.__parseData(r[name], dataType)
                    else:
                        # dict
                        for name, dataType in dataTypes.items():
                            if not isNullBlank(dataType) and name in r.keys():
                                r[name] = self.__parseData(r[name], dataType)
        if recordToList:
            data2 = []
            for r in data:
                r2 = []
                for k, v in r.items():
                    if recordToListIgnoreFields is not None and k in recordToListIgnoreFields:
                        continue
                    r2.append(v)
                data2.append(r2)
            data = data2
        return data

    def __parseData(self, value, dataType) -> any:
        if value is None:
            return value
        v = value
        try:
            if not isNullBlank(dataType):
                if dataType == 'int' or dataType == int:
                    v = int(v)
                elif dataType == 'float' or dataType == float:
                    v = float(v)
        except:
            logger.error('parse [%s] to %s failed.' % (value, dataType))
        return v

    def getFile(self, parameterName) -> (djangoUploadedfile.UploadedFile | None):
        files = self.getFiles(parameterName)
        return files[0] if files and len(files) > 0 else None

    def getFiles(self, parameterName) -> (list | None):
        if parameterName in self.__request.FILES.keys():
            files = self.__request.FILES.getlist(parameterName)
            return files
        else:
            # TODO: temporary solution, see react SimpleFg.tsx (2022-11-03, Li)
            files = []
            for key, value in self.__request.FILES.items():
                if key.startswith(parameterName + '_FILES_'):
                    files.append(value)
            return files


def GetRequestData(request, parameterModelMap={}, screen=None, initDataFromDatabase=True) -> IkRequestData:
    data0 = {}
    try:
        queryParams = request.query_params
        requestBodyStr = request.body.decode()
        data0 = json.loads(requestBodyStr)
    except Exception as e:
        # TODO: UnicodeDecodeError: 'utf-8' codec can't decode byte 0x96 in position 524: invalid start byte
        # When request.FILES contains file
        for key, value in request.data.items():
            data0[key] = value
    data = IkRequestData()
    data.setRequest(request)
    for key, value in data0.items():
        data[key] = value
    dataAdditions = {}
    for key, value in data.items():
        if value is not None and type(value) == str and len(value) > 0 and value[0] == '{' and value[-1] == '}':
            # json
            value = json.loads(value)
            data[key] = value

        if type(value) == dict and len(value.keys()) == 2 and 'attr' in value.keys() and 'data' in value.keys():
            # its a table
            attr = value['attr']
            tableData = value['data']
            modelRecords = []
            tableDataIndex = -1
            selectedDataIndexes = []
            for r in tableData:
                tableDataIndex += 1
                # status column
                if r[0] == ' ':
                    r[0] = RECORD_SET.STATUS_NEW.value
                elif r[0] == RECORD_SET.SELECTED.value:
                    r[0] = True  # checkbox
                    selectedDataIndexes.append(tableDataIndex)
                # id column
                if r[1] == '':
                    r[1] = None
                elif r[1] is not None:
                    r[1] = int(r[1])

            # the dataset maybe is empty (e.g. dummy recordsets)
            if key not in parameterModelMap.keys() or parameterModelMap[key] is None:
                # return array list[[xxx,xxxx,...], [xxxx,xxxx,...]...]
                rows = []
                for r in tableData:
                    # remove key and status columns
                    rows.append(r)
                data[key] = rows
            else:
                modelClassName = parameterModelMap[key]
                if modelClassName == (ikModels.DummyModel.__module__ + '.' + ikModels.DummyModel.__name__):
                    rows = []
                    for r in tableData:
                        clientStatus = ikModels.ModelRecordStatus.RETRIEVE
                        isSelected = None
                        if r[0] == RECORD_SET.STATUS_NEW.value:
                            clientStatus = ikModels.ModelRecordStatus.NEW
                        elif r[0] == RECORD_SET.STATUS_DELETE.value:
                            clientStatus = ikModels.ModelRecordStatus.DELETE
                        elif r[0] == RECORD_SET.STATUS_UPDATE.value:
                            clientStatus = ikModels.ModelRecordStatus.MODIFIED
                        elif r[0] == True or r[0] == False:
                            isSelected = r[0]
                        elif not isNullBlank(r[0]) and r[0] != RECORD_SET.STATUS_NO_CHANGE.value:
                            raise IkValidateException('Unknown record status: %s' % r[0])
                        id = None if isNullBlank(r[1]) else int(r[1])
                        rc = ikModels.DummyModel(status=clientStatus)
                        rc['id'] = id  # put the id field on the first, user may overwrite the id field
                        for i in range(2, len(attr)):
                            rc[attr[i]] = r[i]
                        if isSelected is not None:
                            rc.ik_set_selected(selected=isSelected)
                        rows.append(rc)
                    data[key] = rows
                else:
                    modelClass = modelUtils.getModelClass(modelClassName)
                    primaryKey = modelClass._meta.pk.name
                    dbFieldNamesAttrs = attr[2:]
                    for r in tableData:
                        isNew = r[0] == RECORD_SET.STATUS_NEW.value
                        isDelete = r[0] == RECORD_SET.STATUS_DELETE.value
                        isUpdated = r[0] == RECORD_SET.STATUS_UPDATE.value
                        id = None if isNullBlank(r[1]) else int(r[1])
                        if isDelete:
                            modelInstance = modelClass()
                            if isNotNullBlank(primaryKey) and isNotNullBlank(id):
                                filterDict = {primaryKey: id}
                                modelInstance = modelClass.objects.filter(**filterDict).first()
                            if modelInstance is None:
                                raise IkValidateException('This record has been deleted. ID=%s' % id)
                            modelInstance.ik_set_status_delete()
                            modelRecords.append(modelInstance)
                        elif isUpdated or isNew:
                            rowValues = r[2:]
                            rowValuesDict = {}
                            for i in range(len(dbFieldNamesAttrs)):
                                rowValuesDict[dbFieldNamesAttrs[i]] = rowValues[i]
                            rowValuesDict[primaryKey] = id
                            r = __GetRequestData_oneRecord(screen, parameterModelMap, key, rowValuesDict, initDataFromDatabase, True)
                            if r is None:
                                raise IkValidateException('This record has been deleted. ID=%s' % id)
                            modelRecords.append(r)
                        else:
                            # no update
                            modelInstance = modelClass()
                            if isNotNullBlank(primaryKey) and isNotNullBlank(id):
                                filterDict = {primaryKey: id}
                                modelInstance = modelClass.objects.filter(**filterDict).first()
                            modelRecords.append(modelInstance)
                    # unique validate
                    if not issubclass(modelClass, ikModels.DummyModel):
                        dbFieldNamesAttrsIndex = -1
                        for fieldName in dbFieldNamesAttrs:
                            dbFieldNamesAttrsIndex += 1
                            screenFieldGroup = screen.getFieldGroup(key)
                            screenGroupField = screenFieldGroup.fields[dbFieldNamesAttrsIndex]

                            modelField = None
                            try:
                                modelField = modelClass._meta.get_field(fieldName)
                            except FieldDoesNotExist as e:
                                # this is not a model field. ignore it
                                continue
                            if modelField.unique or screenGroupField.unique:
                                uniqueValues = []
                                for r in modelRecords:
                                    value = getattr(r, fieldName)
                                    if value in uniqueValues:
                                        raise IkValidateException('Column [%s] is unique. Please check value [%s].' %
                                                                  (screenGroupField.caption, value))
                                    uniqueValues.append(value)
                    data[key] = modelRecords
                    dataAdditions['__%s_selected_indexes' % key] = selectedDataIndexes
            selectedRcs = []
            if len(selectedDataIndexes) > 0:
                rowList = data[key]
                for i in selectedDataIndexes:
                    selectedRcs.append(rowList[i])
            dataAdditions['__%s_selected_rcs' % key] = selectedRcs
        elif screen is not None and screen.editable and type(value) == dict and 'COMBOX_CHANGE_EVENT' not in queryParams\
                and parameterModelMap is not None and key in parameterModelMap.keys():
            r = __GetRequestData_oneRecord(screen, parameterModelMap, key, value, initDataFromDatabase, False)
            if r is not None:
                data[key] = r
    for key, value in dataAdditions.items():
        data[key] = value
    return data


def __GetRequestData_oneRecord(screen, parameterModelMap, name, values, initDataFromDatabase, isTable):
    modelClassName = parameterModelMap[name]
    if modelClassName is None:
        return None
    screenFieldGroup = screen.getFieldGroup(name)
    if screenFieldGroup is None:
        return screenFieldGroup

    modelClass = modelUtils.getModelClass(modelClassName)
    # XH 2023-04-21  Data from tables using DummyModel is not processed and directly returns the original data passed from the front end.
    if issubclass(modelClass, ikModels.DummyModel):
        return values
    primaryKeyName = modelClass._meta.pk.name  # E.g. 'id', 'menu_id'

    modelInstance = None
    isNewModelRecord = True
    if initDataFromDatabase and primaryKeyName in values.keys() and not isNullBlank(values[primaryKeyName]) \
            and int(values[primaryKeyName]) > 0:
        id = int(values[primaryKeyName])
        filterDict = {primaryKeyName: id}
        modelInstance = modelClass.objects.filter(**filterDict).first()
        if modelInstance is None:
            raise IkValidateException('This record has been deleted. ID=%s' % id)
        isNewModelRecord = False
    else:
        modelInstance = modelClass()

    if type(values) == dict and primaryKeyName in values.keys() and isNullBlank(values[primaryKeyName]):
        values[primaryKeyName] = None

    hasIDField = False
    for field in screenFieldGroup.fields:
        # if field.dataField is not None and field.visible and field.editable and field.widget.lower() in ('textbox', 'combobox', 'checkBox'.lower(), 'datebox', 'textarea'): # TODO: get from somewhere
        if field.dataField is not None and field.visible and field.widget.lower() in ('label', 'textbox', 'combobox', 'checkBox'.lower(), 'datebox', 'textarea', 'password'):
            if field.dataField.startswith('_'):  # read only fields. E.g. _cre_usr_nm, _mod_usr_nm
                continue  # ignore
            elif '__' in field.dataField:  # foreign key fields. E.g. foreign key field user. access to user.name: user__usr_nm
                continue  # ignore

            newValue = values.get(field.dataField)
            try:
                modelField = modelClass._meta.get_field(field.dataField)
                if modelField is None:
                    raise IkValidateException('%s [%s] does not exist in model [%s].'
                                              % ('Column' if isTable else 'Field', field.dataField, modelClassName))
                # TODO: validate, e.g. data type, require, mandatory
                isDBNullable = modelField.blank or modelField.null
                isDBUnique = modelField.unique
                if newValue == '':
                    newValue = None

                fieldDataType = modelField.get_internal_type()
                if fieldDataType == 'FloatField':
                    try:
                        newValue = __float2(newValue)
                    except:
                        raise IkValidateException('%s [%s] should be a numeric.'
                                                  % ('Column' if isTable else 'Field', field.caption))
                elif fieldDataType == 'IntegerField' or fieldDataType == 'SmallIntegerField':
                    try:
                        newValue = __int2(newValue)
                    except:
                        raise IkValidateException('%s [%s] should be an integer.'
                                                  % ('Column' if isTable else 'Field', field.caption))
                elif fieldDataType == 'BigIntegerField':
                    try:
                        newValue = __BigInteger2(newValue)
                    except:
                        raise IkValidateException('%s [%s] should be an integer.'
                                                  % ('Column' if isTable else 'Field', field.caption))
                elif fieldDataType == 'BooleanField':
                    if type(newValue) != bool:
                        if isNullBlank(newValue):
                            newValue = None
                        elif newValue == 'true':
                            newValue = True
                        elif newValue == 'false':
                            newValue = False
                        else:
                            raise IkValidateException('%s [%s] should be a bool.'
                                                      % ('Column' if isTable else 'Field', field.caption))
                elif fieldDataType == 'DateTimeField':
                    if newValue is not None and type(newValue) != datetime.datetime:
                        newValue = datetime.datetime.strptime(newValue, "%Y-%m-%d %H:%M:%S")
                elif fieldDataType == 'DateField':
                    if newValue is not None and type(newValue) != datetime.datetime.date:
                        newValue = datetime.datetime.strptime(newValue, "%Y-%m-%d").date()
                elif fieldDataType == 'TimeField':
                    if newValue is not None and type(newValue) != datetime.datetime.time:
                        newValue = datetime.datetime.strptime(newValue, "%H:%M:%S").time()

                # simple validation # TODO: max value checking, min value checking, string length checking
                if not isDBNullable and isNullBlank(newValue) and field.dataField != 'cre_dt' and field.dataField != 'cre_usr_id':
                    raise IkValidateException('%s [%s] is mandatory.'
                                              % ('Column' if isTable else 'Field', field.caption))
                elif modelField.max_length is not None and newValue is not None and len(newValue) > modelField.max_length:
                    raise IkValidateException('%s [%s] max length is %s. Please check.'
                                              % ('Column' if isTable else 'Field', field.caption, modelField.max_length))
                originalFieldValue = getattr(modelInstance, field.dataField)

                if field.widget == 'checkBox':
                    if type(newValue) != bool:
                        if newValue == 'true':
                            newValue = True
                        elif newValue == 'false':
                            newValue = False
                        elif not isNullBlank(newValue):
                            logger.error('System error, checkbox value is incorrect. The current value is %s' % newValue)
                            raise IkValidateException('System error: checkbox value is incorrect.')
                        else:
                            newValue = None
                    if newValue is None and (not modelField.blank or not modelField.null):
                        newValue = False

                if not isNewModelRecord:
                    if newValue != originalFieldValue:
                        # value changed
                        setattr(modelInstance, field.dataField, newValue)
                        if isinstance(modelInstance, ikModels.Model):
                            modelInstance.ik_set_status_modified()
                else:
                    setattr(modelInstance, field.dataField, newValue)
                if not hasIDField and field.dataField == primaryKeyName:
                    hasIDField = True
            except FieldDoesNotExist as fdne:
                logger.debug(fdne, exc_info=True)
                if hasattr(modelInstance, field.dataField):  # no database field
                    if field.widget.lower() == 'CheckBox'.lower():
                        if newValue == 'true':
                            newValue = True
                        elif newValue == 'false':
                            newValue = False
                        elif newValue == '':
                            newValue = None
                    logger.debug('model [%s] field [%s] does not exist, then try class property...' % (modelClassName, field.dataField))
                    setattr(modelInstance, field.dataField, newValue)
                else:
                    raise IkValidateException('%s [%s] does not exist in model [%s].'
                                              % ('Column' if isTable else 'Field', field.dataField, modelClassName))
    if isNewModelRecord and not hasIDField and primaryKeyName in values.keys():
        id = values.get(primaryKeyName, None)
        setattr(modelInstance, primaryKeyName, int(id) if id is not None else None)
    return modelInstance


def __float2(s):
    if s is None or type(s) != str:
        return s
    s = s.strip()
    return float(s) if s != '' else None


def __int2(s):
    if s is None or type(s) != str:
        return s
    s = s.strip()
    return int(s) if s != '' else None


def __BigInteger2(s):
    if s is None or type(s) != str:
        return s
    s = s.strip()
    # return BigInteger(s) if s != '' else None
    # TODO: BigInteger field
    return int(s) if s != '' else None


def responseFile(filePath, filename=None, params=None) -> StreamingHttpResponse:
    '''
        download file
        filename: download file's name from browser. default is filename in server side.
    '''
    p = Path(filePath)
    if not p.is_file():
        logger.error('File is not found: %s' % p.absolute())
        raise IkMessageException('File is not found.')
    filename = filename if filename is not None else p.name
    fileType = '' if p.suffix is None else p.suffix[1:].lower()

    def fileIterator(filePath, chunk_size=512):
        with open(filePath, mode='rb') as f:
            while True:
                c = f.read(chunk_size)
                if c:
                    yield c
                else:
                    break

    response = StreamingHttpResponse(fileIterator(p))
    response['Content-Type'] = 'application/' + fileType
    response['Content-Length'] = os.path.getsize(p)
    response['Access-Control-Expose-Headers'] = 'Content-Disposition'  # to allow react to read head "Content-Disposition"
    response['Content-Disposition'] = 'attachment; filename=%s' % quote(filename)
    response['Custom-Param'] = json.dumps(params)  # YL.ikyo, 2023-10-19 for control pdf viewer download, eg.param = {'isOperate': True, 'file:': 'test'}
    return response


def responseImage(imagePath):
    '''
        download image
    '''
    p = Path(imagePath)
    if not p.is_file():
        raise Exception('File is not found.')
    fileType = '' if p.suffix is None else p.suffix[1:].lower()

    data = None
    with open(imagePath, 'rb') as f:
        data = f.read()

    return HttpResponse(data, content_type='image/' + fileType)
