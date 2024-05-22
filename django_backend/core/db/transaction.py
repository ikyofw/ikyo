import inspect
import logging
import traceback
from datetime import datetime

import core.utils.db as dbUtils
from core.core.exception import IkException, IkValidateException
from core.core.lang import Boolean2
from django.core.exceptions import ValidationError
from django.db import (DatabaseError, DataError, IntegrityError, models,
                       transaction)
from django.db.models.query import QuerySet

from .model import IDModel, Model

logger = logging.getLogger('ikyo')


class IkTransactionModel():
    def __init__(self, modelData, updateFields=None, validateExclude=None, validateUnique=True, foreignKeys=None, bulkCreate: bool = False) -> None:
        '''
            modelData: a Model object or Model list [modelRc1, modeRc2...]
        '''
        self.modelData = modelData
        self.updateFields = updateFields
        self.validateExclude = validateExclude
        self.validateUnique = validateUnique
        self.foreignKeys = foreignKeys
        self.bulkCreate = bulkCreate


DEFAULT_FOREIGN_FIELD = 'id'


class IkTransactionForeignKey():
    def __init__(self, modelFieldName, foreignModelRecord, foreignField=DEFAULT_FOREIGN_FIELD) -> None:
        self.modelFieldName = modelFieldName
        self.foreignModelRecord = foreignModelRecord
        self.foreignField = foreignField


class IkTransaction():
    def __init__(self, caller=None, userID=None) -> None:
        self.__modelDataList = []
        self.__operatorId = userID
        if self.__operatorId is None:
            try:
                frame = inspect.stack()[1].frame
                localvars = frame.f_locals
                caller = localvars.get('self', None)  # AuthAPIView
                if caller is not None:
                    self.__operatorId = caller.getCurrentUserId()
            except:
                pass
        if self.__operatorId is None:
            self.__operatorId = -1

    def delete(self, modelData):
        '''
            mark model data to delete and then call add method
        '''
        if modelData is None:
            return
        if type(modelData) == list or type(modelData) == QuerySet:
            if type(modelData) == QuerySet:
                modelData2 = [r for r in modelData]
                modelData = modelData2
            for r in modelData:
                if isinstance(r, Model):
                    r.ik_set_status_delete()
        elif isinstance(modelData, Model):
            modelData.ik_set_status_delete()
        else:
            raise IkException('unsupport data type: %s' % type(modelData))
        self.add(modelData)

    def modify(self, modelData, updateFields=None, validateExclude=None, validateUnique=True):
        '''
            mark the record to modify
        '''
        if modelData is None:
            return
        if type(modelData) == list or type(modelData) == QuerySet:
            for r in modelData:
                if isinstance(r, Model) and not r.ik_is_status_new():
                    r.ik_set_status_modified()
        elif isinstance(modelData, Model):
            if not modelData.ik_is_status_new():
                modelData.ik_set_status_modified()
        else:
            raise IkException('unsupport data type: %s' % type(modelData))
        return self.add(modelData, updateFields=updateFields, validateExclude=validateExclude, validateUnique=validateUnique)

    def add(self, modelData, updateFields=None, validateExclude=None, validateUnique=True, foreignKeys=None):
        '''
            [validateExclude] and [validateUnique] are used for model.full_clean(exclude=None, validate_unique=True)
            foreignKeys (dict/list/IkTransactionForeignKey): {fieldName1: value1, fieldName2: value2 ...} or list [IkTransactionForeignKey1, IkTransactionForeignKey2]
        '''
        if modelData is None:
            raise IkValidateException('Parameter [modelData] is mandatory.')
        if type(modelData) == QuerySet:
            modelDataList = [r for r in modelData]
            modelData = modelDataList
            # raise IkValidateException('Parameter [modelData] cannot be a QuerySet.')
        ikTransactionModel = IkTransactionModel(modelData=modelData, updateFields=updateFields, validateExclude=validateExclude,
                                                validateUnique=validateUnique, foreignKeys=foreignKeys)
        self.__modelDataList.append(ikTransactionModel)

    def getModelData(self) -> list:
        '''
            return IkTransactionModel list
        '''
        return self.__modelDataList

    def clean(self):
        '''
            clean model data
        '''
        self.__modelDataList.clear()

    def save(self, operatorId=None, updateDate=None, beforeSave=None, beforeSaveModels=None, afterSaveModels=None, beforeCommit=None, afterRollback=None) -> Boolean2:
        '''
            save and commit, return true if success
            operatorId: can be null if caller is an AuthAPIView.
            beforeSave (function): Parameter list: self(IkTransaction), django.db.transaction. 
                                If you want to stop continue saving, please raise a IkMessageException.
            beforeSaveModels (function): Parameter list: self(IkTransaction), django.db.transaction, IkTransactionModel. 
                                If you want to stop continue saving, please raise a IkMessageException.
            afterSaveModels (function): Parameter list: self(IkTransaction), django.db.transaction, IkTransactionModel. 
                                If you want to stop continue saving, please raise a IkMessageException.
            beforeCommit (function): Parameter list: self(IkTransaction), django.db.transaction. 
                                If you want to stop continue saving, please raise a IkMessageException.
            afterRollback (function): Parameter list: self(IkTransaction), django.db.transaction. 
                                If you want to stop continue saving, please raise a IkMessageException.
        '''
        if len(self.__modelDataList) == 0:
            return Boolean2(False, 'No data saved.')

        try:
            operatorId2 = self.__operatorId if operatorId is None else operatorId
            # update system fields - start
            updateDate = datetime.now() if updateDate is None else updateDate
            hasUpdateRecords = False
            for ikTransactionModel in self.__modelDataList:
                data = ikTransactionModel.modelData
                if isinstance(data, Model):
                    if data.ik_is_status_modified() or data.ik_is_status_new():
                        data.updateCommonFields({'operatorID': operatorId2, 'updateTime': updateDate})
                    if not hasUpdateRecords and not data.ik_is_status_retrieve():
                        hasUpdateRecords = True
                elif type(data) == list or type(data) == QuerySet:
                    for r in data:
                        if isinstance(r, Model):
                            if r.ik_is_status_modified() or r.ik_is_status_new():
                                r.updateCommonFields({'operatorID': operatorId2, 'updateTime': updateDate})
                            if not hasUpdateRecords and not r.ik_is_status_retrieve():
                                hasUpdateRecords = True
                        else:
                            hasUpdateRecords = True
                else:
                    hasUpdateRecords = True
            if not hasUpdateRecords:
                return Boolean2(trueFalse=True, data='No data changed.')
            # update system fields - end

            # validate and save
            try:
                savePoint = None
                try:
                    with transaction.atomic():
                        savePoint = transaction.savepoint()
                        logger.debug("save models ...")
                        if beforeSave is not None:
                            logger.debug("save models before save ...")
                            beforeSave(self, transaction)
                        modelSeq = 0
                        totalModels = len(self.__modelDataList)
                        for ikTransactionModel in self.__modelDataList:
                            modelSeq += 1
                            logger.debug('save models %s of %s ...' % (modelSeq, totalModels))
                            if beforeSaveModels is not None:
                                beforeSaveModels(self, transaction, ikTransactionModel)
                            data = ikTransactionModel.modelData
                            if isinstance(data, models.Model):
                                self.__updateForeignKey([data], ikTransactionModel.foreignKeys)
                                # self.__validateRc(data, ikTransactionModel, [data])
                                self.__saveOneRecord(data, ikTransactionModel)
                            elif (type(data) == list or type(data) == QuerySet):
                                if len(data) == 0:
                                    continue
                                self.__bulkSave(data, ikTransactionModel)
                            else:
                                raise IkValidateException('Unsupport data: %s' % type(data))
                            if afterSaveModels is not None:
                                logger.debug("save models afterSaveModels ...")
                                afterSaveModels(self, transaction, ikTransactionModel)
                        if beforeCommit is not None:
                            logger.debug("save models beforeCommit ...")
                            beforeCommit(self, transaction)
                        logger.debug("save models savepoint_commit ...")
                        transaction.savepoint_commit(savePoint)
                        logger.debug("save models savepoint_commit done")
                except Exception as e:
                    if savePoint is not None:
                        transaction.savepoint_rollback(savePoint)
                        if afterRollback is not None:
                            afterRollback(self, transaction)
                    raise e
            except ValidationError as ve:
                logger.error(ve, exc_info=True)
                return Boolean2(trueFalse=False, data=self.__getValidationError(ve))
            except DatabaseError as ie:  # IntegrityError
                logger.error(ie, exc_info=True)
                msg = str(ie)
                if type(ie) == IntegrityError:
                    if 'DETAIL: ' in msg:  # e.g. IntegrityError
                        msg = msg[msg.index('DETAIL: '):-1]  # last character is \n
                        return Boolean2(False, 'Save data failed. %s' % msg)
                    if 'duplicate key value violates unique constraint' in msg:
                        return Boolean2(False, 'Save failed. Please check unique field(s).')
                elif type(ie) == DataError:
                    errStr = str(ie).split('\n')[0]
                    return Boolean2(False, 'Save failed. Please check your inputs: %s' % (errStr))
                return Boolean2(False, 'Save failed. Please check your inputs: %s' % (msg))
        except IkException as e:
            logger.error(e, exc_info=True)
            return Boolean2(False, str(e))
        except Exception as e:
            logger.error(e, exc_info=True)
            return Boolean2(False, 'Save data to database failed. Please ask adinistrator to check.')
        return Boolean2(True, data='Saved.')

    def __getValidationError(self, ve) -> str:
        s = ''
        for name, msg in ve.message_dict.items():
            if len(s) > 0:
                s += '\n'
            s += '%s: %s' % (name, msg)
        return s

    def __saveOneRecord(self, r, ikTransactionModel):
        if r.ik_is_status_delete():
            r.delete()
        elif r.ik_is_status_new() or r.ik_is_status_modified():
            self.__validateRc(r, ikTransactionModel, [r])
            if ikTransactionModel.updateFields is not None:
                r.save(update_fields=ikTransactionModel.updateFields)
            else:
                r.save()

    def __bulkSave(self, data, ikTransactionModel):
        modelClass = data[0].__class__
        updatedRcs = []
        deletedRcs = []
        newRcs = []
        dataWithoutDeletedRcs = []
        for r in data:
            if r.ik_is_status_delete():
                deletedRcs.append(r)
            elif r.ik_is_status_new():
                newRcs.append(r)
            elif r.ik_is_status_modified():
                updatedRcs.append(r)
            if not r.ik_is_status_delete():
                dataWithoutDeletedRcs.append(r)
        self.__updateForeignKey(data, ikTransactionModel.foreignKeys)

        # delete first
        if len(deletedRcs) > 0:
            for r in deletedRcs:
                r.delete()
        if len(updatedRcs) > 0:
            # unique check for update rcs- start
            updateFields = None
            saveUpdateOneByOne = False
            if len(updatedRcs) > 0:
                updateFields = self.__getUpdateFieldNames(ikTransactionModel, updatedRcs[0])
                uniqueCheckedRcs = self.__validateUpdateRecords(deletedRcs, updatedRcs, ikTransactionModel, updateFields)
                saveUpdateOneByOne = len(uniqueCheckedRcs) > 0
                for r in updatedRcs:
                    # if the record has run unique sql, then ignore the unique check
                    self.__validateRc(r, ikTransactionModel, dataWithoutDeletedRcs, validateUnique=(not saveUpdateOneByOne))
                    # TODO: 2022-11-10 (Li)
                    # need to save one by one. E.g.
                    # seq, name
                    # 1, a1
                    # 2, a2
                    # 3, a3
                    # 4, a4
                    # then delete item 2.
                    # when validate item 4, will get error (item 4's seq changed to 3)
                    r.save(update_fields=ikTransactionModel.updateFields)
                    if isinstance(r, IDModel):
                        r.concurrencyCheck(beforeUpdate=False)

            # unique check for update rcs- end
            # if saveUpdateOneByOne:
            #    for r in updatedRcs:
            #        r.save()
            # else:
            #    modelClass.objects.bulk_update(updatedRcs, updateFields)
        if len(newRcs) > 0:
            self.__validateNewRecords(newRcs, ikTransactionModel, dataWithoutDeletedRcs)
            if ikTransactionModel.bulkCreate:
                modelClass.objects.bulk_create(newRcs)
            else:
                for newRc in newRcs:
                    newRc.save()

    def __getUpdateFieldNames(self, ikTransactionModel, rc) -> list:
        updateFields = ikTransactionModel.updateFields
        if updateFields is None:
            updateFields = self.__getModelFullUpdateFieldNames(rc)
        return updateFields

    def __validateRc(self, rc, ikTransactionModel, rcs, validateUnique=True):
        for field in rc._meta.get_fields():
            try:
                if field.many_to_one and len(field.to_fields) > 0:  # e.g. set model.hdr = model.hdr to update the model.hdr_id
                    value = getattr(rc, field.name)
                    setattr(rc, field.name, value)
            except:
                traceback.print_exc()
        if len(rcs) > 1 and isinstance(rc, Model):
            rc.full_clean2(rcs=rcs, exclude=ikTransactionModel.validateExclude,
                           validate_unique=(ikTransactionModel.validateUnique and validateUnique))
        else:
            rc.full_clean(exclude=ikTransactionModel.validateExclude, validate_unique=(ikTransactionModel.validateUnique and validateUnique))
        if isinstance(rc, IDModel) and rc.ik_is_status_modified():
            rc.concurrencyCheck(beforeUpdate=True)

    def __getModelFullUpdateFieldNames(self, modelRecord) -> list:
        updateFields = []
        for modelField in modelRecord._meta.fields:
            if modelField.name == 'id':
                continue
            updateFields.append(modelField.name)
        return updateFields

    def __hasIdField(self, modelRecord) -> list:
        if isinstance(modelRecord, IDModel):
            return True
        for modelField in modelRecord._meta.fields:
            if modelField.name == 'id':
                return True
        return False

    def __getFieldValue(self, rc, fieldName):
        return getattr(rc, fieldName)

    def __updateForeignKey(self, rcs, foreignKeys):
        if len(rcs) > 0 and foreignKeys is not None:
            if isinstance(foreignKeys, dict) and len(foreignKeys) > 0:
                for field, foreignValue in foreignKeys.items():
                    for rc in rcs:
                        if rc.ik_is_status_delete():
                            continue
                        originalValue = self.__getModelForeignField(rc, field)
                        newValue = foreignValue
                        if isinstance(foreignValue, models.Model):
                            newValue = getattr(foreignValue, DEFAULT_FOREIGN_FIELD)
                        if originalValue != newValue:
                            self.__setForeignFieldValue(rc, field, foreignValue, newValue)
                            if rc.ik_is_status_retrieve():
                                rc.ik_set_status_modified()
            elif type(foreignKeys) == list and len(foreignKeys) > 0:
                for fk in foreignKeys:  # fk = IkTransactionForeignKey
                    if fk is not None:
                        for rc in rcs:
                            if rc.ik_is_status_delete():
                                continue
                            originalValue = self.__getModelForeignField(rc, fk.modelFieldName)
                            newValue = self.__getModelForeignField(fk.foreignModelRecord, fk.foreignField)
                            if originalValue != newValue:
                                self.__setForeignFieldValue(rc, fk.modelFieldName, fk.foreignModelRecord, newValue)
                                if rc.ik_is_status_retrieve():
                                    rc.ik_set_status_modified()
            elif isinstance(foreignKeys, IkTransactionForeignKey):
                fk = foreignKeys
                for rc in rcs:
                    if rc.ik_is_status_delete():
                        continue
                    originalValue = self.__getModelForeignField(rc, fk.modelFieldName)
                    newValue = self.__getModelForeignField(fk.foreignModelRecord, fk.foreignField)
                    if originalValue != newValue:
                        self.__setForeignFieldValue(rc, fk.modelFieldName, fk.foreignModelRecord, newValue)
                        if rc.ik_is_status_retrieve():
                            rc.ik_set_status_modified()

    def __getModelForeignField(self, rc, fieldName):
        try:
            return getattr(rc, fieldName)
        except Exception as e:
            if type(e).__name__ == 'RelatedObjectDoesNotExist' \
                and type(fieldName) == str and not fieldName.endswith('_' + DEFAULT_FOREIGN_FIELD):
                    return getattr(rc, fieldName + '_' + DEFAULT_FOREIGN_FIELD)
            else:
                raise e

    def __setForeignFieldValue(self, rc, fieldName, valueRc, value):
        try:
            if isinstance(valueRc, models.Model):
                setattr(rc, fieldName, valueRc)
            else:
                setattr(rc, fieldName, value)
        except Exception as e:
            if type(e).__name__ == 'RelatedObjectDoesNotExist' \
                and type(fieldName) == str and not fieldName.endswith('_' + DEFAULT_FOREIGN_FIELD):
                setattr(rc, fieldName + '_' + DEFAULT_FOREIGN_FIELD, value)
            else:
                raise e

    def __validateUpdateRecords(self, deletedRcs, updatedRcs, ikTransactionModel, updateFieldNames) -> list:
        '''
            return patched unique records
        '''
        uniqueCheckedRcs = []
        hasIDField = self.__hasIdField(updatedRcs[0])
        if not hasIDField:
            # TODO: support id key model only
            return uniqueCheckedRcs
        uniqueFieldsList = self.__getModelUnique(updatedRcs[0])

        modelClass = updatedRcs[0].__class__
        dbTable = modelClass._meta.db_table
        conn = transaction.get_connection()
        for uniqueFiledNames in uniqueFieldsList:
            for rcIndex in range(len(updatedRcs)):
                rc = updatedRcs[rcIndex]
                uniqueValues = self.__getFieldValues(rc, uniqueFiledNames)

                # if the unique record will be delete, then ignore it
                if len(deletedRcs) > 0:
                    hasFoundDeletingRecords = False
                    deleteRecordID = None
                    for deleteRc in deletedRcs:
                        deleteRcUniqueValues = self.__getFieldValues(deleteRc, uniqueFiledNames)
                        if self.__isTheSame(modelClass, uniqueFiledNames, uniqueValues, deleteRcUniqueValues):
                            hasFoundDeletingRecords = True
                            if hasIDField:
                                deleteRecordID = deleteRc.id
                            break
                    if hasFoundDeletingRecords and (not hasIDField or (hasIDField and rc.id != deleteRecordID)):
                        continue  # ignore this record unique's checking

                # check other updating records
                for i in range(rcIndex + 1, len(updatedRcs)):
                    nextRc = updatedRcs[i]
                    if hasIDField:
                        modelFields = nextRc._meta.fields
                        sql = 'SELECT '
                        for j in range(len(uniqueFiledNames)):
                            if j > 0:
                                sql += ','
                            modelField = None
                            for mf in modelFields:
                                if mf.is_relation:  # E.g. hdr -> hdr_id, hdr_id -> hdr
                                    if mf.column == uniqueFiledNames[j] or mf.name == uniqueFiledNames[j]:
                                        modelField = mf
                                        break
                                else:
                                    if mf.name == uniqueFiledNames[j]:
                                        modelField = mf
                                        break
                            if modelField is None:
                                raise IkException('Field [%s] does not exist in [%s]. Plesae check the unique keys: %s' %
                                                  (uniqueFiledNames[j], nextRc._meta.label, str(uniqueFiledNames)))
                            sql += modelField.column
                        sql += ' FROM ' + dbTable + ' WHERE id=' + dbUtils.toSqlField(nextRc.id)
                        rs = None
                        with conn.cursor() as cursor:
                            cursor.execute(sql)
                            rs = cursor.fetchall()
                        if not dbUtils.isEmpty(rs):
                            if self.__isTheSame(modelClass, uniqueFiledNames, uniqueValues, rs[0]):
                                # is this record's unique changed ?
                                nextRcCurrentUniqueValues = self.__getFieldValues(nextRc, uniqueFiledNames)
                                if not self.__isTheSame(modelClass, uniqueFiledNames, nextRcCurrentUniqueValues, rs[0]):
                                    # get foreign keys
                                    foreignKeys = []
                                    uniqueFiledNamesWithoutForeignKeys = []
                                    for name in uniqueFiledNames:
                                        modelField = nextRc._meta.get_field(name)
                                        if modelField.many_to_one and len(modelField.to_fields) > 0:
                                            foreignKeys.append(name)
                                        else:
                                            uniqueFiledNamesWithoutForeignKeys.append(name)
                                    tempUniqueValues = nextRc._getUniqueFieldRadonValues(conn, uniqueFiledNamesWithoutForeignKeys)
                                    # update the unique fields to a temp value
                                    sql = 'UPDATE ' + dbTable + ' SET '
                                    for j in range(len(uniqueFiledNamesWithoutForeignKeys)):
                                        name = uniqueFiledNamesWithoutForeignKeys[j]
                                        if j > 0:
                                            sql += ','
                                        sql += uniqueFiledNamesWithoutForeignKeys[j] + '=' + dbUtils.toSqlField(tempUniqueValues[j])
                                    sql += ' WHERE id=' + dbUtils.toSqlField(nextRc.id)
                                    logger.debug(sql)
                                    with conn.cursor() as cursor:
                                        cursor.execute(sql)
                                    if rc not in uniqueCheckedRcs:
                                        uniqueCheckedRcs.append(rc)
                    else:  # doesn't have 'id' field, then check the unique field directly
                        pass  # TODO:
        return uniqueCheckedRcs

    def __validateNewRecords(self, newRcs, ikTransactionModel, dataWithoutDeletedRcs):
        '''
            if validate failed, then raise exception
        '''
        hasIDField = self.__hasIdField(newRcs[0])
        if not hasIDField:
            # TODO: support id key model only
            return
        uniqueFieldsList = self.__getModelUnique(newRcs[0])
        if len(uniqueFieldsList) == 0:
            return
        # check the current record sets' unique fields
        isAllTheSame = False
        for uniqueFiledNames in uniqueFieldsList:
            uniqueValueList = []
            for rcIndex in range(len(dataWithoutDeletedRcs)):
                rc = dataWithoutDeletedRcs[rcIndex]
                rcUniqueValues = self.__getFieldValues(rc, uniqueFiledNames)
                if len(uniqueValueList) > 0:
                    isAllTheSame = True
                    for values in uniqueValueList:
                        for i in range(len(values)):
                            v1 = values[i]
                            v2 = rcUniqueValues[i]
                            if v1 != v2:
                                isAllTheSame = False
                                break
                    if isAllTheSame:
                        errorMsg1 = ''
                        errorMsg2 = ''
                        for i in range(len(uniqueFiledNames)):
                            if i > 0:
                                errorMsg1 += ', '
                                errorMsg2 += ', '
                            errorMsg1 += uniqueFiledNames[i] + ' = '
                            errorMsg2 += uniqueFiledNames[i] + ' = '
                            if isinstance(rcUniqueValues[i], IDModel):
                                errorMsg1 += str(rcUniqueValues[i].getModelDisplayName())
                                errorMsg2 += str(rcUniqueValues[i].getModelDisplayName()) + ', id=' + str(rcUniqueValues[i].id)
                            else:
                                errorMsg1 += str(rcUniqueValues[i])
                                errorMsg2 += str(rcUniqueValues[i])
                        tableVerboseName = rc._meta.verbose_name
                        logger.error("Unique Validate Failed: Key (%s) already exists. Please check %s." % (errorMsg2, tableVerboseName))
                        raise IkException("Unique Validate Failed: Key (%s) already exists. Plesae check %s." % (errorMsg1, tableVerboseName))
                uniqueValueList.append(rcUniqueValues)
        # validate from database
        for r in newRcs:
            self.__validateRc(r, ikTransactionModel, dataWithoutDeletedRcs)

    def __getModelUnique(self, rc) -> list:
        modelClass = rc.__class__
        updateFieldNames = self.__getModelFullUpdateFieldNames(rc)

        uniqueFieldsList = []
        for fieldName in updateFieldNames:
            modelField = modelClass._meta.get_field(fieldName)
            if modelField is None:
                raise IkValidateException("Model [%s] doesn't have field [%s]." % (modelClass._meta.label, fieldName))
            if modelField.unique:
                uniqueFieldsList.append([modelField.name])
        if modelClass._meta.unique_together is not None and len(modelClass._meta.unique_together) > 0:
            for ut in modelClass._meta.unique_together:
                if len(uniqueFieldsList) == 0:
                    uniqueFieldsList.append(list(ut))
                else:
                    found = True
                    for fields in uniqueFieldsList:
                        # check is the same or not
                        if len(ut) == len(fields):
                            for i in range(len(ut)):
                                if ut[i] not in fields:
                                    found = False
                                    break
                        else:
                            found = False
                            break
                    if not found:
                        uniqueFieldsList.append(list(ut))
        return uniqueFieldsList

    def __getFieldValues(self, rc, uniqueColumns) -> list:
        '''
            return [aaa,bb]
        '''
        values = []
        for name in uniqueColumns:
            values.append(self.__getFieldValue(rc, name))
        return values

    def __isTheSame(self, modelClass, uniqueFiledNames, values1, values2) -> bool:
        if len(values1) != len(values2):
            return False
        for i in range(len(values1)):
            v1, v2 = values1[i], values2[i]
            if v1 != v2:
                # check the data Type:
                modelField = modelClass._meta.get_field(uniqueFiledNames[i])
                if type(modelField) == models.DateField:
                    v1 = v1 if type(v1) == str else v1.strftime("%Y-%m-%d")
                    v2 = v2 if type(v2) == str else v2.strftime("%Y-%m-%d")
                    if v1 != v2:
                        return False
                    else:
                        continue
                elif type(modelField) == models.TimeField:
                    v1 = v1 if type(v1) == str else v1.strftime("%H:%M:%S")
                    v2 = v2 if type(v2) == str else v2.strftime("%H:%M:%S")
                    if v1 != v2:
                        return False
                    else:
                        continue
                elif type(modelField) == models.DateTimeField:
                    v1 = v1 if type(v1) == str else v1.strftime("%Y-%m-%d %H:%M:%S")
                    v2 = v2 if type(v2) == str else v2.strftime("%Y-%m-%d %H:%M:%S")
                    if v1 != v2:
                        return False
                    else:
                        continue
                return False
        return True
