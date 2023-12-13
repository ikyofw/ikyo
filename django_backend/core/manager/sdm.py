'''
Description: Screen Definition Manager
version: 
Author: YL.ik
Date: 2023-04-19 11:49:27
'''
import logging
import os
import sys
from django.apps import apps
from django.db.models.fields.related import ForeignKey

import core.core.fs as ikfs
import core.ui.ui as ikui
import core.ui.uidb as ikuidb
import core.ui.uiCache as ikuiCache
import core.utils.spreadsheet as ikSpreadsheet
import core.utils.modelUtils as modelUtils
from core.core.exception import IkException
from core.core.http import *
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.utils.langUtils import isNotNullBlank, isNullBlank
from core.utils import strUtils

import core.models as ikModels

logger = logging.getLogger('ikyo')


### Screen
# save Screen Detail
def saveScreen(self, screenSn, isNew, currentBtnClick) -> Boolean2:
    try:
        screenDtlFg = self.getRequestData().get("screenDtlFg", None)
        if screenDtlFg:
            sn = strUtils.stripStr(screenDtlFg.screen_sn)
            if strUtils.isEmpty(sn):
                return Boolean2(False, "Screen ID is mandatory, please check.")

            screenTitle = strUtils.stripStr(screenDtlFg.screen_title)
            if strUtils.isEmpty(screenTitle):
                return Boolean2(False, "Screen Title is mandatory, please check.")

            layoutType = strUtils.stripStr(screenDtlFg.layout_type)
            if strUtils.isEmpty(layoutType):
                return Boolean2(False, "Screen Layout Type is mandatory, please check.")

            classNm = strUtils.stripStr(screenDtlFg.class_nm)
            if strUtils.isEmpty(classNm):
                return Boolean2(False, "Screen Class Name is mandatory, please check.")
            try:
                viewClass = modelUtils.getModelClass(classNm)
            except Exception as e:
                return Boolean2(False, "The format of Screen Class Name is error: %s" % e)

            # validate screen SN
            validateRcs = ikModels.Screen.objects.all().values('screen_sn').distinct()
            if not strUtils.isEmpty(screenSn) and not isNew:  # update
                validateRcs = validateRcs.exclude(screen_sn=sn)
            validateSns = list(validateRcs.values_list('screen_sn', flat=True))
            if sn in validateSns:
                return Boolean2(False, sn + " is exists, please change.")

            if isNew and strUtils.isEmpty(screenSn):
                screenSn = sn
            ## check real modified
            # TODO

            if currentBtnClick:
                return __createNewRevScreen(self, screenSn, screenRc=screenDtlFg)

        return Boolean2(True, 'Nothing changed.')
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


def deleteScreen(self, screenSn) -> Boolean2:
    try:
        screenDtlFg = self.getRequestData().get("screenDtlFg", None)
        if screenDtlFg:
            screenRcs = ikModels.Screen.objects.filter(screen_sn__iexact=screenSn)
            screenFileRcs = []
            screenRecordsetRcs = []
            screenFieldGroupRcs = []
            screenFieldRcs = []
            screenFgLinkRcs = []
            screenFgHeaderFooterRcs = []
            for screenRc in screenRcs:
                screenRc.ik_set_status_delete()
                fileRcs = ikModels.ScreenFile.objects.filter(screen=screenRc)
                for i in fileRcs:
                    i.ik_set_status_delete()
                    screenFileRcs.append(i)
                recordsetRcs = ikModels.ScreenRecordset.objects.filter(screen=screenRc)
                for j in recordsetRcs:
                    j.ik_set_status_delete()
                    screenRecordsetRcs.append(j)
                fieldGroupRcs = ikModels.ScreenFieldGroup.objects.filter(screen=screenRc)
                for k in fieldGroupRcs:
                    k.ik_set_status_delete()
                    screenFieldGroupRcs.append(k)
                fieldRcs = ikModels.ScreenField.objects.filter(screen=screenRc)
                for l in fieldRcs:
                    l.ik_set_status_delete()
                    screenFieldRcs.append(l)
                fgLinkRcs = ikModels.ScreenFgLink.objects.filter(screen=screenRc)
                for m in fgLinkRcs:
                    m.ik_set_status_delete()
                    screenFgLinkRcs.append(m)
                fgHeaderFooterRcs = ikModels.ScreenFgHeaderFooter.objects.filter(screen=screenRc)
                for n in fgHeaderFooterRcs:
                    n.ik_set_status_delete()
                    screenFgHeaderFooterRcs.append(n)

            ptrn = IkTransaction(self)
            ptrn.add(screenFileRcs)
            ptrn.add(screenFgHeaderFooterRcs)
            ptrn.add(screenFgLinkRcs)
            ptrn.add(screenFieldRcs)
            ptrn.add(screenFieldGroupRcs)
            ptrn.add(screenRecordsetRcs)
            ptrn.add(screenRcs)
            b = ptrn.save()
            if not b.value:
                return b

            if len(screenFileRcs) > 0:
                fp = screenFileRcs[0].file_path
                for file in os.listdir(fp):
                    fp2 = os.path.join(fp, file)
                    if os.path.isfile(fp2) and screenRcs[0].screen_sn in file:
                        ikfs.deleteEmptyFolderAndParentFolder(fp2)
            return Boolean2(True, 'Deleted.')
        return Boolean2(True, 'Nothing deleted.')
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


def deleteLastScreen(self, screenSn) -> Boolean2:
    try:
        screenDtlFg = self.getRequestData().get("screenDtlFg", None)
        if screenDtlFg:
            screenRc = ikModels.Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            screenFileRcs = []
            screenRecordsetRcs = []
            screenFieldGroupRcs = []
            screenFieldRcs = []
            screenFgLinkRcs = []
            screenFgHeaderFooterRcs = []

            screenRc.ik_set_status_delete()
            fileRcs = ikModels.ScreenFile.objects.filter(screen=screenRc)
            for i in fileRcs:
                i.ik_set_status_delete()
                screenFileRcs.append(i)
            recordsetRcs = ikModels.ScreenRecordset.objects.filter(screen=screenRc)
            for j in recordsetRcs:
                j.ik_set_status_delete()
                screenRecordsetRcs.append(j)
            fieldGroupRcs = ikModels.ScreenFieldGroup.objects.filter(screen=screenRc)
            for k in fieldGroupRcs:
                k.ik_set_status_delete()
                screenFieldGroupRcs.append(k)
            fieldRcs = ikModels.ScreenField.objects.filter(screen=screenRc)
            for l in fieldRcs:
                l.ik_set_status_delete()
                screenFieldRcs.append(l)
            fgLinkRcs = ikModels.ScreenFgLink.objects.filter(screen=screenRc)
            for m in fgLinkRcs:
                m.ik_set_status_delete()
                screenFgLinkRcs.append(m)
            fgHeaderFooterRcs = ikModels.ScreenFgHeaderFooter.objects.filter(screen=screenRc)
            for n in fgHeaderFooterRcs:
                n.ik_set_status_delete()
                screenFgHeaderFooterRcs.append(n)

            ptrn = IkTransaction(self)
            ptrn.add(screenFileRcs)
            ptrn.add(screenFgHeaderFooterRcs)
            ptrn.add(screenFgLinkRcs)
            ptrn.add(screenFieldRcs)
            ptrn.add(screenFieldGroupRcs)
            ptrn.add(screenRecordsetRcs)
            ptrn.add(screenRc)
            b = ptrn.save()
            if not b.value:
                return b

            if len(screenFileRcs) > 0:
                fp = screenFileRcs[0].file_path
                fn = screenFileRcs[0].file_nm
                for file in os.listdir(fp):
                    fp2 = os.path.join(fp, file)
                    if os.path.isfile(fp2) and fn == file:
                        ikfs.deleteEmptyFolderAndParentFolder(fp2)
            return Boolean2(True, 'Deleted.')
        return Boolean2(True, 'Nothing deleted.')
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


def copyScreen(self, userID, screenSn) -> Boolean2:
    try:
        screenRc = ikModels.Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        originalScreenRc = ikModels.Screen.objects.filter(screen_sn__icontains=screenSn).order_by("-screen_sn").first()

        originalSeq = originalScreenRc.screen_sn[len(screenSn) + 5:]
        try:
            if isNullBlank(originalSeq):
                seq = 1
            else:
                seq = int(originalSeq) + 1
        except:
            seq = 1
        newSeq = "_New_%s" % "{:02d}".format(seq)
        screenRc.screen_sn = screenRc.screen_sn + newSeq
        screenRc.screen_title = screenRc.screen_title + newSeq
        screenRc.screen_dsc = screenRc.screen_dsc + newSeq
        screenRc.class_nm = screenRc.class_nm + newSeq
        if not isNullBlank(screenRc.api_url):
            screenRc.api_url = screenRc.api_url + newSeq 
        
        fileRc = ikModels.ScreenFile.objects.filter(screen=screenRc).first()
        filePath = fileRc.file_path
        if isNullBlank(filePath) or "\\" in filePath:
            filePath = __getImportScreenFilePath(screenRc.class_nm, screenRc.screen_sn)
        filename = '%s-v%s.xlsx' % (screenRc.screen_sn, '0')
        outputFile = os.path.join(filePath, filename)
        templateFileFolder = ikui.IkUI.getScreenFileTemplateFolder()
        templateFile = ikfs.getLastRevisionFile(templateFileFolder, 'template.xlsx')
        if isNullBlank(templateFile):
            logger.error("Template file does not exist in folder [%s]." % templateFileFolder.absolute())
            return Boolean2(False, 'Screen template file is not found. Please check.')
        if os.path.isfile(outputFile):
            os.remove(outputFile)
        ikuidb.screenDbWriteToExcel(screenRc, templateFile, outputFile)

        sp = ikSpreadsheet.SpreadsheetParser(outputFile)
        ikuidb._updateDatabaseWithExcelFiles(ikui.ScreenDefinition(name='',fullName='',filePath=outputFile, definition=sp.data), userID)
        self.setSessionParameters({"screenSN": screenRc.screen_sn})
        return Boolean2(True, 'Copied.')
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


### Recordset
# save Recordset Table
def saveScreenRecordsets(self, screenSn, currentBtnClick) -> Boolean2:
    try:
        screenRc = ikModels.Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        if screenRc is None:
            return Boolean2(False, screenSn + " does not exist, please ask administrator to check.")
        recordsetLists = self.getRequestData().get("recordsetListFg", None)

        # 1. validate screen
        validateScreenFg = saveScreen(self, screenSn, None, False)
        if not validateScreenFg.value:
            return validateScreenFg

        # hasUpdate = False
        uniqueCheckList = []
        if recordsetLists:
            for rc in recordsetLists:
                if rc.ik_is_status_delete():
                    # if delete check has related recordset
                    relateFgRc = ikModels.ScreenFieldGroup.objects.filter(screen=screenRc, recordset__id=rc.id).first()
                    if relateFgRc:
                        return Boolean2(False, rc.recordset_nm + " was used by field group: " + relateFgRc.fg_nm + ", please delete " + relateFgRc.fg_nm + " first.")
                    # hasUpdate = True
                    rc.ik_set_status_delete()
                else:
                    recordsetNm = strUtils.stripStr(rc.recordset_nm)
                    if strUtils.isEmpty(recordsetNm):
                        return Boolean2(False, "Recordset Name is mandatory, please check.")
                    if strUtils.isEmpty(rc.sql_fields):
                        rc.sql_fields = "*"
                        # if (rc.ik_is_status_retrieve()):
                        #     rc.ik_set_status_modified()
                    if strUtils.isEmpty(rc.sql_models):
                        return Boolean2(False, "Models is mandatory, please check.")
                    # check unique
                    if recordsetNm in uniqueCheckList:
                        return Boolean2(False, "Recordset Name is unique. Please check: " + recordsetNm)
                    uniqueCheckList.append(recordsetNm)

                    # if rc.ik_is_status_new() or rc.ik_is_status_modified():
                    #     hasUpdate = True

        # if hasUpdate and currentBtnClick:
        if currentBtnClick:
            return __createNewRevScreen(self, screenSn, screenRc=self.getRequestData().get("screenDtlFg", None), recordsetRcs=recordsetLists)

        return Boolean2(True, 'Nothing changed.')
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


### Field Group
# save field group
def saveFieldGroup(self, screenSn, isNew, currentBtnClick) -> Boolean2:
    try:
        screenRc = ikModels.Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        if screenRc is None:
            return Boolean2(False, screenSn + " does not exist, please ask administrator to check.")

        # _1. validate screen
        validateScreenFg = saveScreen(self, screenSn, None, False)
        if not validateScreenFg.value:
            return validateScreenFg
        # _2. validate recordsetFg
        validateRecordsetFg = saveScreenRecordsets(self, screenSn, False)
        if not validateRecordsetFg.value:
            return validateRecordsetFg

        ## 1. validate field group
        fieldGroupId = self.getSessionParameterInt("currentFgID")
        fieldGroupDtlFg = self.getRequestData().get("fieldGroupDtlFg", None)
        if fieldGroupDtlFg is None and currentBtnClick:
            logger.error("Save Field Group failed, get fieldGroupDtlFg error.")
            return Boolean2(False, "System error, please ask administrator to check.")

        if fieldGroupDtlFg:
            # put to end if user not input seq
            if strUtils.isEmpty(fieldGroupDtlFg.seq):
                fieldGroupDtlFg.seq = sys.maxsize
            # validate field group
            fgName = strUtils.stripStr(fieldGroupDtlFg.fg_nm)
            if strUtils.isEmpty(fgName):
                return Boolean2(False, "Field Group Name is mandatory, please check.")
            validateFgNmRcs = ikModels.ScreenFieldGroup.objects.filter(screen=screenRc)
            if not isNew and fieldGroupId:  # update
                validateFgNmRcs = validateFgNmRcs.exclude(id=fieldGroupId)
            validateFgNms = list(validateFgNmRcs.values_list('fg_nm', flat=True))
            if fgName in validateFgNms:
                return Boolean2(False, fgName + " is exists, please change.")

            fgTypeId = fieldGroupDtlFg.fg_type_id
            if strUtils.isEmpty(fgTypeId):
                return Boolean2(False, "Group Type is mandatory, please check.")

            # validate page type & page size
            if not strUtils.isEmpty(fieldGroupDtlFg.data_page_type) and strUtils.isEmpty(fieldGroupDtlFg.data_page_size):
                return Boolean2(False, "Page Size is mandatory, please check.")
            if strUtils.isEmpty(fieldGroupDtlFg.data_page_type) and not strUtils.isEmpty(fieldGroupDtlFg.data_page_size):
                return Boolean2(False, "Page Type is mandatory, please check.")

            ## 2.validate fields
            fieldListFg = self.getRequestData().get("fieldListFg", None)
            uniqueCheckList = []
            if fieldListFg:
                fieldSeq = 1
                for rc in fieldListFg:
                    if not rc.ik_is_status_delete():
                        # auto set field name & field seq
                        rc.seq = strUtils.stripStr(rc.seq)
                        rc.field_nm = strUtils.stripStr(rc.field_nm)
                        if strUtils.isEmpty(rc.field_nm):
                            rc.field_nm = fieldGroupDtlFg.fg_nm + "_" + str(fieldSeq) if strUtils.isEmpty(rc.seq) else str(rc.seq)
                        # check field name unique
                        if rc.field_nm in uniqueCheckList:
                            return Boolean2(False, "Field Name is unique. Please check: " + rc.field_nm)
                        uniqueCheckList.append(rc.field_nm)

                        if strUtils.isEmpty(rc.seq):
                            rc.seq = fieldSeq
                        else:
                            rc.seq = float(rc.seq) - 0.5
                        fieldSeq += 1
                        # if not rc.ik_is_status_retrieve():
                        #     rc.visible = not rc.visible  # page is hidden
                        #     rc.editable = not rc.editable  # page is not editable

            # check real modified
            # TODO

        if currentBtnClick:
            return __createNewRevScreen(self,
                                        screenSn,
                                        screenRc=self.getRequestData().get("screenDtlFg", None),
                                        recordsetRcs=self.getRequestData().get("recordsetListFg", None),
                                        fieldGroupRc=fieldGroupDtlFg,
                                        fieldRcs=fieldListFg)

        return Boolean2(True, 'Nothing changed.')
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


# delete field group
def deleteFieldGroup(self, screenSn, fieldGroupId) -> Boolean2:
    try:
        fieldGroupRc = ikModels.ScreenFieldGroup.objects.filter(id=fieldGroupId).first()
        if fieldGroupRc is None:
            return Boolean2(False, "The ID(" + str(fieldGroupId) + ") of Field Group does not exist, please check.")
        fieldRcs = ikModels.ScreenField.objects.filter(screen=fieldGroupRc.screen, field_group=fieldGroupRc)
        return __createNewRevScreen(self, screenSn, fieldGroupRc.screen, fieldGroupRc=fieldGroupRc, fieldRcs=fieldRcs)
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


def saveSubScreen(self, screenSn, screenDfn):
    try:
        screenRc = ikModels.Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        if screenRc is None:
            return Boolean2(False, screenSn + " does not exist, please ask administrator to check.")
        for i in screenDfn:
            i.screen_id = screenRc.id
            fgs = i.field_group_nms
            fgNmList = []
            if isNullBlank(fgs):
                fgNmList = ikModels.ScreenFieldGroup.objects.filter(screen=screenRc).values_list('fg_nm', flat=True)
            else:
                fgList = [fg.strip() for fg in fgs.split(',')]
                for j in fgList:
                    fgRc = ikModels.ScreenFieldGroup.objects.filter(screen=screenRc, fg_nm=j).first()
                    if not strUtils.isEmpty(fgRc):
                        fgNmList.append(fgRc.fg_nm)
            i.field_group_nms = ", ".join(fgNmList)

        return __createNewRevScreen(self, screenSn, screenRc, subScreenRcs=screenDfn)
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


### Field Group Link
# save field group link
def saveFgLink(self, screenSn, isNew, currentBtnClick) -> Boolean2:
    try:
        screenRc = ikModels.Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        if screenRc is None:
            return Boolean2(False, screenSn + " does not exist, please ask administrator to check.")

        fgLinkId = self.getSessionParameterInt("currentFgLinkID")
        fgLinkDtlFg = self.getRequestData().get("fgLinkDtlFg", None)
        if fgLinkDtlFg is None and currentBtnClick:
            logger.error("Save Field Group failed, get fgLinkDtlFg error.")
            return Boolean2(False, "System error, please ask administrator to check.")

        if fgLinkDtlFg:
            # _1. validate screen
            validateScreenFg = saveScreen(self, screenSn, None, False)
            if not validateScreenFg.value:
                return validateScreenFg
            # _2. validate recordsetFg
            validateRecordsetFg = saveScreenRecordsets(self, screenSn, False)
            if not validateRecordsetFg.value:
                return validateRecordsetFg
            # _3. validate field group
            validateFieldGroupFg = saveFieldGroup(self, screenSn, False, False)
            if not validateFieldGroupFg.value:
                return validateFieldGroupFg

            # validate field group
            fgId = strUtils.stripStr(fgLinkDtlFg.field_group_id)
            if strUtils.isEmpty(fgId):
                return Boolean2(False, "Field Group Name is mandatory, please check.")
            pFgId = strUtils.stripStr(fgLinkDtlFg.parent_field_group_id)
            if strUtils.isEmpty(pFgId):
                return Boolean2(False, "Parent Field Group Name is mandatory, please check.")
            if fgId == pFgId:
                # TODO if need more relationship validate
                return Boolean2(False, "Field Group Name and Parent Field Group Name has no relationships.")
            parentKey = strUtils.stripStr(fgLinkDtlFg.parent_key)
            if strUtils.isEmpty(parentKey):
                return Boolean2(False, "Parent Key is mandatory, please check.")
            localKey = strUtils.stripStr(fgLinkDtlFg.local_key)
            if strUtils.isEmpty(localKey):
                return Boolean2(False, "Local Key is mandatory, please check.")
            ## XH 2023-04-25 START

            validateRc = ikModels.ScreenFgLink.objects.filter(screen__id=screenRc.id, field_group__id=fgId, parent_field_group__id=pFgId)
            if len(validateRc) > 0 and not isNew and fgLinkId:  # if modified, except himself
                validateRc = validateRc.exclude(id=fgLinkId)
            validateRc = validateRc.first() if len(validateRc) > 0 else None
            if validateRc is not None and validateRc.parent_key == parentKey and validateRc.local_key == localKey:
                return Boolean2(False, "This relationship has exists, please check.")
            ## XH 2023-04-25 END

            # check real modified
            # TODO

        if currentBtnClick:
            return __createNewRevScreen(self,
                                        screenSn,
                                        screenRc=self.getRequestData().get("screenDtlFg", None),
                                        recordsetRcs=self.getRequestData().get("recordsetListFg", None),
                                        fieldGroupRc=self.getRequestData().get("fieldGroupDtlFg", None),
                                        fieldRcs=self.getRequestData().get("fieldListFg", None),
                                        fgLinkRc=fgLinkDtlFg)

        return Boolean2(True, 'Nothing changed.')
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


# delete field group link
def deleteFgLink(self, screenSn, fgLinkId) -> Boolean2:
    try:
        fgLinkRc = ikModels.ScreenFgLink.objects.filter(id=fgLinkId).first()
        if fgLinkRc is None:
            return Boolean2(False, "The ID(" + str(fgLinkId) + ") of Field Group Link does not exist, please check.")

        return __createNewRevScreen(self, screenSn, fgLinkRc.screen, fgLinkRc=fgLinkRc)
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


### Header And Footer
# save table header and footer
def saveFgHeaderFooter(self, screenSn, isNew, currentBtnClick) -> Boolean2:
    try:
        screenRc = ikModels.Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        if screenRc is None:
            return Boolean2(False, screenSn + " does not exist, please ask administrator to check.")

        fgHeaderFooterId = self.getSessionParameterInt("currentFgHeaderFooterID")
        fgHeaderFooterDtlFg = self.getRequestData().get("fgHeaderFooterDtlFg", None)
        if fgHeaderFooterDtlFg is None:
            logger.error("Save Field Group failed, get fgHeaderFooterDtlFg error.")
            return Boolean2(False, "System error, please ask administrator to check.")

        # _1. validate screen
        validateScreenFg = saveScreen(self, screenSn, None, False)
        if not validateScreenFg.value:
            return validateScreenFg
        # _2. validate recordsetFg
        validateRecordsetFg = saveScreenRecordsets(self, screenSn, False)
        if not validateRecordsetFg.value:
            return validateRecordsetFg
        # _3. validate field group
        validateFieldGroupFg = saveFieldGroup(self, screenSn, False, False)
        if not validateFieldGroupFg.value:
            return validateFieldGroupFg
        # _4. validate field group link
        validateFgLinkFg = saveFgLink(self, screenSn, False, False)
        if not validateFgLinkFg.value:
            return validateFgLinkFg

        # validate field group
        fgId = strUtils.stripStr(fgHeaderFooterDtlFg.field_group_id)
        if strUtils.isEmpty(fgId):
            return Boolean2(False, "Field Group Name is mandatory, please check.")
        fId = strUtils.stripStr(fgHeaderFooterDtlFg.field_id)
        if strUtils.isEmpty(fId):
            return Boolean2(False, "Field Name is mandatory, please check.")
        headerLevel1 = strUtils.stripStr(fgHeaderFooterDtlFg.header_level1)
        ## XH 2023-04-25 START
        # if strUtils.isEmpty(headerLevel1):
        #     return Boolean2(False, "Header level 1 is mandatory, please check.")
        headerLevel2 = strUtils.stripStr(fgHeaderFooterDtlFg.header_level2)
        # if strUtils.isEmpty(headerLevel2):
        #     return Boolean2(False, "Header level 2 is mandatory, please check.")
        headerLevel3 = strUtils.stripStr(fgHeaderFooterDtlFg.header_level3)
        # if strUtils.isEmpty(headerLevel3):
        #     return Boolean2(False, "Header level 3 is mandatory, please check.")
        footer = strUtils.stripStr(fgHeaderFooterDtlFg.footer)

        validateRc = ikModels.ScreenFgHeaderFooter.objects.filter(screen__id=screenRc.id, field_group__id=fgId, field__id=fId)
        if len(validateRc) > 0 and not isNew and fgHeaderFooterId:  # if modified, except himself
            validateRc = validateRc.exclude(id=fgHeaderFooterId)
        validateRc = validateRc.first() if len(validateRc) > 0 else None
        if validateRc is not None and validateRc.header_level1 == headerLevel1 and validateRc.header_level2 == headerLevel2 and validateRc.header_level3 == headerLevel3\
            and validateRc.footer == footer:
            return Boolean2(False, "This record has exists, please check.")
        ## XH 2023-04-25 END

        # check real modified
        # TODO

        if currentBtnClick:
            return __createNewRevScreen(self,
                                        screenSn,
                                        screenRc=self.getRequestData().get("screenDtlFg", None),
                                        recordsetRcs=self.getRequestData().get("recordsetListFg", None),
                                        fieldGroupRc=self.getRequestData().get("fieldGroupDtlFg", None),
                                        fieldRcs=self.getRequestData().get("fieldListFg", None),
                                        fgLinkRc=self.getRequestData().get("fgLinkDtlFg", None),
                                        fgHeaderFooterRc=fgHeaderFooterDtlFg)

        return Boolean2(True, 'Nothing changed.')
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


# delete table header and footer
def deleteFgHeaderFooter(self, screenSn, fgHeaderFooterId) -> Boolean2:
    try:
        fgHeaderFooterRc = ikModels.ScreenFgHeaderFooter.objects.filter(id=fgHeaderFooterId).first()
        if fgHeaderFooterRc is None:
            return Boolean2(False, "The ID(" + str(fgHeaderFooterId) + ") of Header And Footer table does not exist, please check.")

        return __createNewRevScreen(self, screenSn, fgHeaderFooterRc.screen, fgHeaderFooterRc=fgHeaderFooterRc)
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


# whole screen
def __createNewRevScreen(self, screenSn, screenRc: ikModels.Screen, recordsetRcs=None, fieldGroupRc=None, fieldRcs=None, subScreenRcs=None, fgLinkRc=None, fgHeaderFooterRc=None) -> Boolean2:
    try:
        # get the last rev screen
        lastRevScreenRc = ikModels.Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()

        #===== 1. new Screen
        if screenRc:
            try:
                viewClass = modelUtils.getModelClass(screenRc.class_nm)
            except Exception as e:
                return Boolean2(False, "The format of Class Name in [%s] is error: %s" % (screenSn, e))
            if lastRevScreenRc:
                screenRc.rev = lastRevScreenRc.rev + 1
            else:
                screenRc.rev = 0  # the first rev screen
            screenRc.ik_set_status_new()
            screenRc.id = ikModels.Screen().assignPrimaryID()

        isNewScreen = True if self.getSessionParameterBool("isNewScreen") else False
        recordsetDBRcs = []
        fieldGroupDBRcs = []
        fgFieldDBRcs = []
        subScreenDBRcs = []
        fgLinkDBRcs = []
        fgHeaderFooterDBRcs = []
        screenFileRc = []
        if not isNewScreen:  # just new screen
            #===== 2. new Recordset records
            # if not data, get the last rev screen's records
            if (recordsetRcs is None or len(recordsetRcs) <= 0) and lastRevScreenRc:
                recordsetRcs = ikModels.ScreenRecordset.objects.filter(screen=lastRevScreenRc).order_by("id")
            recordsetNewIdMap = {}  # **import: for create new field group
            for rc in recordsetRcs:
                if not rc.ik_is_status_delete():
                    ## _import if modified recordset_nm need update field group recordset id
                    orgRecordsetNm = None
                    if rc.ik_is_status_modified():
                        orgRecordsetNm = ikModels.ScreenRecordset.objects.filter(id=rc.id).first().recordset_nm
                        if rc.recordset_nm != orgRecordsetNm:
                            recordsetNewIdMap.update({orgRecordsetNm: rc.id})
                    rc.ik_set_status_new()
                    rc.screen = screenRc
                    rc.id = ikModels.ScreenRecordset().assignPrimaryID()
                    recordsetNewIdMap.update({rc.recordset_nm: rc.id})
                    if not strUtils.isEmpty(orgRecordsetNm):
                        recordsetNewIdMap.update({orgRecordsetNm: rc.id})
                    recordsetDBRcs.append(rc)

            #===== 3. new Field Group,  4. new Field records
            fieldGroupNewIdMap = {}
            fgFieldNewIdMap = {}
            isDeleteFieldGroup = True if self.getSessionParameterBool("isDeleteFieldGroup") else False  # delete current field group
            # copy the last rev screen's field group
            lastRevFieldGroupRcs = ikModels.ScreenFieldGroup.objects.filter(screen=lastRevScreenRc).order_by("seq")
            currentFgId = self.getSessionParameterInt("currentFgID")
            newCurrentFgId = None
            curSeq = 100
            for fgRc in lastRevFieldGroupRcs:
                if fgRc.id == currentFgId and isDeleteFieldGroup:  # delete.
                    continue
                if not strUtils.isEmpty(currentFgId) and fieldGroupRc and fgRc.id == currentFgId and not isDeleteFieldGroup:  # modify current field group info
                    ## _import if modified field group name need update fg link and header footer table id
                    orgFgNm = ikModels.ScreenFieldGroup.objects.filter(id=fgRc.id).first().fg_nm
                    fieldGroupRc.ik_set_status_new()
                    fieldGroupRc.id = ikModels.ScreenFieldGroup().assignPrimaryID()
                    newCurrentFgId = fieldGroupRc.id  # get new current field group id
                    curSeq = fieldGroupRc.seq
                    # _import: use new screenRc and recordset(if have)
                    fieldGroupRc.screen = screenRc
                    fieldGroupRc.recordset_id = recordsetNewIdMap.get(fieldGroupRc.recordset.recordset_nm) if fieldGroupRc.recordset else None
                    if fieldGroupRc.fg_nm != orgFgNm:
                        fieldGroupNewIdMap.update({orgFgNm: fieldGroupRc.id})
                    fieldGroupNewIdMap.update({fieldGroupRc.fg_nm: fieldGroupRc.id})
                    if fieldRcs:
                        fieldRcs.sort(key=lambda obj: obj.seq)  # sort fields
                        seq1 = 1
                        for fRc in fieldRcs:
                            if not fRc.ik_is_status_delete():
                                ## _import if modified field name need update header and footer field id
                                orgFieldNm = None
                                if fRc.ik_is_status_modified():
                                    orgFieldNm = ikModels.ScreenField.objects.filter(id=fRc.id).first().field_nm
                                    if fRc.field_nm != orgFieldNm:
                                        fgFieldNewIdMap.update({fRc.field_group.fg_nm + "-" + orgFieldNm: fRc.id})
                                # if fRc.ik_is_status_modified():
                                #     fRc.visible = not fRc.visible if fRc.visible else True  # in page is use hidden
                                fRc.ik_set_status_new()
                                fRc.field_group = fieldGroupRc
                                fRc.id = ikModels.ScreenField().assignPrimaryID()
                                fRc.seq = seq1
                                # _import: use new screenRc and field group
                                fRc.screen = screenRc
                                fRc.field_group_id = fieldGroupNewIdMap.get(fRc.field_group.fg_nm)
                                fgFieldNewIdMap.update({fRc.field_group.fg_nm + "-" + fRc.field_nm: fRc.id})
                                if not strUtils.isEmpty(orgFieldNm):
                                    fgFieldNewIdMap.update({fRc.field_group.fg_nm + "-" + orgFieldNm: fRc.id})
                                fgFieldDBRcs.append(fRc)
                                seq1 += 1
                    fieldGroupDBRcs.append(fieldGroupRc)
                else:  # copy the last rev screen's field group
                    # get last rev fields
                    lastRevFieldRcs = ikModels.ScreenField.objects.filter(screen=lastRevScreenRc, field_group=fgRc).order_by("seq")
                    fgRc.ik_set_status_new()
                    fgRc.screen = screenRc
                    fgRc.id = ikModels.ScreenFieldGroup().assignPrimaryID()
                    if fgRc.seq >= curSeq:
                        fgRc.seq += 1
                    # _import: use new screenRc and recordset(if have)
                    fgRc.screen = screenRc
                    fgRc.recordset_id = recordsetNewIdMap.get(fgRc.recordset.recordset_nm) if fgRc.recordset else None
                    fieldGroupNewIdMap.update({fgRc.fg_nm: fgRc.id})
                    fSeq = 1
                    for fRc in lastRevFieldRcs:
                        fRc.ik_set_status_new()
                        fRc.field_group = fgRc
                        fRc.id = ikModels.ScreenField().assignPrimaryID()
                        fRc.seq = fSeq
                        # _import: use new screenRc and field group
                        fRc.screen = screenRc
                        fRc.field_group_id = fieldGroupNewIdMap.get(fRc.field_group.fg_nm)
                        fgFieldNewIdMap.update({fRc.field_group.fg_nm + "-" + fRc.field_nm: fRc.id})
                        fgFieldDBRcs.append(fRc)
                        fSeq += 1
                    fieldGroupDBRcs.append(fgRc)

            # create new field group
            if fieldGroupRc and strUtils.isEmpty(currentFgId) and not isDeleteFieldGroup:
                fieldGroupRc.ik_set_status_new()
                fieldGroupRc.id = ikModels.ScreenFieldGroup().assignPrimaryID()
                newCurrentFgId = fieldGroupRc.id
                # _import: use new screenRc and recordset(if have)
                fieldGroupRc.screen = screenRc
                fieldGroupRc.recordset_id = recordsetNewIdMap.get(fieldGroupRc.recordset.recordset_nm) if fieldGroupRc.recordset else None
                fieldGroupDBRcs.append(fieldGroupRc)
                fieldGroupNewIdMap.update({fieldGroupRc.fg_nm: fieldGroupRc.id})
                if fieldRcs:
                    fieldRcs.sort(key=lambda obj: obj.seq)  # sort fields
                    fSeq = 1
                    for fRc in fieldRcs:
                        if not fRc.ik_is_status_delete():
                            fRc.ik_set_status_new()
                            fRc.field_group = fieldGroupRc
                            fRc.id = ikModels.ScreenField().assignPrimaryID()
                            # fRc.visible = not fRc.visible if fRc.visible else True  # in page is use hidden
                            fRc.seq = fSeq
                            # _import: use new screenRc and field group
                            fRc.screen = screenRc
                            fRc.field_group_id = fieldGroupNewIdMap.get(fRc.field_group.fg_nm)
                            fgFieldNewIdMap.update({fRc.field_group.fg_nm + "-" + fRc.field_nm: fRc.id})
                            fgFieldDBRcs.append(fRc)
                            fSeq += 1

            # sort field Group
            if len(fieldGroupDBRcs) > 0:
                fieldGroupDBRcs.sort(key=lambda obj: obj.seq)
                fgSeq = 1
                for fgRc in fieldGroupDBRcs:
                    fgRc.seq = fgSeq
                    fgSeq += 1
            self.setSessionParameters({"currentFgID": newCurrentFgId})  # for get new current field group id

            #===== 5. new Sub Screen
            # if not data, get the last rev screen's records
            if (subScreenRcs is None or len(subScreenRcs) <= 0) and lastRevScreenRc:
                subScreenRcs = ikModels.ScreenDfn.objects.filter(screen=lastRevScreenRc).order_by("id")
            for rc in subScreenRcs:
                if not rc.ik_is_status_delete():
                    ## _import if modified recordset_nm need update field group recordset id
                    rc.ik_set_status_new()
                    rc.screen = screenRc
                    rc.id = ikModels.ScreenDfn().assignPrimaryID()
                    subScreenDBRcs.append(rc)

            #===== 6. new Field Table Link
            isDeleteFgLink = True if self.getSessionParameterBool("isDeleteFgLink") else False  # delete current field group link
            # copy the last rev screen's field group link
            lastRevFgLinkRcs = ikModels.ScreenFgLink.objects.filter(screen=lastRevScreenRc).order_by("id")
            currentFgLinkId = self.getSessionParameterInt("currentFgLinkID")
            newCurrentFgLinkId = None
            for rc in lastRevFgLinkRcs:
                if rc.id == currentFgLinkId and isDeleteFgLink:
                    continue
                if not strUtils.isEmpty(currentFgLinkId) and fgLinkRc and rc.id == currentFgLinkId and not isDeleteFgLink:  # modify current field group link info
                    fgLinkRc.ik_set_status_new()
                    fgLinkRc.id = ikModels.ScreenFgLink().assignPrimaryID()
                    newCurrentFgLinkId = fgLinkRc.id  # for get new current field group link id
                    # _import: use new screenRc and field group
                    fgLinkRc.screen = screenRc
                    fgLinkRc.field_group_id = fieldGroupNewIdMap.get(fgLinkRc.field_group.fg_nm)
                    fgLinkRc.parent_field_group_id = fieldGroupNewIdMap.get(fgLinkRc.parent_field_group.fg_nm)
                    fgLinkDBRcs.append(fgLinkRc)
                else:  # copy the last rev screen's field group
                    rc.ik_set_status_new()
                    rc.id = ikModels.ScreenFgLink().assignPrimaryID()
                    # _import: use new screenRc and field group
                    rc.screen = screenRc
                    rc.field_group_id = fieldGroupNewIdMap.get(rc.field_group.fg_nm)
                    rc.parent_field_group_id = fieldGroupNewIdMap.get(rc.parent_field_group.fg_nm)
                    fgLinkDBRcs.append(rc)

            ## XH 2023-04-25 START
            # create new field group
            if fgLinkRc and strUtils.isEmpty(currentFgLinkId) and not isDeleteFgLink:
                fgLinkRc.ik_set_status_new()
                fgLinkRc.id = ikModels.ScreenFgLink().assignPrimaryID()
                newCurrentFgLinkId = fgLinkRc.id  # for get new current field group link id
                # _import: use new screenRc and field group
                fgLinkRc.screen = screenRc
                fgLinkRc.field_group_id = fieldGroupNewIdMap.get(fgLinkRc.field_group.fg_nm)
                fgLinkRc.parent_field_group_id = fieldGroupNewIdMap.get(fgLinkRc.parent_field_group.fg_nm)
                fgLinkDBRcs.append(fgLinkRc)
            ## XH 2023-04-25 END
            self.setSessionParameters({"currentFgLinkID": newCurrentFgLinkId})  # for get new current field group link id

            #===== 7. new Header And Footer Table
            isDeleteFgHeaderFooter = True if self.getSessionParameterBool("isDeleteFgHeaderFooter") else False  # delete current header and footer table
            # copy the last rev screen's header footer table
            lastRevFgHeaderFooterRcs = ikModels.ScreenFgHeaderFooter.objects.filter(screen=lastRevScreenRc).order_by("id")
            currentFgHeaderFooterId = self.getSessionParameterInt("currentFgHeaderFooterID")
            newCurrentFgHeaderFooterId = None
            for rc in lastRevFgHeaderFooterRcs:
                if rc.id == currentFgHeaderFooterId and isDeleteFgHeaderFooter:  # delete  Delete the rows related to header footer table when deleting field group.
                    continue
                if not strUtils.isEmpty(currentFgHeaderFooterId
                                        ) and fgHeaderFooterRc and rc.id == currentFgHeaderFooterId and not isDeleteFgHeaderFooter:  # modify current header footer table info
                    fgHeaderFooterRc.ik_set_status_new()
                    fgHeaderFooterRc.id = ikModels.ScreenFgHeaderFooter().assignPrimaryID()
                    newCurrentFgHeaderFooterId = fgHeaderFooterRc.id  # for get new current header and footer table id
                    # _import: use new screenRc and field group and field
                    fgHeaderFooterRc.screen = screenRc
                    fgHeaderFooterRc.field_id = fgFieldNewIdMap.get(fgHeaderFooterRc.field_group.fg_nm + "-" + fgHeaderFooterRc.field.field_nm)
                    fgHeaderFooterRc.field_group_id = fieldGroupNewIdMap.get(fgHeaderFooterRc.field_group.fg_nm)
                    fgHeaderFooterDBRcs.append(fgHeaderFooterRc)
                else:  # copy the last rev screen's header footer table
                    rc.ik_set_status_new()
                    rc.id = ikModels.ScreenFgHeaderFooter().assignPrimaryID()
                    # _import: use new screenRc and field group and field
                    rc.screen = screenRc
                    rc.field_id = fgFieldNewIdMap.get(rc.field_group.fg_nm + "-" + rc.field.field_nm)
                    rc.field_group_id = fieldGroupNewIdMap.get(rc.field_group.fg_nm)
                    fgHeaderFooterDBRcs.append(rc)

            ## XH 2023-04-25 START
            if fgHeaderFooterRc and strUtils.isEmpty(currentFgHeaderFooterId) and not isDeleteFgHeaderFooter:
                fgHeaderFooterRc.ik_set_status_new()
                fgHeaderFooterRc.id = ikModels.ScreenFgHeaderFooter().assignPrimaryID()
                newCurrentFgHeaderFooterId = fgHeaderFooterRc.id  # for get new current header and footer table id
                # _import: use new screenRc and field group and field
                fgHeaderFooterRc.screen = screenRc
                fgHeaderFooterRc.field_id = fgFieldNewIdMap.get(fgHeaderFooterRc.field_group.fg_nm + "-" + fgHeaderFooterRc.field.field_nm)
                fgHeaderFooterRc.field_group_id = fieldGroupNewIdMap.get(fgHeaderFooterRc.field_group.fg_nm)
                fgHeaderFooterDBRcs.append(fgHeaderFooterRc)
            ## XH 2023-04-25 END
            self.setSessionParameters({"currentFgHeaderFooterID": newCurrentFgHeaderFooterId})  # for get new current header and footer table id

        ptrn = IkTransaction(self)
        ptrn.add(screenRc)
        ptrn.add(recordsetDBRcs)
        ptrn.add(fieldGroupDBRcs)
        ptrn.add(fgFieldDBRcs)
        ptrn.add(subScreenDBRcs)
        ptrn.add(fgLinkDBRcs)
        ptrn.add(fgHeaderFooterDBRcs)
        # ptrn.add(screenFileRc)
        b = ptrn.save()
        if b.value:
            ## XH 2023-05-08 START
            lastRevScreenRc = ikModels.Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            filePath = __getImportScreenFilePath(lastRevScreenRc.class_nm, lastRevScreenRc.screen_sn)
            filename = '%s-v%s.xlsx' % (screenSn, lastRevScreenRc.rev)
            outputFile = os.path.join(filePath, filename)
            templateFileFolder = ikui.IkUI.getScreenFileTemplateFolder()
            templateFile = ikfs.getLastRevisionFile(templateFileFolder, 'template.xlsx')
            if isNullBlank(templateFile):
                logger.error("Template file does not exist in folder [%s]." % templateFileFolder.absolute())
                return Boolean2(False, 'Screen template file is not found. Please check.')
            if os.path.isfile(outputFile):
                os.remove(outputFile)
            c = ikuidb.screenDbWriteToExcel(lastRevScreenRc, templateFile, outputFile)
            if not c.value:
                logger.error("Screen [%s] excel file generation failed. Please check the database or the template file used for generating the Excel." % screenSn)
                return c
            else:
                # save screen file
                screenFileRc = ikModels.ScreenFile()
                screenFileRc.ik_set_status_new()
                screenFileRc.screen = lastRevScreenRc
                screenFileRc.file_nm = filename
                screenFileRc.file_size = os.path.getsize(outputFile)
                screenFileRc.file_path = filePath
                screenFileRc.file_dt = datetime.datetime.now()
                screenFileRc.file_md5 = ikuidb._getExcelMD5(outputFile)
                screenFileRc.rmk = "Saved on Screen Definition"

                ptrn = IkTransaction(self)
                ptrn.add(screenFileRc)
                b = ptrn.save()
                if not b.value:
                    return b
                
                # 在缓存中保存新的页面的定义
                screenDefinition = ikui.IkUI._getScreenDefinitionFromDB(screenRc.screen_sn)
                ikuiCache.updatePageDefinitionCache(screenRc.screen_sn, screenDefinition)
            ## XH 2023-05-08 End

            if isNewScreen:
                self.setSessionParameters({"screenSN": screenSn})
            return Boolean2(True, 'Saved.')
        else:
            logger.debug(b.data)
            # return Boolean2(False, 'Save failure.')
            return Boolean2(False, b.data)
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


## XH 2023-04-24 START
def getFieldDBKeys(screenRc, field_group):
    data = []
    try:
        if field_group:
            recordset = ikModels.ScreenFieldGroup.objects.filter(screen=screenRc, fg_nm=field_group.fg_nm).first().recordset
            sql_models = ikModels.ScreenRecordset.objects.filter(screen=screenRc, recordset_nm=recordset.recordset_nm).first().sql_models
            sql_models = sql_models.split('.')
            ModelClass = apps.get_model(sql_models[0], sql_models[-1])
            for field in ModelClass._meta.get_fields():
                if field.auto_created:
                    continue
                if isinstance(field, ForeignKey):
                    data.append(field.name + '_id')
                elif hasattr(field, 'name'):
                    data.append(field.name)
    except Exception as e:
        logger.error(e, exc_info=True)
    finally:
        return data
## XH 2023-04-24 END

def __getImportScreenFilePath(classNm, menuNm):
    try:
        viewClass = modelUtils.getModelClass(classNm)
        ss = classNm.split('.')
        subPath = os.path.join('sys', 'views', ss[0])
        return ikfs.getRelativeVarFolder(subPath=subPath)
    except Exception as e:
        return Boolean2(False, "The format of Class Name in [%s] is error: %s" % (menuNm, e))