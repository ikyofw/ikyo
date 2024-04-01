'''
    2022-08-29
'''
import copy, logging, random, time
from collections import OrderedDict
from datetime import datetime
from enum import Enum
from django.core.exceptions import ValidationError
from django.db import connection, models, transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django_backend.settings import DATABASES
import core.utils.db as dbUtils
from core.core.exception import IkException, IkValidateException

logger = logging.getLogger('ikyo')

MODEL_RECORD_DATA_STATUS_KEY_NAME = '__STT_'
MODEL_RECORD_DATA_CURRENT_KEY_NAME = '__CRR_'

FOREIGN_KEY_VALUE_FLAG = '.'
"""Foreign key value flag. 

Example:

    user.usr_nm
"""


MODEL_PROPERTY_ATTRIBUTE_NAME_PREFIX = '_'
"""Model additional property attribute name's prefix.
    It's a read only function.

Example:
    @property
        
    def _cre_usr_nm(self):
    
        pass
"""


class ModelRecordStatus(Enum):
    '''
        model record status: n (new), m (modified), r (retrieve from database), d (delete)
    '''

    NEW = 'n'
    '''
        n: new records
    '''

    MODIFIED = 'm'
    '''
        m: record updated
    '''

    RETRIEVE = 'r'
    '''
        r: retrieve from database
    '''

    DELETE = 'd'
    '''
        d: delete
    '''


def toRecordJson(dictValues, fields=None, addRowStatus=True) -> dict:
    j = {}
    for key, value in dictValues.items():
        if key == '_state' or '__ik_' in key:  # _state: django model field. __ik_: ikyo fields, e.g. _IkModel__ik_status
            if addRowStatus:
                if (key == '_Model__ik_status' or key == '_DummyModel__ik_status'):
                    j[MODEL_RECORD_DATA_STATUS_KEY_NAME] = value.value
                elif (key == '_Model__ik_cursor' or key == '_DummyModel__ik_cursor'):
                    j[MODEL_RECORD_DATA_CURRENT_KEY_NAME] = value
            continue  # _state: django fields
        if type(value) == datetime:
            j[key] = value.strftime('%Y-%m-%d %H:%M:%S')
        else:
            j[key] = value
    if fields is None:
        return j
    j2 = {}
    for field in fields:
        j2[field] = j[field]
    return j2


class Model(models.Model):
    __ik_status = None
    '''
        IKYO record status. Values: n, m, r
    '''
    __ik_cursor = False

    def __init__(self, *args, **kwargs):
        super(Model, self).__init__(*args, **kwargs)
        # if the args' length is 0, means this is a new record created by user. E.g. newModel = ModelName()
        # else this model is from django filter from database
        self.__ik_status = ModelRecordStatus.NEW if len(args) == 0 else ModelRecordStatus.RETRIEVE

    def ik_get_status(self) -> ModelRecordStatus:
        return self.__ik_status

    def ik_is_status_new(self) -> bool:
        return self.__ik_status == ModelRecordStatus.NEW

    def ik_set_status_new(self) -> bool:
        self.__ik_status = ModelRecordStatus.NEW

    def ik_is_status_modified(self) -> bool:
        return self.__ik_status == ModelRecordStatus.MODIFIED

    def ik_set_status_modified(self):
        self.__ik_status = ModelRecordStatus.MODIFIED

    def ik_is_status_retrieve(self) -> bool:
        return self.__ik_status == ModelRecordStatus.RETRIEVE

    def ik_set_status_retrieve(self):
        self.__ik_status = ModelRecordStatus.RETRIEVE

    def ik_is_status_delete(self) -> bool:
        return self.__ik_status == ModelRecordStatus.DELETE

    def ik_set_status_delete(self):
        self.__ik_status = ModelRecordStatus.DELETE

    def ik_set_cursor(self, isCursor=True) -> None:
        self.__ik_cursor = isCursor

    def ik_is_cursor(self) -> bool:
        return self.__ik_cursor

    def getModelFields(self) -> list:
        fields = []
        fields.extend(self._meta.fields)
        return fields

    def getModelFieldNames(self) -> list:
        '''
            return db field names
        '''
        names = []
        for field in self._meta.fields:
            names.append(field.column)
        return names

    def updateValues(self, dataDict):
        '''
            Update field values (IKYO)
            dataDict = {field1: value, field2: value2, ...}
        '''
        for key, value in dataDict:
            setattr(self, key, value)

    def clean(self):
        # if True:
        #    raise ValidationError({'pub_date': 'Draft entries may not have a publication date.'})
        super().clean()

    def full_clean2(self, rcs, exclude=None, validate_unique=True):
        '''
            all records in this transaction
        '''
        self.full_clean(exclude=exclude, validate_unique=(validate_unique))

    def full_clean(self, exclude=None, validate_unique=True):
        try:
            super().full_clean(exclude=exclude, validate_unique=validate_unique)
        except ValidationError as ve:
            logger.error(ve, exc_info=True)
            messageDict = {}
            tableVerboseName = self._meta.verbose_name
            for fieldName, message in ve.message_dict.items():
                msgName = fieldName
                if msgName == '__all__':
                    msgName = 'Save data failed'
                else:
                    verboseName = self._meta.get_field(fieldName).verbose_name
                    if msgName is not None and len(msgName) > 0:
                        msgName = verboseName
                        if tableVerboseName is not None and len(tableVerboseName) > 0 \
                                and verboseName[0:len(tableVerboseName)] != tableVerboseName:
                            msgName = '%s - %s' % (tableVerboseName, msgName)
                # E.g. Soil Type Table with this Import data flag and Type already exists.
                for i in range(len(message)):
                    if message[i].endswith('with this Import data flag and Type already exists.'):
                        message[i] = 'Unique check failed. Please check [%s].' % tableVerboseName
                messageDict[msgName] = message
            raise ValidationError(messageDict)

    def _getUniqueFieldRadonValues(self, connection, uniqueFields) -> list:
        uniqueFields2 = uniqueFields
        if type(uniqueFields2) != list:
            uniqueFields2 = [uniqueFields2]
        values = []
        for field in self._meta.fields:
            if field.column in uniqueFields2:
                if field.many_to_one and len(field.to_fields) > 0:
                    raise IkException("Unique check doesn't support foreign key: Table=[%s], column=[%s]" % (self._meta.label, field.name))
                fieldType = type(field)
                randomValue = None
                if fieldType == models.TextField:
                    randomValue = self.__generateRandomUniqueString()
                elif fieldType == models.CharField:
                    randomValue = self.__generateRandomUniqueString(stringLength=field.max_length)
                elif fieldType == models.IntegerField:
                    randomValue = self.__generateRadomUniqueInteger()
                elif fieldType == models.BigIntegerField:
                    randomValue = self.__generateRadomUniqueBigInteger()
                elif fieldType == models.SmallIntegerField:
                    randomValue = self.__generateRadomUniqueSmallInteger()
                elif fieldType == models.DecimalField:
                    randomValue = self.__generateRadomUniqueDecimal(field.max_digits, field.decimal_places)
                elif fieldType == models.FloatField:
                    randomValue = self.__generateRadomUniqueFloat()
                elif fieldType == models.DateField:
                    randomValue = self.__generateRadomUniqueDate()
                elif fieldType == models.DateTimeField:
                    randomValue = self.__generateRadomUniqueDateTime()
                elif fieldType == models.TimeField:
                    randomValue = self.__generateRadomUniqueTime()
                else:
                    raise IkException('Unsupport data type: ' + fieldType)
                values.append(randomValue)
                if len(values) == len(uniqueFields):
                    break
        return values

    def __generateRandomUniqueString(self, stringLength=50) -> str:
        strLen = stringLength
        randomStr = ''
        if strLen >= 5:
            randomStr = 'BACKEND'
            strLen -= len(randomStr)

        baseStr = '!@#$%^&*()_+{}[];"|;\<>?,./`~'
        length = len(baseStr) - 1
        for i in range(strLen):
            randomStr += baseStr[random.randint(0, length)]
        return randomStr

    def __generateRadomNumberStr(self, stringLength, baseStr='123456789') -> str:
        randomStr = ''
        length = len(baseStr) - 1
        for i in range(stringLength):
            randomStr += baseStr[random.randint(0, length)]
        return randomStr

    def __generateRadomUniqueInteger(self) -> int:
        # [-2147483648,2147483647]
        s = '-20' + self.__generateRadomNumberStr(7)
        return int(s)

    def __generateRadomUniqueBigInteger(self) -> str:
        # 64bit，from -2^63 (-9223372036854775808) to 2^63-1(9223372036854775807)
        return '-91' + self.__generateRadomNumberStr(17)

    def __generateRadomUniqueSmallInteger(self) -> int:
        # [-32768 ,32767]
        s1 = self.__generateRadomNumberStr(1, baseStr='123')
        s2 = ''
        if s1 == '1' or s1 == '2':
            s2 = self.__generateRadomNumberStr(4)
        else:
            s2 = '1' + self.__generateRadomNumberStr(3)
        return int('-' + s1 + s2)

    def __generateRadomUniqueDecimal(self, max_digits, decimal_places) -> float:
        '''
            TODO: need to test 
        '''
        s1 = self.__generateRadomNumberStr(max_digits - 1)
        if decimal_places < 2:
            return float('-' + s1)
        s2 = self.__generateRadomNumberStr(decimal_places - 1)
        return float('-' + s1 + '.' + s2)

    def __generateRadomUniqueFloat(self) -> float:
        return float('-91' + self.__generateRadomNumberStr(7) + '.' + self.__generateRadomNumberStr(9))

    def __generateRadomUniqueDateStr(self) -> str:
        # 2022-09-14
        dateStr = '9' + self.__generateRadomNumberStr(3)
        month = self.__generateRadomNumberStr(1, baseStr='01')
        if month == '1':
            month += self.__generateRadomNumberStr(1, baseStr='012')
        else:  # 0
            month += self.__generateRadomNumberStr(1, baseStr='12345679')
        dateStr += '-' + month
        dateStr += '-' + self.__generateRadomNumberStr(1, baseStr='012') + self.__generateRadomNumberStr(1, baseStr='12345678')
        return dateStr

    def __generateRadomUniqueTimeStr(self) -> str:
        timeStr = self.__generateRadomNumberStr(1, baseStr='01') + self.__generateRadomNumberStr(1, baseStr='1234567890')
        timeStr += ':' + self.__generateRadomNumberStr(1, baseStr='012345') + self.__generateRadomNumberStr(1)
        timeStr += ':' + self.__generateRadomNumberStr(1, baseStr='012345') + self.__generateRadomNumberStr(1)
        return timeStr

    def __generateRadomUniqueDate(self) -> datetime:
        dateStr = self.__generateRadomUniqueDateStr()
        return datetime.strptime(dateStr, "%Y-%m-%d").date()

    def __generateRadomUniqueDateTime(self) -> datetime:
        dateStr = self.__generateRadomUniqueDateStr()
        timeStr = self.__generateRadomUniqueTimeStr()
        return datetime.strptime(dateStr + ' ' + timeStr, "%Y-%m-%d %H:%M:%S")

    def __generateRadomUniqueTime(self) -> time:
        timeStr = self.__generateRadomUniqueTimeStr()
        return datetime.strptime(timeStr, "%H:%M:%S").time()

    def toJson(self, fields=None) -> dict:
        '''
            fields: model fields. None means all
        '''
        jData = toRecordJson(self.__dict__, fields=fields)
        if self.ik_is_cursor():
            jData[MODEL_RECORD_DATA_CURRENT_KEY_NAME] = True
        return jData

    def updateCommonFields(self, values: dict) -> None:
        '''
            values: {'operatorID': operatorId2, 'updateTime': updateDate}
        '''
        pass

    def save2(self) -> None:
        """Use IkTransaction to save the current model for a new, updated or delete record.

        Exception:
            Raise core.core.exception.IkException if save failed.
        """
        from core.db.transaction import IkTransaction # fix circular import problem
        trn = IkTransaction()
        trn.add(self)
        b = trn.save()
        if not b.value:
            raise IkException(b.value)
        
    def delete2(self) -> None:
        """Use IkTransaction to delete the current model.

        Exception:
            Raise core.core.exception.IkException if save failed.
        """
        if self.ik_is_status_new():
            return
        from core.db.transaction import IkTransaction # fix circular import problem
        trn = IkTransaction()
        trn.delete(self)
        b = trn.save()
        if not b.value:
            raise IkException(b.value)


    class Meta:
        abstract = True


class IkViewModel(models.Model):
    class Meta:
        abstract = True


class IkTempModel(models.Model):
    '''
        the model does not exist in the database
    '''
    class Meta:
        abstract = True
        managed = False


# TODO: cannot call??


@receiver(pre_save, sender=Model)
def pre_save_handler(sender, **kwargs):
    logger.debug("{},{}".format(sender, **kwargs))


class IDModel(Model):
    '''
        The models has id field
    '''
    id = models.AutoField(primary_key=True)
    version_no = models.SmallIntegerField(default=0, verbose_name='Version No.')
    __original_version_no = None

    def assignPrimaryID(self) -> int:
        '''
            assign the 'id' field's value if id is None or id = 0. The id field should be a serial type.

            Supports PostgreSQL only.
        '''
        dbType = DATABASES['default']['ENGINE']
        # YL.ikyo, 2023-11-23 Update add support sqlite3 - start
        if 'postgresql' in dbType:
            if self.id is None or self.id == 0:
                dbTable = self._meta.db_table
                id = dbUtils.getNextSequence(dbTable + '_id_seq', 'postgresql')
                self.id = id
                return id
            return self.id
        elif 'sqlite3' in dbType:
            if self.id is None or self.id == 0:
                dbTable = self._meta.db_table
                id = dbUtils.getNextSequence(dbTable, 'sqlite3')
                self.id = id
                return id
            return self.id
        else:
            raise IkException('Unsupport database engine: %s' % dbType)
        # YL.ikyo, 2023-11-23 - end

    def getModelDisplayName(self) -> str:
        return self.__str__()

    # overwrite
    def ik_set_status_modified(self):
        if not self.ik_is_status_modified():
            super().ik_set_status_modified()
            if self.__original_version_no is None:  # prevention version_no multiple times +1
                self.__original_version_no = self.version_no
                self.version_no += 1

    def concurrencyCheck(self, beforeUpdate=True) -> None:
        '''
            raise IkValidateException if failed.
            beforeUpdate: true: before updating, false: after saving
        '''
        rc = self
        if self.ik_is_status_modified() and beforeUpdate or not beforeUpdate:
            # Concurrency check: version_no
            recordName = rc.getModelDisplayName()
            if recordName is None:
                recordName = str(rc.id)
            sql = 'SELECT version_no FROM ' + rc.__class__._meta.db_table + ' WHERE id=' + dbUtils.toSqlField(rc.id)
            conn = transaction.get_connection()
            rs = None
            with conn.cursor() as cursor:
                cursor.execute(sql)
                rs = cursor.fetchall()
            if dbUtils.isEmpty(rs):
                raise IkValidateException('Concurrency Validate Error: Record [%s] has been deleted, please check %s.' % (
                    recordName, rc._meta.verbose_name))
            dbVersionNo = rs[0][0]
            if (rc.version_no - 1 if beforeUpdate else rc.version_no) < dbVersionNo:
                modifyUser = None
                raise IkValidateException('Concurrency Validate Error: Record [%s] has been updated by %s, please check %s.' % (recordName,
                                                                                                                                'others' if modifyUser is None else modifyUser, rc._meta.verbose_name))
            elif (rc.version_no - 1) > dbVersionNo:
                raise IkValidateException("Concurrency Validate Error: Record [%s]'s concurrency flat is incorrect, please check %s." % (
                    recordName, rc._meta.verbose_name))

    class Meta:
        abstract = True


class IDModelView(IDModel):
    '''
        view model
    '''

    def assignPrimaryID(self) -> int:
        raise IkValidateException('View cannot call [assignPrimaryID] method.')

    class Meta:
        abstract = True


class IkView(Model):
    class Meta:
        abstract = True


class DummyModel(OrderedDict):
    RECORD_NAME = 'dummy'

    def __init__(self, values=None, status=None) -> None:
        if values is not None:
            self.update(values)
        self.__ik_status = ModelRecordStatus.NEW if status is None else status
        '''
            Row status. Same as normal model.
            ModelRecordStatus
        '''
        self.__selected = None

    def ik_is_status_new(self) -> bool:
        return self.__ik_status == ModelRecordStatus.NEW

    def ik_set_status_new(self) -> bool:
        self.__ik_status = ModelRecordStatus.NEW

    def ik_is_status_modified(self) -> bool:
        return self.__ik_status == ModelRecordStatus.MODIFIED

    def ik_set_status_modified(self):
        self.__ik_status = ModelRecordStatus.MODIFIED

    def ik_is_status_retrieve(self) -> bool:
        return self.__ik_status == ModelRecordStatus.RETRIEVE

    def ik_set_status_retrieve(self):
        self.__ik_status = ModelRecordStatus.RETRIEVE

    def ik_is_status_delete(self) -> bool:
        return self.__ik_status == ModelRecordStatus.DELETE

    def ik_set_status_delete(self):
        self.__ik_status = ModelRecordStatus.DELETE

    def ik_set_selected(self, selected=True) -> None:
        self.__selected = selected

    def ik_is_selected(self) -> bool:
        return self.__selected == True

    def getJson(self) -> dict:
        v = copy.deepcopy(self)
        v.update(self.__dict__)
        return toRecordJson(v)
