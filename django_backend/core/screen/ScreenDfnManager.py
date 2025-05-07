'''
Description: Screen Definition Manager
version: 
Author: YL
Date: 2023-04-19 11:49:27
'''
import sys
import time
import os
from pathlib import Path

from django.apps import apps
from django.db.models.fields.related import ForeignKey

import core.ui.ui as ikui
import core.ui.uiCache as ikuiCache
import core.ui.uidb as ikuidb
import core.utils.modelUtils as modelUtils
import core.utils.spreadsheet as ikSpreadsheet
import core.utils.strUtils as strUtils
from core.log.logger import logger
from core.core.exception import IkException
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.models import *
from core.utils.langUtils import isNotNullBlank, isNullBlank


NO_PARAMETERS_WIDGET = [ikui.SCREEN_FIELD_WIDGET_PLUGIN, ikui.SCREEN_FIELD_WIDGET_HTML, ikui.SCREEN_FIELD_WIDGET_PASSWORD]
PARAMETERS_NOT_REQUIRED_FOR_WIDGET = {
    ikui.SCREEN_FIELD_WIDGET_LABEL: ['stateNumber', 'multiple', 'icon', 'type', 'onChange', 'dialog'],
    ikui.SCREEN_FIELD_WIDGET_TEXT_BOX: ['stateNumber', 'multiple', 'icon', 'type', 'recordset', 'data', 'dataUrl', 'values', 'onChange', 'dialog'],
    ikui.SCREEN_FIELD_WIDGET_DATE_BOX: ['stateNumber', 'multiple', 'icon', 'type', 'recordset', 'data', 'dataUrl', 'values', 'onChange', 'dialog'],
    ikui.SCREEN_FIELD_WIDGET_COMBO_BOX: ['format', 'stateNumber', 'multiple', 'icon', 'type', 'dialog'],
    ikui.SCREEN_FIELD_WIDGET_ADVANCED_SELECTION: ['format', 'stateNumber', 'multiple', 'type'],
    ikui.SCREEN_FIELD_WIDGET_CHECK_BOX: ['format', 'icon', 'type', 'recordset', 'data', 'dataUrl', 'values', 'onChange', 'dialog'],
    ikui.SCREEN_FIELD_WIDGET_BUTTON: ['format', 'stateNumber', 'recordset', 'data', 'dataUrl', 'values', 'onChange'],
    ikui.SCREEN_FIELD_WIDGET_ICON_AND_TEXT: ['format', 'stateNumber', 'recordset', 'data', 'dataUrl', 'values', 'onChange'],
    ikui.SCREEN_FIELD_WIDGET_FILE: ['format', 'stateNumber', 'icon', 'type', 'recordset', 'data', 'dataUrl', 'values', 'onChange', 'dialog']
}


# Screen
# save Screen Detail
def saveScreen(self, screenSn, isNew, currentBtnClick) -> Boolean2:
    try:
        screenDtlFg = self.getRequestData().get("screenDtlFg", None)
        screenDtlFg: Screen
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

            appNm = strUtils.stripStr(screenDtlFg.app_nm)
            if strUtils.isEmpty(appNm):
                return Boolean2(False, "Screen App Name is mandatory, please check.")

            classNm = strUtils.stripStr(screenDtlFg.class_nm)
            if isNotNullBlank(classNm) and appNm not in classNm:
                return Boolean2(False, "Screen Class Name must contain App Name, please check.")
            if isNotNullBlank(classNm) and sn not in classNm:
                return Boolean2(False, "Screen Class Name must contain Screen SN, please check.")

            b = __is_model_class_exists(appNm, sn, classNm)
            if not b.value:
                return b

            # validate screen SN
            validateRcs = Screen.objects.all().values('screen_sn').distinct()
            if not strUtils.isEmpty(screenSn) and not isNew:  # update
                validateRcs = validateRcs.exclude(screen_sn=sn)
            validateSns = list(validateRcs.values_list('screen_sn', flat=True))
            if sn in validateSns:
                return Boolean2(False, sn + " is exists, please change.")

            if isNew and strUtils.isEmpty(screenSn):
                screenSn = sn
            # check real modified
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
            screenRcs = Screen.objects.filter(screen_sn__iexact=screenSn)
            screenDfnRcs = []
            screenFileRcs = []
            screenRecordsetRcs = []
            screenFieldGroupRcs = []
            screenFieldRcs = []
            screenFgLinkRcs = []
            screenFgHeaderFooterRcs = []
            for screenRc in screenRcs:
                b = __is_excel_open(screenRc)
                if b.value:
                    return b

                screenRc.ik_set_status_delete()
                dfnRcs = ScreenDfn.objects.filter(screen=screenRc)
                for i in dfnRcs:
                    i.ik_set_status_delete()
                    screenDfnRcs.append(i)
                fileRcs = ScreenFile.objects.filter(screen=screenRc)
                for j in fileRcs:
                    j.ik_set_status_delete()
                    screenFileRcs.append(j)
                recordsetRcs = ScreenRecordset.objects.filter(screen=screenRc)
                for k in recordsetRcs:
                    k.ik_set_status_delete()
                    screenRecordsetRcs.append(k)
                fieldGroupRcs = ScreenFieldGroup.objects.filter(screen=screenRc)
                for l in fieldGroupRcs:
                    l.ik_set_status_delete()
                    screenFieldGroupRcs.append(l)
                fieldRcs = ScreenField.objects.filter(screen=screenRc)
                for m in fieldRcs:
                    m.ik_set_status_delete()
                    screenFieldRcs.append(m)
                fgLinkRcs = ScreenFgLink.objects.filter(screen=screenRc)
                for n in fgLinkRcs:
                    n.ik_set_status_delete()
                    screenFgLinkRcs.append(n)
                fgHeaderFooterRcs = ScreenFgHeaderFooter.objects.filter(screen=screenRc)
                for o in fgHeaderFooterRcs:
                    o.ik_set_status_delete()
                    screenFgHeaderFooterRcs.append(o)

            ptrn = IkTransaction(self)
            ptrn.add(screenDfnRcs)
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
                ikuidb._deleteExcelAndCSV(screenFileRcs[0])

            ikuiCache.deletePageDefinitionFromCache(screenRc.screen_sn)
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
            screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            b = __is_excel_open(screenRc)
            if b.value:
                return b

            screenFileRcs = []
            screenRecordsetRcs = []
            screenFieldGroupRcs = []
            screenFieldRcs = []
            screenFgLinkRcs = []
            screenFgHeaderFooterRcs = []

            screenRc.ik_set_status_delete()
            fileRcs = ScreenFile.objects.filter(screen=screenRc)
            for i in fileRcs:
                i.ik_set_status_delete()
                screenFileRcs.append(i)
            recordsetRcs = ScreenRecordset.objects.filter(screen=screenRc)
            for j in recordsetRcs:
                j.ik_set_status_delete()
                screenRecordsetRcs.append(j)
            fieldGroupRcs = ScreenFieldGroup.objects.filter(screen=screenRc)
            for k in fieldGroupRcs:
                k.ik_set_status_delete()
                screenFieldGroupRcs.append(k)
            fieldRcs = ScreenField.objects.filter(screen=screenRc)
            for l in fieldRcs:
                l.ik_set_status_delete()
                screenFieldRcs.append(l)
            fgLinkRcs = ScreenFgLink.objects.filter(screen=screenRc)
            for m in fgLinkRcs:
                m.ik_set_status_delete()
                screenFgLinkRcs.append(m)
            fgHeaderFooterRcs = ScreenFgHeaderFooter.objects.filter(screen=screenRc)
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
                ikuidb._deleteExcelAndCSV(screenFileRcs[0])
                newScreenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
                if isNotNullBlank(newScreenRc):
                    c = ikuidb.screenDbWriteToExcel(newScreenRc, "Saved on Screen Definition (Delete last Screen)")
                    if not c.value:
                        return c

            ikuiCache.deletePageDefinitionFromCache(screenRc.screen_sn)
            return Boolean2(True, 'Deleted.')
        return Boolean2(True, 'Nothing deleted.')
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


def copyScreen(self, userID, screenSn, newScreenSn) -> Boolean2:
    try:
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        screenRc.screen_sn = newScreenSn
        b = __is_excel_open(screenRc)
        if b.value:
            return b
        b = __is_model_class_exists(screenRc.app_nm, screenRc.screen_sn, screenRc.class_nm)
        if not b.value:
            return b

        b = ikuidb.screenDbWriteToExcel(screenRc)
        if not b.value:
            return b
        time.sleep(2)

        sp = ikSpreadsheet.SpreadsheetParser(b.data)
        ikuidb._updateDatabaseWithExcelFiles(ikui.ScreenDefinition(name='', fullName='', filePath=b.data, definition=sp.data), userID)
        self.setSessionParameters({"screenSN": screenRc.screen_sn})
        return Boolean2(True, 'Copied.')
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


def resetRev(userID, screenSn, newRev) -> Boolean2:
    lastScreenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
    screenRcs = []
    screenFileRcs = []
    screenRecordsetRcs = []
    screenFieldGroupRcs = []
    screenFieldRcs = []
    screenFgLinkRcs = []
    screenFgHeaderFooterRcs = []
    if lastScreenRc.rev > newRev:
        screenRcs = Screen.objects.filter(screen_sn__iexact=screenSn, rev__gte=newRev)
        for screenRc in screenRcs:
            b = __is_excel_open(screenRc)
            if b.value:
                return b
            if screenRc.id != lastScreenRc.id:
                screenRc.ik_set_status_delete()
                fileRcs = ScreenFile.objects.filter(screen=screenRc)
                for i in fileRcs:
                    i.ik_set_status_delete()
                    screenFileRcs.append(i)
                recordsetRcs = ScreenRecordset.objects.filter(screen=screenRc)
                for j in recordsetRcs:
                    j.ik_set_status_delete()
                    screenRecordsetRcs.append(j)
                fieldGroupRcs = ScreenFieldGroup.objects.filter(screen=screenRc)
                for k in fieldGroupRcs:
                    k.ik_set_status_delete()
                    screenFieldGroupRcs.append(k)
                fieldRcs = ScreenField.objects.filter(screen=screenRc)
                for l in fieldRcs:
                    l.ik_set_status_delete()
                    screenFieldRcs.append(l)
                fgLinkRcs = ScreenFgLink.objects.filter(screen=screenRc)
                for m in fgLinkRcs:
                    m.ik_set_status_delete()
                    screenFgLinkRcs.append(m)
                fgHeaderFooterRcs = ScreenFgHeaderFooter.objects.filter(screen=screenRc)
                for n in fgHeaderFooterRcs:
                    n.ik_set_status_delete()
                    screenFgHeaderFooterRcs.append(n)
    elif lastScreenRc.rev == newRev:
        return Boolean2(False, 'New revision is the same as previous revision')

    lastScreenRc.rev = newRev
    lastScreenRc.ik_set_status_modified()

    ptrn = IkTransaction(userID=userID)
    ptrn.add(screenFileRcs)
    ptrn.add(screenFgHeaderFooterRcs)
    ptrn.add(screenFgLinkRcs)
    ptrn.add(screenFieldRcs)
    ptrn.add(screenFieldGroupRcs)
    ptrn.add(screenRecordsetRcs)
    ptrn.add(screenRcs)
    ptrn.add(lastScreenRc)
    b = ptrn.save()
    if not b.value:
        return b
    if len(screenFileRcs) > 0:
        ikuidb._deleteExcelAndCSV(screenFileRcs[0])
        newScreenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        if isNotNullBlank(newScreenRc):
            c = ikuidb.screenDbWriteToExcel(newScreenRc, "Saved on Screen Definition (Reset Revision)")
            if not c.value:
                return c
    return Boolean2(True, 'Revision successfully reset to [%s]' % newRev)


# Recordset
# save Recordset Table
def saveScreenRecordsets(self, screenSn, currentBtnClick) -> Boolean2:
    try:
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
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
            recordsetSeq = 1
            for rc in recordsetLists:
                if strUtils.isEmpty(rc.seq):
                    rc.seq = recordsetSeq
                else:
                    rc.seq = float(rc.seq) - 0.5
                recordsetSeq += 1
                if rc.ik_is_status_delete():
                    # if delete check has related recordset
                    relateFgRc = ScreenFieldGroup.objects.filter(screen=screenRc, recordset__id=rc.id).first()
                    if relateFgRc:
                        return Boolean2(False, rc.recordset_nm + " was used by field group: " + relateFgRc.fg_nm + ", please remove it first.")
                    # hasUpdate = True
                    rc.ik_set_status_delete()
                else:
                    recordsetNm = strUtils.stripStr(rc.recordset_nm)
                    if strUtils.isEmpty(recordsetNm):
                        return Boolean2(False, "Recordset Name is mandatory, please check.")
                    if strUtils.isEmpty(rc.sql_fields):
                        rc.sql_fields = "*"
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


# Field Group
# save field group
def saveFieldGroup(self, screenSn, isNew, currentBtnClick) -> Boolean2:
    try:
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
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

        # 1. validate field group
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
            validateFgNmRcs = ScreenFieldGroup.objects.filter(screen=screenRc)
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

            # 2.validate fields
            fieldListFg: list[ScreenField] = self.getRequestData().get("fieldListFg", None)
            # uniqueCheckList = []
            if fieldListFg:
                fieldSeq = 1
                fieldNmList = []
                for rc in fieldListFg:
                    if not rc.ik_is_status_delete():
                        # auto set field name & field seq
                        rc.seq = strUtils.stripStr(rc.seq)
                        rc.field_nm = strUtils.stripStr(rc.field_nm)
                        if isNotNullBlank(rc.field_nm):
                            if rc.field_nm in fieldNmList:
                                return Boolean2(False, "Field name in the same field group must be unique.")
                            fieldNmList.append(rc.field_nm)
                        # check field name unique
                        # if rc.field_nm in uniqueCheckList:
                        #     return Boolean2(False, "Field Name is unique. Please check: " + rc.field_nm)
                        # uniqueCheckList.append(rc.field_nm)

                        if strUtils.isEmpty(rc.seq):
                            rc.seq = fieldSeq
                        else:
                            rc.seq = float(rc.seq) - 0.5
                        fieldSeq += 1
                        if not rc.ik_is_status_retrieve() and isNotNullBlank(rc.widget):
                            # rc.visible = not rc.visible  # page is hidden
                            # rc.editable = not rc.editable  # page is not editable
                            if rc.widget.widget_nm in PARAMETERS_NOT_REQUIRED_FOR_WIDGET:
                                nonExistentParams = PARAMETERS_NOT_REQUIRED_FOR_WIDGET[rc.widget.widget_nm]
                                for i in nonExistentParams:
                                    widgetParameters = ikui.IkUI.parseWidgetPrams(rc.widget_parameters)
                                    if isNotNullBlank(rc.widget_parameters) and i in widgetParameters.keys():
                                        return Boolean2(False, "Widget [%s] does not require parameter [%s]." % (rc.widget.widget_nm, i))
                            elif rc.widget.widget_nm in NO_PARAMETERS_WIDGET:
                                if isNotNullBlank(rc.widget_parameters):
                                    return Boolean2(False, "Widget [%s] does not require parameters." % rc.widget.widget_nm)
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
        fieldGroupRc = ScreenFieldGroup.objects.filter(id=fieldGroupId).first()
        if fieldGroupRc is None:
            return Boolean2(False, "The ID(" + str(fieldGroupId) + ") of Field Group does not exist, please check.")
        fieldRcs = ScreenField.objects.filter(screen=fieldGroupRc.screen, field_group=fieldGroupRc)
        return __createNewRevScreen(self, screenSn, fieldGroupRc.screen, fieldGroupRc=fieldGroupRc, fieldRcs=fieldRcs)
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


def saveSubScreen(self, screenSn, currentBtnClick):
    try:
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
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
        # _3. validate field group
        validateFieldGroupFg = saveFieldGroup(self, screenSn, False, False)
        if not validateFieldGroupFg.value:
            return validateFieldGroupFg

        # validate sub screen
        screenDfnFg: list[ScreenDfn] = self.getRequestData().get('subScreenFg', None)
        if screenDfnFg is None and currentBtnClick:
            logger.error("Save sub screen definition failed, get screenDfnFg error.")
            return Boolean2(False, "System error, please ask administrator to check.")

        for i in screenDfnFg:
            i.screen_id = screenRc.id
            fgs = i.field_group_nms
            fgNmList = []
            if isNullBlank(fgs):
                fgNmList = ScreenFieldGroup.objects.filter(screen=screenRc).values_list('fg_nm', flat=True)
            else:
                fgList = [fg.strip() for fg in fgs.split(',')]
                for j in fgList:
                    fgRc = ScreenFieldGroup.objects.filter(screen=screenRc, fg_nm=j).first()
                    if not strUtils.isEmpty(fgRc):
                        fgNmList.append(fgRc.fg_nm)
            i.field_group_nms = ", ".join(fgNmList)

        if currentBtnClick:
            return __createNewRevScreen(self,
                                        screenSn,
                                        screenRc=self.getRequestData().get("screenDtlFg", None),
                                        recordsetRcs=self.getRequestData().get("recordsetListFg", None),
                                        fieldGroupRc=self.getRequestData().get("fieldGroupDtlFg", None),
                                        fieldRcs=self.getRequestData().get("fieldListFg", None),
                                        subScreenRcs=screenDfnFg)

        return Boolean2(True, 'Nothing changed.')
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


# Field Group Link
# save field group link
def saveFgLink(self, screenSn, isNew, currentBtnClick) -> Boolean2:
    try:
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
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
            # _4. validate subScreenFg
            validateSubScreenFg = saveSubScreen(self, screenSn, False)
            if not validateSubScreenFg.value:
                return validateSubScreenFg

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
            # XH 2023-04-25 START

            validateRc = ScreenFgLink.objects.filter(screen__id=screenRc.id, field_group__id=fgId, parent_field_group__id=pFgId)
            if len(validateRc) > 0 and not isNew and fgLinkId:  # if modified, except himself
                validateRc = validateRc.exclude(id=fgLinkId)
            validateRc = validateRc.first() if len(validateRc) > 0 else None
            if validateRc is not None and validateRc.parent_key == parentKey and validateRc.local_key == localKey:
                return Boolean2(False, "This relationship has exists, please check.")
            # XH 2023-04-25 END

            # check real modified
            # TODO

        if currentBtnClick:
            return __createNewRevScreen(self,
                                        screenSn,
                                        screenRc=self.getRequestData().get("screenDtlFg", None),
                                        recordsetRcs=self.getRequestData().get("recordsetListFg", None),
                                        fieldGroupRc=self.getRequestData().get("fieldGroupDtlFg", None),
                                        fieldRcs=self.getRequestData().get("fieldListFg", None),
                                        subScreenRcs=self.getRequestData().get("subScreenFg", None),
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
        fgLinkRc = ScreenFgLink.objects.filter(id=fgLinkId).first()
        if fgLinkRc is None:
            return Boolean2(False, "The ID(" + str(fgLinkId) + ") of Field Group Link does not exist, please check.")

        fgLinkRc.ik_set_status_delete()
        return __createNewRevScreen(self, screenSn, fgLinkRc.screen, fgLinkRc=fgLinkRc)
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


# Header And Footer
# save table header and footer
def saveFgHeaderFooter(self, screenSn, isNew, currentBtnClick) -> Boolean2:
    try:
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
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
        # _4. validate subScreenFg
        validateSubScreenFg = saveSubScreen(self, screenSn, False)
        if not validateSubScreenFg.value:
            return validateSubScreenFg
        # _5. validate field group link
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
        # XH 2023-04-25 START
        # if strUtils.isEmpty(headerLevel1):
        #     return Boolean2(False, "Header level 1 is mandatory, please check.")
        headerLevel2 = strUtils.stripStr(fgHeaderFooterDtlFg.header_level2)
        # if strUtils.isEmpty(headerLevel2):
        #     return Boolean2(False, "Header level 2 is mandatory, please check.")
        headerLevel3 = strUtils.stripStr(fgHeaderFooterDtlFg.header_level3)
        # if strUtils.isEmpty(headerLevel3):
        #     return Boolean2(False, "Header level 3 is mandatory, please check.")
        footer = strUtils.stripStr(fgHeaderFooterDtlFg.footer)

        validateRc = ScreenFgHeaderFooter.objects.filter(screen__id=screenRc.id, field_group__id=fgId, field__id=fId)
        if len(validateRc) > 0 and not isNew and fgHeaderFooterId:  # if modified, except himself
            validateRc = validateRc.exclude(id=fgHeaderFooterId)
        validateRc = validateRc.first() if len(validateRc) > 0 else None
        if validateRc is not None and validateRc.header_level1 == headerLevel1 and validateRc.header_level2 == headerLevel2 and validateRc.header_level3 == headerLevel3\
                and validateRc.footer == footer:
            return Boolean2(False, "This record has exists, please check.")
        # XH 2023-04-25 END

        # check real modified
        # TODO

        if currentBtnClick:
            return __createNewRevScreen(self,
                                        screenSn,
                                        screenRc=self.getRequestData().get("screenDtlFg", None),
                                        recordsetRcs=self.getRequestData().get("recordsetListFg", None),
                                        fieldGroupRc=self.getRequestData().get("fieldGroupDtlFg", None),
                                        fieldRcs=self.getRequestData().get("fieldListFg", None),
                                        subScreenRcs=self.getRequestData().get("subScreenFg", None),
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
        fgHeaderFooterRc = ScreenFgHeaderFooter.objects.filter(id=fgHeaderFooterId).first()
        if fgHeaderFooterRc is None:
            return Boolean2(False, "The ID(" + str(fgHeaderFooterId) + ") of Header And Footer table does not exist, please check.")

        fgHeaderFooterRc.ik_set_status_delete()
        return __createNewRevScreen(self, screenSn, fgHeaderFooterRc.screen, fgHeaderFooterRc=fgHeaderFooterRc)
    except IkException as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, str(e))
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'System error, please ask administrator to check.')


# whole screen
def __createNewRevScreen(self,
                         screenSn,
                         screenRc: Screen,
                         recordsetRcs: list[ScreenRecordset] = None,
                         fieldGroupRc: ScreenFieldGroup = None,
                         fieldRcs: list[ScreenField] = None,
                         subScreenRcs: list[ScreenDfn] = None,
                         fgLinkRc: ScreenFgLink = None,
                         fgHeaderFooterRc: ScreenFgHeaderFooter = None) -> Boolean2:
    try:
        modifyFlag = False
        isDeleteFieldGroup = True if self.getSessionParameterBool("isDeleteFieldGroup") else False  # delete current field group
        isDeleteFgLink = True if self.getSessionParameterBool("isDeleteFgLink") else False  # delete current field group link
        isDeleteFgHeaderFooter = True if self.getSessionParameterBool("isDeleteFgHeaderFooter") else False  # delete current header and footer table
        if isDeleteFieldGroup or isDeleteFgLink or isDeleteFgHeaderFooter:
            modifyFlag = True
        else:
            if isNotNullBlank(screenRc) and not screenRc.ik_is_status_retrieve():
                modifyFlag = True
            if isNotNullBlank(recordsetRcs) and not modifyFlag:
                for i in recordsetRcs:
                    if not i.ik_is_status_retrieve():
                        modifyFlag = True
                        break
            if isNotNullBlank(fieldGroupRc) and not fieldGroupRc.ik_is_status_retrieve():
                modifyFlag = True
            if isNotNullBlank(fieldRcs) and not modifyFlag:
                for j in fieldRcs:
                    if not j.ik_is_status_retrieve():
                        modifyFlag = True
                        break
            if isNotNullBlank(subScreenRcs) and not modifyFlag:
                for k in subScreenRcs:
                    if not k.ik_is_status_retrieve():
                        modifyFlag = True
                        break
            if isNotNullBlank(fgLinkRc) and not fgLinkRc.ik_is_status_retrieve():
                modifyFlag = True
            if isNotNullBlank(fgHeaderFooterRc) and not fgHeaderFooterRc.ik_is_status_retrieve():
                modifyFlag = True

        if not modifyFlag:
            return Boolean2(True, 'No changes detected. Nothing to save.')

        # get the last rev screen
        lastRevScreenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()

        # ===== 1. new Screen
        if screenRc:
            b = __is_excel_open(screenRc)
            if b.value:
                return b
            b = __is_model_class_exists(screenRc.app_nm, screenRc.screen_sn, screenRc.class_nm)
            if not b.value:
                return b
            if lastRevScreenRc:
                if screenRc.app_nm != lastRevScreenRc.app_nm:
                    lastScreenFileRc = ScreenFile.objects.filter(screen=lastRevScreenRc).order_by('-file_dt').first()
                    if isNotNullBlank(lastScreenFileRc):
                        ikuidb._deleteExcelAndCSV(lastScreenFileRc)
                screenRc.rev = lastRevScreenRc.rev + 1
            else:
                screenRc.rev = 0  # the first rev screen
            screenRc.ik_set_status_new()
            screenRc.id = Screen().assignPrimaryID()

        isNewScreen = True if self.getSessionParameterBool("isNewScreen") else False
        recordsetDBRcs = []
        fieldGroupDBRcs = []
        fgFieldDBRcs = []
        subScreenDBRcs = []
        fgLinkDBRcs = []
        fgHeaderFooterDBRcs = []
        screenFileRc = []
        if not isNewScreen:  # just new screen
            # ===== 2. new Recordset records
            # if not data, get the last rev screen's records
            if (recordsetRcs is None or len(recordsetRcs) <= 0) and lastRevScreenRc:
                recordsetRcs = list(ScreenRecordset.objects.filter(screen=lastRevScreenRc).order_by("id"))
            recordsetNewIdMap = {}  # **import: for create new field group
            rSeq = 1
            recordsetRcs.sort(key=lambda obj: (obj.seq, obj.recordset_nm))
            for rc in recordsetRcs:
                if not rc.ik_is_status_delete():
                    # _import if modified recordset_nm need update field group recordset id
                    orgRecordsetNm = None
                    if rc.ik_is_status_modified():
                        orgRecordsetNm = ScreenRecordset.objects.filter(id=rc.id).first().recordset_nm
                        if rc.recordset_nm != orgRecordsetNm:
                            recordsetNewIdMap.update({orgRecordsetNm: rc.id})
                    rc.ik_set_status_new()
                    rc.seq = rSeq
                    rc.screen = screenRc
                    rc.id = ScreenRecordset().assignPrimaryID()
                    recordsetNewIdMap.update({rc.recordset_nm: rc.id})
                    if not strUtils.isEmpty(orgRecordsetNm):
                        recordsetNewIdMap.update({orgRecordsetNm: rc.id})
                    recordsetDBRcs.append(rc)
                    rSeq += 1

            # ===== 3. new Field Group,  4. new Field records
            fieldGroupNewIdMap = {}
            fgFieldNewIdMap = {}

            # copy the last rev screen's field group
            lastRevFieldGroupRcs = ScreenFieldGroup.objects.filter(screen=lastRevScreenRc).order_by("seq")
            currentFgId = self.getSessionParameterInt("currentFgID")
            newCurrentFgId = None
            curSeq = 100
            for fgRc in lastRevFieldGroupRcs:
                if fgRc.id == currentFgId and isDeleteFieldGroup:  # delete.
                    continue
                if not strUtils.isEmpty(currentFgId) and fieldGroupRc and fgRc.id == currentFgId and not isDeleteFieldGroup:  # modify current field group info
                    # _import if modified field group name need update fg link and header footer table id
                    orgFgNm = ScreenFieldGroup.objects.filter(id=fgRc.id).first().fg_nm
                    fieldGroupRc.ik_set_status_new()
                    fieldGroupRc.id = ScreenFieldGroup().assignPrimaryID()
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
                                # _import if modified field name need update header and footer field id
                                fieldNm = fRc.field_nm if isNotNullBlank(fRc.field_nm) else str(fRc.seq)
                                orgFieldNm = None
                                if fRc.ik_is_status_modified():
                                    orgField = ScreenField.objects.filter(id=fRc.id).first()
                                    orgFieldNm = orgField.field_nm if isNotNullBlank(orgField.field_nm) else str(orgField.seq)
                                    if fieldNm != orgFieldNm:
                                        fgFieldNewIdMap.update({fRc.field_group.fg_nm + "-" + orgFieldNm: fRc.id})
                                # if fRc.ik_is_status_modified():
                                #     fRc.visible = not fRc.visible if fRc.visible else True  # in page is use hidden
                                fRc.ik_set_status_new()
                                fRc.field_group = fieldGroupRc
                                fRc.id = ScreenField().assignPrimaryID()
                                fRc.seq = seq1
                                # _import: use new screenRc and field group
                                fRc.screen = screenRc
                                fRc.field_group_id = fieldGroupNewIdMap.get(fRc.field_group.fg_nm)
                                fgFieldNewIdMap.update({fRc.field_group.fg_nm + "-" + fieldNm: fRc.id})
                                if not strUtils.isEmpty(orgFieldNm):
                                    fgFieldNewIdMap.update({fRc.field_group.fg_nm + "-" + orgFieldNm: fRc.id})
                                fgFieldDBRcs.append(fRc)
                                seq1 += 1
                    fieldGroupDBRcs.append(fieldGroupRc)
                else:  # copy the last rev screen's field group
                    # get last rev fields
                    lastRevFieldRcs = ScreenField.objects.filter(screen=lastRevScreenRc, field_group=fgRc).order_by("seq")
                    fgRc.ik_set_status_new()
                    fgRc.screen = screenRc
                    fgRc.id = ScreenFieldGroup().assignPrimaryID()
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
                        fRc.id = ScreenField().assignPrimaryID()
                        fRc.seq = fSeq
                        # _import: use new screenRc and field group
                        fRc.screen = screenRc
                        fRc.field_group_id = fieldGroupNewIdMap.get(fRc.field_group.fg_nm)
                        fieldNm = fRc.field_nm if isNotNullBlank(fRc.field_nm) else str(fRc.seq)
                        fgFieldNewIdMap.update({fRc.field_group.fg_nm + "-" + fieldNm: fRc.id})
                        fgFieldDBRcs.append(fRc)
                        fSeq += 1
                    fieldGroupDBRcs.append(fgRc)

            # create new field group
            if fieldGroupRc and strUtils.isEmpty(currentFgId) and not isDeleteFieldGroup:
                fieldGroupRc.ik_set_status_new()
                fieldGroupRc.id = ScreenFieldGroup().assignPrimaryID()
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
                            fRc.id = ScreenField().assignPrimaryID()
                            # fRc.visible = not fRc.visible if fRc.visible else True  # in page is use hidden
                            fRc.seq = fSeq
                            # _import: use new screenRc and field group
                            fRc.screen = screenRc
                            fRc.field_group_id = fieldGroupNewIdMap.get(fRc.field_group.fg_nm)
                            fieldNm = fRc.field_nm if isNotNullBlank(fRc.field_nm) else str(fRc.seq)
                            fgFieldNewIdMap.update({fRc.field_group.fg_nm + "-" + fieldNm: fRc.id})
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

            # ===== 5. new Sub Screen
            # if not data, get the last rev screen's records
            if (subScreenRcs is None or len(subScreenRcs) <= 0) and lastRevScreenRc:
                subScreenRcs = ScreenDfn.objects.filter(screen=lastRevScreenRc).order_by("id")
            for rc in subScreenRcs:
                if not rc.ik_is_status_delete():
                    # _import if modified recordset_nm need update field group recordset id
                    rc.ik_set_status_new()
                    rc.screen = screenRc
                    rc.id = ScreenDfn().assignPrimaryID()
                    subScreenDBRcs.append(rc)

            # ===== 6. new Field Table Link
            # copy the last rev screen's field group link
            lastRevFgLinkRcs = ScreenFgLink.objects.filter(screen=lastRevScreenRc).order_by("id")
            currentFgLinkId = self.getSessionParameterInt("currentFgLinkID")
            newCurrentFgLinkId = None
            for rc in lastRevFgLinkRcs:
                if rc.id == currentFgLinkId and isDeleteFgLink or rc.field_group_id == currentFgId and isDeleteFieldGroup:
                    continue
                if not strUtils.isEmpty(currentFgLinkId) and fgLinkRc and rc.id == currentFgLinkId and not isDeleteFgLink:  # modify current field group link info
                    fgLinkRc.ik_set_status_new()
                    fgLinkRc.id = ScreenFgLink().assignPrimaryID()
                    newCurrentFgLinkId = fgLinkRc.id  # for get new current field group link id
                    # _import: use new screenRc and field group
                    fgLinkRc.screen = screenRc
                    fgLinkRc.field_group_id = fieldGroupNewIdMap.get(fgLinkRc.field_group.fg_nm)
                    fgLinkRc.parent_field_group_id = fieldGroupNewIdMap.get(fgLinkRc.parent_field_group.fg_nm)
                    fgLinkDBRcs.append(fgLinkRc)
                else:  # copy the last rev screen's field group
                    rc.ik_set_status_new()
                    rc.id = ScreenFgLink().assignPrimaryID()
                    # _import: use new screenRc and field group
                    rc.screen = screenRc
                    rc.field_group_id = fieldGroupNewIdMap.get(rc.field_group.fg_nm)
                    rc.parent_field_group_id = fieldGroupNewIdMap.get(rc.parent_field_group.fg_nm)
                    fgLinkDBRcs.append(rc)

            # XH 2023-04-25 START
            # create new field group
            if fgLinkRc and strUtils.isEmpty(currentFgLinkId) and not isDeleteFgLink:
                fgLinkRc.ik_set_status_new()
                fgLinkRc.id = ScreenFgLink().assignPrimaryID()
                newCurrentFgLinkId = fgLinkRc.id  # for get new current field group link id
                # _import: use new screenRc and field group
                fgLinkRc.screen = screenRc
                fgLinkRc.field_group_id = fieldGroupNewIdMap.get(fgLinkRc.field_group.fg_nm)
                fgLinkRc.parent_field_group_id = fieldGroupNewIdMap.get(fgLinkRc.parent_field_group.fg_nm)
                fgLinkDBRcs.append(fgLinkRc)
            # XH 2023-04-25 END
            self.setSessionParameters({"currentFgLinkID": newCurrentFgLinkId})  # for get new current field group link id

            # ===== 7. new Header And Footer Table
            # copy the last rev screen's header footer table
            lastRevFgHeaderFooterRcs = ScreenFgHeaderFooter.objects.filter(screen=lastRevScreenRc).order_by("id")
            currentFgHeaderFooterId = self.getSessionParameterInt("currentFgHeaderFooterID")
            newCurrentFgHeaderFooterId = None
            for rc in lastRevFgHeaderFooterRcs:
                # delete  Delete the rows related to header footer table when deleting field group.
                if rc.id == currentFgHeaderFooterId and isDeleteFgHeaderFooter or rc.field_group_id == currentFgId and isDeleteFieldGroup:
                    continue
                if not strUtils.isEmpty(currentFgHeaderFooterId
                                        ) and fgHeaderFooterRc and rc.id == currentFgHeaderFooterId and not isDeleteFgHeaderFooter:  # modify current header footer table info
                    fgHeaderFooterRc.ik_set_status_new()
                    fgHeaderFooterRc.id = ScreenFgHeaderFooter().assignPrimaryID()
                    newCurrentFgHeaderFooterId = fgHeaderFooterRc.id  # for get new current header and footer table id
                    # _import: use new screenRc and field group and field
                    fgHeaderFooterRc.screen = screenRc
                    fieldNm = fgHeaderFooterRc.field.field_nm if isNotNullBlank(fgHeaderFooterRc.field.field_nm) else str(fgHeaderFooterRc.field.seq)
                    fgHeaderFooterRc.field_id = fgFieldNewIdMap.get(fgHeaderFooterRc.field_group.fg_nm + "-" + fieldNm)
                    fgHeaderFooterRc.field_group_id = fieldGroupNewIdMap.get(fgHeaderFooterRc.field_group.fg_nm)
                    fgHeaderFooterDBRcs.append(fgHeaderFooterRc)
                else:  # copy the last rev screen's header footer table
                    rc.ik_set_status_new()
                    rc.id = ScreenFgHeaderFooter().assignPrimaryID()
                    # _import: use new screenRc and field group and field
                    rc.screen = screenRc
                    fieldNm = rc.field.field_nm if isNotNullBlank(rc.field.field_nm) else str(rc.field.seq)
                    rc.field_id = fgFieldNewIdMap.get(rc.field_group.fg_nm + "-" + fieldNm)
                    rc.field_group_id = fieldGroupNewIdMap.get(rc.field_group.fg_nm)
                    fgHeaderFooterDBRcs.append(rc)

            # XH 2023-04-25 START
            if fgHeaderFooterRc and strUtils.isEmpty(currentFgHeaderFooterId) and not isDeleteFgHeaderFooter:
                fgHeaderFooterRc.ik_set_status_new()
                fgHeaderFooterRc.id = ScreenFgHeaderFooter().assignPrimaryID()
                newCurrentFgHeaderFooterId = fgHeaderFooterRc.id  # for get new current header and footer table id
                # _import: use new screenRc and field group and field
                fgHeaderFooterRc.screen = screenRc
                fieldNm = fgHeaderFooterRc.field.field_nm if isNotNullBlank(fgHeaderFooterRc.field.field_nm) else str(fgHeaderFooterRc.field.seq)
                fgHeaderFooterRc.field_id = fgFieldNewIdMap.get(fgHeaderFooterRc.field_group.fg_nm + "-" + fieldNm)
                fgHeaderFooterRc.field_group_id = fieldGroupNewIdMap.get(fgHeaderFooterRc.field_group.fg_nm)
                fgHeaderFooterDBRcs.append(fgHeaderFooterRc)
            # XH 2023-04-25 END
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
            # XH 2023-05-08 START
            lastRevScreenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            c = __is_model_class_exists(lastRevScreenRc.app_nm, lastRevScreenRc.screen_sn, lastRevScreenRc.class_nm)
            if not c.value:
                return c
            d = ikuidb.screenDbWriteToExcel(lastRevScreenRc, "Saved on Screen Definition")
            if not d.value:
                logger.error("Screen [%s] excel file generation failed. Please check the database or the template file used for generating the Excel." % screenSn)
                return d
            else:
                # Saving new page definitions in the cache
                screenDefinition = ikui.IkUI._getScreenDefinitionFromDB(screenRc.screen_sn)
                ikuiCache.setPageDefinitionCache(screenRc.screen_sn, screenDefinition)
            # XH 2023-05-08 End

            if isNewScreen:
                self.setSessionParameters({"screenSN": screenSn})

                from core.urls import apiScreenUrl, urlpatterns
                viewClass = modelUtils.get_model_class_2(screenRc.app_nm, screenRc.screen_sn, screenRc.class_nm)
                url = apiScreenUrl(viewClass, None if isNullBlank(screenRc.api_url) else screenRc.api_url.lower())
                urlpatterns.append(url)
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


# XH 2023-04-24 START
def getFieldDBKeys(screenRc, field_group):
    data = []
    try:
        if field_group:
            recordset = ScreenFieldGroup.objects.filter(screen=screenRc, fg_nm=field_group.fg_nm).first().recordset
            sql_models = ScreenRecordset.objects.filter(screen=screenRc, recordset_nm=recordset.recordset_nm).first().sql_models
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


# XH 2023-04-24 END


def __is_model_class_exists(app_mm, screen_sn, class_nm):
    if not modelUtils.is_model_class_exists(app_mm, screen_sn, class_nm):
        module_name_1 = "%s.views.%s" % (app_mm, screen_sn)
        module_name_2 = "%s.views.%s.%s" % (app_mm, screen_sn.lower(), screen_sn)
        error = "Failed to import module for [%s]. Please check the following paths: [%s] or [%s]" % (screen_sn, module_name_1, module_name_2)
        if isNotNullBlank(class_nm):
            error += "  or [%s]." % class_nm
        else:
            error += "."
        return Boolean2(False, error)
    return Boolean2(True)


def __is_excel_open(screenRc: Screen) -> Boolean2:
    filename = '%s.xlsx' % screenRc.screen_sn
    file_path = Path(os.path.join(screenRc.app_nm, ikui.SCREEN_RESOURCE_FOLDER_PATH, filename))

    if not os.path.exists(file_path):
        return Boolean2(False)
    try:
        with open(file_path, 'r+'):
            return Boolean2(False)
    except IOError:
        return Boolean2(True, "File [%s] is already open. Please close it and try again." % filename)
