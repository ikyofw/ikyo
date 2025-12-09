import json
import logging
from importlib import import_module

from django.core import serializers
from django.db.models import QuerySet

from core.core.exception import IkValidateException
from core.db.model import DummyModel, Model
from iktools import IkConfig

from .lang_utils import isNullBlank

logger = logging.getLogger('ikyo')


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


def redcordsets2List(recordsets, fields: list[str], removeDumpItemFields=None) -> list:
    data = []
    if recordsets is not None:
        for rc in recordsets:
            r = []
            for field in fields:
                v = None
                if '.' in field:  # for foreign key. e.g. user.usr_nm
                    v2 = rc
                    for field2 in field.split('.'):
                        v2 = v2[field2] if type(v2) == dict else getModelAttr(v2, field2)
                        if v2 is None:
                            break
                    v = v2
                else:
                    if type(rc) == dict:
                        v = rc[field]
                    else:
                        v = getModelAttr(rc, field)
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
    try:
        module_name, class_name = modelName.rsplit('.', 1)

        # Import the module and get the class
        module = import_module(module_name)
        return getattr(module, class_name)
    except ValueError:
        raise ImportError(f"Invalid modelName format: '{modelName}'.")
    except ImportError as e:
        raise ImportError(e)
    except AttributeError as e:
        raise AttributeError(e)


def get_model_class_1(app_name: str, class_nm: str):
    '''
        return model class
    '''
    model_name = "%s.models.%s" % (app_name, class_nm)

    viewClass = None
    error_messages = []
    try:
        viewClass = getModelClass(class_nm)
    except Exception as e:
        error_messages.append(str(e))
    if viewClass is None:
        try:
            viewClass = getModelClass(model_name)
        except Exception as e:
            error_messages.append(str(e))

    if viewClass is None:
        logger.error("Failed to load model [%s] from app [%s], errors: %s" % (class_nm, app_name, "; ".join(error_messages)))
    return viewClass


def get_model_class_2(app_name: str, screen_sn: str, class_nm: str):
    '''
        return module class
    '''
    module_name_1 = "%s.views.%s" % (app_name, screen_sn)
    module_name_2 = "%s.views.%s.%s" % (app_name, screen_sn.lower(), screen_sn)

    viewClass = None
    error_messages = []
    try:
        viewClass = getModelClass(class_nm)
    except Exception as e:
        error_messages.append(str(e))
    if viewClass is None:
        try:
            viewClass = getModelClass(module_name_1)
        except Exception as e:
            error_messages.append(str(e))
    if viewClass is None:
        try:
            viewClass = getModelClass(module_name_2)
        except Exception as e:
            error_messages.append(str(e))

    if viewClass is None:
        logger.error("Failed to load module [%s] from app [%s], errors: %s" % (screen_sn, app_name, "; ".join(error_messages)))
    return viewClass


def is_model_class_exists(app_name: str, screen_sn: str, class_nm: str) -> bool:
    '''
    Check if the model class exists.
    '''
    try:
        if not isNullBlank(class_nm):
            module_name, class_name = class_nm.rsplit('.', 1)
            module = import_module(module_name)
            if hasattr(module, class_name):
                return True
            else:
                logger.error("Failed to load module [%s] from app [%s], errors: [%s] is not found." % (screen_sn, app_name, class_nm))
                return False
    except ImportError as e:
        logger.error("Failed to load module [%s] from app [%s], errors: %s" % (screen_sn, app_name, e))

    module_name_1 = "%s.views" % app_name
    try:
        module = import_module(module_name_1)
        if hasattr(module, screen_sn):
            return True
        else:
            logger.error("Failed to load module [%s] from app [%s], errors: [%s.%s] is not found." % (screen_sn, app_name, module_name_1, screen_sn))
    except ImportError as e:
        logger.error("Failed to load module [%s] from app [%s], errors: %s" % (screen_sn, app_name, e))

    module_name_2 = "%s.views.%s" % (app_name, screen_sn.lower())
    try:
        module = import_module(module_name_2)
        if hasattr(module, screen_sn):
            return True
        else:
            logger.error("Failed to load module [%s] from app [%s], errors: [%s.%s] is not found." % (screen_sn, app_name, module_name_2, screen_sn))
    except ImportError as e:
        logger.error("Failed to load module [%s] from app [%s], errors: %s" % (screen_sn, app_name, e))

    return False


def queryModel(modelNames, queryFields=None, distinct=False, queryWhere=None, orderBy=None,
               limit=None, pageSize=None, page=None) -> QuerySet:
    if ',' in modelNames:
        raise IkValidateException('Screen recordset supports one model only at the moment: %s' % modelNames)
    modelClass = getModelClass(modelNames)
    if modelClass == DummyModel:
        return None
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
    sql += 'FROM %s ' % meta.db_table
    if not isNullBlank(queryWhere):
        sql += 'WHERE %s ' % queryWhere
    if not isNullBlank(orderBy):
        sql += 'ORDER BY %s ' % orderBy
    if not isNullBlank(limit):
        sql += 'LIMIT %s ' % limit
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
        if 'pk' in j and hasattr(r, 'id'):
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
            value = getModelAttr(rc, fieldName)
            isCursor = (value == fieldValue)
            if isCursor:
                cursorRc = rc
            rc.ik_set_cursor(isCursor=isCursor)
            if isCursor:
                break
    return cursorRc


def locateToFirstByID(recordset, id) -> Model:
    return locateToFirst(recordset, 'id', None if isNullBlank(id) else int(id))


def dictToModel(dictData: dict, modelClass: Model) -> Model:
    modelOnstance = modelClass()
    # Iterate through the dictionary items
    for key, value in dictData.items():
        # Check if the key exists as a field in the model
        if hasattr(modelOnstance, key):
            # Set the value of the field
            setattr(modelOnstance, key, value)
    return modelOnstance


def dictsToModels(dictDataList: list[dict], modelClass: Model) -> list[Model]:
    rcs = []
    for dd in dictDataList:
        rcs.append(dictToModel(dd, modelClass))
    return rcs


def getModelAttr(modrlRecord: Model, attrName: str) -> any:
    """attrName can be a foreign key. E.g. usr__usr_nm (it's the same as usr.usr_nm)
    """
    fields = attrName.replace('__', '.').split('.')
    attr = None
    for i in range(0, len(fields)):
        attr = getattr(modrlRecord if i == 0 else attr, fields[i])
        if attr is None:
            break
    return attr


def getModelPropertyValues(instance: Model) -> dict:
    """Get the model's property values which the function defined with @property.
    """
    properties = vars(instance.__class__)
    property_methods = [name for name, value in properties.items() if isinstance(value, property)]

    values = {}
    for name in property_methods:
        values[name] = getattr(instance, name)
    return values

def models_equal(m1: Model, m2: Model, fields: list) -> bool:
    return all(getattr(m1, f) == getattr(m2, f) for f in fields)