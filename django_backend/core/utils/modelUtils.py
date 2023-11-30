import json
import logging
from datetime import datetime
from importlib import import_module

from core.core.exception import IkValidateException
from core.db.model import IDModel, Model
from django.core import serializers
from django.db.models import QuerySet
from iktools import IkConfig

from .langUtils import isNullBlank

logger = logging.getLogger('backend')


def updateSystemFields(modelRc, usrId, date=None):
    if date is None:
        date = datetime.now()
    if type(modelRc) is list:
        for rc in modelRc:
            __updateSystemFields(rc, usrId, date)
    else:
        __updateSystemFields(modelRc, usrId, date)


def __updateSystemFields(modelRc, usrId, date=None):
    # if date is None:
    #     date = datetime.now()
    if modelRc.cre_usr_id is None:  # new
        # modelRc.cre_usr_id = usrId
        # modelRc.cre_dt = date
        pass
    else:  # update
        # modelRc.mod_usr_id = usrId
        # modelRc.mod_dt = date
        modelRc.version_no += 1


def model2Fields(modelRc):
    if type(modelRc) == list:
        rs = []
        for r in modelRc:
            rs.append(__model2Fields(r))
        return rs
    else:
        return __model2Fields(modelRc)


def __model2Fields(modelRc) -> dict:
    fields = modelRc['fields']
    fields['id'] = modelRc['pk']  # TODO: get primary key field
    return fields


def redcordsets2List(recordsets, fields, removeDumpItemFields=None) -> list:
    data = []
    if recordsets is not None:
        for rc in recordsets:
            r = []
            for field in fields:
                v = None
                if '.' in field:  # for foreign key. e.g. user.usr_nm
                    v2 = rc
                    for field2 in field.split('.'):
                        v2 = v2[field2] if type(v2) == dict else getattr(v2, field2)
                        if v2 is None:
                            break
                    v = v2
                else:
                    if type(rc) == dict:
                        v = rc[field]
                    else:
                        v = getattr(rc, field)
                r.append(v)
            data .append(r)

    if removeDumpItemFields is not None:
        if len(removeDumpItemFields) > 1:
            raise Exception('Support 1 field only')  # TODO: only support the first column at the moment
        if len(data) > 0:
            fieldIndex = -1
            for i in range(len(fields)):
                if fields[i] == removeDumpItemFields[0]:
                    fieldIndex = i
                    break
            if fieldIndex == -1:
                raise Exception('Field [%s] is not found.' % removeDumpItemFields[0])
            i = -1
            lastValue = 0
            for r in data:
                i += 1
                if i == 0 or r[fieldIndex] != lastValue:
                    lastValue = r[fieldIndex]
                elif r[fieldIndex] == lastValue:
                    r[fieldIndex] = None
    return data


def getModelClass(modelName):
    '''
        return model classs
    '''
    ss = modelName.split('.')
    moduleName = ''
    modelClassName = None
    if len(ss) == 1:
        modelClassName = ss[0]
    else:
        for i in range(len(ss) - 1):
            if i > 0:
                moduleName += '.'
            moduleName += str(ss[i])
        modelClassName = ss[-1]
    return getattr(import_module(moduleName), modelClassName)


def queryModel(modelNames, queryFields=None, distinct=False, queryWhere=None, orderBy=None,
               limit=None, pageSize=None, page=None) -> QuerySet:
    if ',' in modelNames:
        raise IkValidateException('Screen recordset supports one model only at the moment: %s' % modelNames)
    modelClass = getModelClass(modelNames)
    meta = modelClass._meta

    sql = 'SELECT '
    if type(distinct) == bool and distinct:
        sql += 'DISTINCT '
    if isNullBlank(queryFields):
        sql += '* '
    else:
        if 'id' not in queryFields:
            sql += '0 AS id,'   # Raw query must include the primary key
        sql += queryFields + ' '
    sql += 'FROM ' + meta.db_table + ' '
    if not isNullBlank(queryWhere):
        sql += 'WHERE ' + queryWhere + ' '
    if not isNullBlank(orderBy):
        sql += 'ORDER BY ' + orderBy + ' '
    if not isNullBlank(limit):
        sql += 'LIMIT ' + limit + ' '
    if not isNullBlank(pageSize):
        if isNullBlank(page):
            page = 1
        if page < 1:
            raise IkValidateException('Query page cannot less than 1: %s' % page)
        engine = IkConfig.get('Database', 'engine')
        if 'postgresql' not in engine:
            raise IkValidateException('Query Pageable only supports PostgreSQL.')
        sql += 'LIIT %s OFFSET %s ' % (pageSize, pageSize * (page - 1))
    logger.debug(sql)
    ds = modelClass.objects.raw(sql)  # -> django.db.models.query.RawQuerySet
    dataStr = serializers.serialize('json', ds, fields=queryFields)
    rcs = []
    for j in json.loads(dataStr):
        r = modelClass()
        if isinstance(r, IDModel):
            id = j['pk']
            if id:
                setattr(r, 'id', id)
        fields = j['fields']
        for fieldName, fieldValue in fields.items():
            try:
                setattr(r, fieldName, fieldValue)
            except Exception as e:
                setattr(r, fieldName + "_id", fieldValue)  # TODO: foreign key ? seee masterDetailDemo.py: "author" -> "author_id"
        r.ik_set_status_retrieve()
        rcs.append(r)
    return rcs


def locateToFirst(recordset, fieldName, fieldValue) -> Model:
    '''
        locate to first record if found and set it as a cursor record. Reset the others to no cursor 
    '''
    cursorRc = None
    for rc in recordset:
        if cursorRc is not None:
            rc.ik_set_cursor(isCursor=False)
        else:
            value = getattr(rc, fieldName)
            isCursor = (value == fieldValue)
            if isCursor:
                cursorRc = rc
            rc.ik_set_cursor(isCursor=isCursor)
            if isCursor:
                break
    return cursorRc


def locateToFirstByID(recordset, id) -> Model:
    return locateToFirst(recordset, 'id', None if isNullBlank(id) else int(id))
