'''
Description: PYI Screen Definition
version:
Author: YL
Date: 2023-04-18 15:36:52
'''

from django.db.models import Q, OuterRef, Subquery, Prefetch
from django.forms import model_to_dict

import core.core.fs as ikfs
import core.ui.ui as ikui
import core.ui.uidb as ikuidb
import core.utils.strUtils as strUtils
from core.core.http import *
from core.core.lang import Boolean2
from core.log.logger import logger
from core.models import *
from core.utils.langUtils import isNotNullBlank, isNullBlank
from core.screen import ScreenDfnManager
from core.view.screenView import ScreenAPIView

class ScreenDfnView(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen: ikui.Screen):
            if screen.subScreenName == 'deleteScreenDialog':
                return
            if screen.subScreenName == 'resetRevDialog':
                return
            if screen.subScreenName == 'copyPramsDialog':
                return
            if screen.subScreenName == 'widgetPramsDialog':
                widgetNm = self.getSessionParameter('widgetNm')
                screen.setFieldsVisible(fieldGroupName='dialogWidgetPramsFg',
                                        fieldNames=[
                                            'placeholderField', 'formatField1', 'formatField2', 'stateNumField', 'captionPositionField', 'multipleField', 'dataField', 
                                            'recordsetField', 'dataUrlField', 'valueField', 'displayField', 'onChangeField', 'iconField', 'typeField'
                                        ],
                                        visible=False)
                screen.setFieldGroupsVisible(fieldGroupNames='dialogWidgetDialogPramsFg', visible=False)
                if widgetNm in ScreenDfnManager.NO_PARAMETERS_WIDGET:
                    screen.setFieldGroupsVisible(fieldGroupNames=['dialogWidgetPramsFg'], visible=False)
                elif widgetNm == ikui.SCREEN_FIELD_WIDGET_LABEL:
                    screen.setFieldsVisible(fieldGroupName='dialogWidgetPramsFg',
                                            fieldNames=['formatField1', 'dataField', 'recordsetField', 'dataUrlField', 'valueField', 'displayField'],
                                            visible=True)
                elif widgetNm == ikui.SCREEN_FIELD_WIDGET_TEXT_BOX:
                    screen.setFieldsVisible(fieldGroupName='dialogWidgetPramsFg', fieldNames=['placeholderField', 'formatField1'], visible=True)
                elif widgetNm == ikui.SCREEN_FIELD_WIDGET_TEXT_AREA:
                    screen.setFieldsVisible(fieldGroupName='dialogWidgetPramsFg', fieldNames=['placeholderField'], visible=True)
                elif widgetNm == ikui.SCREEN_FIELD_WIDGET_DATE_BOX:
                    screen.setFieldsVisible(fieldGroupName='dialogWidgetPramsFg', fieldNames=['formatField2'], visible=True)
                elif widgetNm == ikui.SCREEN_FIELD_WIDGET_COMBO_BOX or widgetNm == ikui.SCREEN_FIELD_WIDGET_LIST_BOX or widgetNm == ikui.SCREEN_FIELD_WIDGET_ADVANCED_COMBOBOX:
                    screen.setFieldsVisible(fieldGroupName='dialogWidgetPramsFg',
                                            fieldNames=['dataField', 'recordsetField', 'dataUrlField', 'valueField', 'displayField', 'onChangeField'],
                                            visible=True)
                elif widgetNm == ikui.SCREEN_FIELD_WIDGET_ADVANCED_SELECTION:
                    screen.setFieldsVisible(fieldGroupName='dialogWidgetPramsFg',
                                            fieldNames=['iconField', 'recordsetField', 'dataField', 'dataUrlField', 'valueField', 'displayField'],
                                            visible=True)
                    screen.setFieldGroupsVisible(fieldGroupNames='dialogWidgetDialogPramsFg', visible=True)
                elif widgetNm == ikui.SCREEN_FIELD_WIDGET_CHECK_BOX:
                    screen.setFieldsVisible(fieldGroupName='dialogWidgetPramsFg', fieldNames=['stateNumField', 'captionPositionField'], visible=True)
                elif widgetNm == ikui.SCREEN_FIELD_WIDGET_BUTTON or widgetNm == ikui.SCREEN_FIELD_WIDGET_ICON_AND_TEXT:
                    screen.setFieldsVisible(fieldGroupName='dialogWidgetPramsFg', fieldNames=['iconField', 'typeField', 'multipleField'], visible=True)
                    screen.setFieldGroupsVisible(fieldGroupNames='dialogWidgetDialogPramsFg', visible=True)
                    dialogWidgetPramsRc = self.getSessionParameter('dialogWidgetPramsRc')
                    if isNullBlank(dialogWidgetPramsRc) or dialogWidgetPramsRc.get('type', '') != 'uploadDialog':
                        screen.setFieldsVisible(fieldGroupName='dialogWidgetPramsFg', fieldNames=['multipleField'], visible=False)
                        screen.setFieldsVisible(fieldGroupName='dialogWidgetDialogPramsFg', fieldNames=['dialogUploadTipField'], visible=False)
                elif widgetNm == ikui.SCREEN_FIELD_WIDGET_FILE:
                    screen.setFieldsVisible(fieldGroupName='dialogWidgetPramsFg', fieldNames=['multipleField'], visible=True)
                return
            if screen.subScreenName == 'additionalPropsDialog':
                return

            isNewScreen = True if self.getSessionParameterBool("isNewScreen") else False
            selectedScreenSn = self.getSessionParameter("screenSN")
            isNewFg = True if self.getSessionParameterBool("isNewFg") else False
            currentFgId = self.getSessionParameterInt("currentFgID")
            isNewFgLink = True if self.getSessionParameterBool("isNewFgLink") else False
            currentFgLinkId = self.getSessionParameterInt("currentFgLinkID")
            isNewFgHeaderFooter = True if self.getSessionParameterBool("isNewFgHeaderFooter") else False
            currentFgHeaderFooterId = self.getSessionParameterInt("currentFgHeaderFooterID")

            isSelectedScreenSn = True if not strUtils.isEmpty(selectedScreenSn) else False
            screen.setFieldsRequired(fieldGroupName='screenDtlFg', fieldNames='screenLayoutTypeField', required=True)
            # screen page
            screen.setFieldGroupsVisible(fieldGroupNames=['screenDtlFg', 'screenToolbar2'], visible=isSelectedScreenSn or isNewScreen)
            # screen.setFieldsVisible(fieldGroupName='screenToolbar', fieldNames=['bttSaveScreen'], visible=isSelectedScreenSn or isNewScreen)
            screen.setFieldGroupsVisible(
                fieldGroupNames=['recordsetListFg', 'recordsetToolbar', 'fieldGroupListFg', 'fgLinkListFg', 'fgHeaderFooterListFg', 'subScreenFg', 'subScreenToolbar'],
                visible=isSelectedScreenSn)

            # XH 2023-05-04 START
            # import and export
            # screen.setFieldGroupsVisible(fieldGroupNames=['importFg'], visible= not isSelectedScreenSn)
            screen.setFieldsVisible(fieldGroupName='screenToolbar2',
                                    fieldNames=['bttExportScreen', 'bttDeleteScreen', 'bttDeleteLastRev', 'bttCopyScreen', 'bttResetRev', 'bttRefresh'],
                                    visible=isSelectedScreenSn)
            # screen.setFieldsVisible(fieldGroupName='screenToolbar', fieldNames=['bttImportScreen'], visible=not isSelectedScreenSn)
            # XH 2023-05-04 END

            # field group page
            screen.setFieldGroupsVisible(fieldGroupNames=['fieldGroupDtlFg', 'fieldListFg'], visible=isSelectedScreenSn and (currentFgId is not None or isNewFg))
            screen.setFieldsVisible(fieldGroupName='fgToolbar', fieldNames='bttNewFg', visible=isSelectedScreenSn)
            screen.setFieldsVisible(fieldGroupName='fgToolbar',
                                    fieldNames=['bttHideFgDtl', 'bttSaveFg', 'bttDeleteFg'],
                                    visible=isSelectedScreenSn and (currentFgId is not None or isNewFg))

            # field group link page
            screen.setFieldGroupsVisible(fieldGroupNames=['fgLinkDtlFg'], visible=isSelectedScreenSn and (currentFgLinkId is not None or isNewFgLink))
            screen.setFieldsVisible(fieldGroupName='fgLinkToolbar', fieldNames='bttNewFgLink', visible=isSelectedScreenSn)
            screen.setFieldsVisible(fieldGroupName='fgLinkToolbar',
                                    fieldNames=['bttHideFgLinkDtl', 'bttSaveFgLink', 'bttDeleteFgLink'],
                                    visible=isSelectedScreenSn and (currentFgLinkId is not None or isNewFgLink))

            # field group header and footer page
            screen.setFieldGroupsVisible(fieldGroupNames=['fgHeaderFooterDtlFg'], visible=isSelectedScreenSn and (currentFgHeaderFooterId is not None or isNewFgHeaderFooter))
            screen.setFieldsVisible(fieldGroupName='fgHeaderFooterToolbar', fieldNames='bttNewFgHeaderFooter', visible=isSelectedScreenSn)
            screen.setFieldsVisible(fieldGroupName='fgHeaderFooterToolbar',
                                    fieldNames=['bttHideFgHeaderFooterDtl', 'bttSaveHeaderFooter', 'bttDeleteHeaderFooter'],
                                    visible=isSelectedScreenSn and (currentFgHeaderFooterId is not None or isNewFgHeaderFooter))

        self.beforeDisplayAdapter = beforeDisplayAdapter

    # Screen
    def newScreen(self):
        self.deleteSessionParameters(
            nameFilters=['isNewScreen', 'screenSN', 'isNewFg', 'currentFgID', 'isNewFgLink', 'currentFgLinkID', 'isNewFgHeaderFooter', 'currentFgHeaderFooterID'])
        self.setSessionParameters({"isNewScreen": True})
        return IkSccJsonResponse()

    def importScreen(self):
        ImportScreen = self.getRequestData().getFile('ImportScreen')
        if ImportScreen is None:
            return IkErrJsonResponse(message="Please select a file to upload.")
        b = ikuidb.updateDatabaseWithImportExcel(ImportScreen, self.getCurrentUserId())
        if b.value:
            self.deleteSessionParameters(
                nameFilters=['isNewScreen', 'screenSN', 'isNewFg', 'currentFgID', 'isNewFgLink', 'currentFgLinkID', 'isNewFgHeaderFooter', 'currentFgHeaderFooterID'])
        return b.toIkJsonResponse1()

    def downloadExample(self):
        exampleFileFolder = ikui.IkUI.getScreenFileExampleFolder()
        exampleFile = ikfs.getLastRevisionFile(exampleFileFolder, 'example.xlsx')
        if isNullBlank(exampleFile):
            logger.error("Example file does not exist in folder [%s]." % exampleFileFolder.absolute())
            return Boolean2(False, 'Screen example file not found. Please check.')
        return self.downloadFile(exampleFile)

    def syncScreenDefinitions(self):
        return ikuidb.syncScreenDefinitions(self.getCurrentUserId())

    def createCSVFile(self):
        b = ikuidb.createCSVFileWithDatabase()
        if not b.value:
            return b.toIkJsonResponse1()
        return IkSccJsonResponse(message="Successfully created csv files for all pages.")

        # get all screens combobox
    def getScreens(self):
        data = []
        subquery = Screen.objects.filter(screen_sn=OuterRef('screen_sn')).order_by('-rev').values('id')[:1]
        screenRcs = Screen.objects.filter(id__in=Subquery(subquery)).order_by('screen_sn')

        # Pre-fetch the latest ScreenFile for each Screen
        screenFileRcs = ScreenFile.objects.filter(screen__in=screenRcs).order_by('screen', '-file_dt')
        # Use Prefetch to fetch related ScreenFile objects into Screen objects
        screenRcs = screenRcs.prefetch_related(Prefetch('screenfile_set', queryset=screenFileRcs, to_attr='screen_files'))

        for screenRc in screenRcs:
            if len(screenRc.screen_files) == 1:
                screenFileRc = screenRc.screen_files[0]
            elif len(screenRc.screen_files) > 1:
                screenFileRc = sorted(screenRc.screen_files, key=lambda x: x.file_dt, reverse=True)[0]
            else:
                screenFileRc = None
            if isNullBlank(screenFileRc):
                dt = ''
            else:
                dt = screenFileRc.file_dt.strftime('%Y-%m-%d %H:%M:%S')
            data.append({'screen_sn': screenRc.screen_sn, 'screen_full_sn': screenRc.screen_sn + " - v" + str(screenRc.rev) + " - " + dt + " - " + screenRc.app_nm })
        data = sorted(data, key=lambda x: x['screen_full_sn'])
        return data

    # get selected screen
    def getScreenSelectRc(self):
        data = None
        if not strUtils.isEmpty(self.getSessionParameter("screenSN")):
            data = {'screenField': self.getSessionParameter("screenSN")}
        return IkSccJsonResponse(data=data)

    # screenSelectFg change event
    def changeScreen(self):
        screenSelectionFg = self.getRequestData().get('screenSelectionFg', None)
        if screenSelectionFg:
            screenSn = screenSelectionFg['value']
            self.setSessionParameters({"screenSN": screenSn})
        return self.deleteSessionParameters(
            nameFilters=['currentFgID', 'currentFgLinkID', 'currentFgHeaderFooterID', 'isNewScreen', 'isNewFg', 'isNewFgLink', 'isNewFgHeaderFooter'])

    def getScreenRc(self):
        data = {}
        screenSn = self.getSessionParameter("screenSN")
        isNewScreen = self.getSessionParameterBool("isNewScreen")
        if not strUtils.isEmpty(screenSn) and not isNewScreen:
            data = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        else:
            data['template_version'] = 1
            data['editable'] = True
        return data

    def getScreenLayoutType(self):
        layoutType = Screen._meta.get_field('layout_type')
        layoutTypeChoices = layoutType.choices
        data = []
        for choice in layoutTypeChoices:
            data.append({"value": choice[0], "display": choice[1]})
        return data

    def saveScreen(self):
        screenSn = self.getSessionParameter("screenSN")
        isNewScreen = self.getSessionParameterBool("isNewScreen")
        if strUtils.isEmpty(screenSn) and not isNewScreen:
            return IkErrJsonResponse(message="Please select a Screen first.")
        boo = ScreenDfnManager.saveScreen(self, screenSn, isNewScreen, True)
        if boo.value and isNewScreen:
            self.deleteSessionParameters("isNewScreen")
        return boo.toIkJsonResponse1()

    def deleteScreen(self):
        screenSn = self.getSessionParameter("screenSN")
        isNewScreen = self.getSessionParameterBool("isNewScreen")
        if strUtils.isEmpty(screenSn) and not isNewScreen:
            return IkErrJsonResponse(message="Please select a Screen first.")
        boo = ScreenDfnManager.deleteScreen(self, screenSn)
        if boo.value:
            self.deleteSessionParameters(
                nameFilters=['isNewScreen', 'screenSN', 'isNewFg', 'currentFgID', 'isNewFgLink', 'currentFgLinkID', 'isNewFgHeaderFooter', 'currentFgHeaderFooterID'])
        return boo.toIkJsonResponse1()

    def getHtmlDialogDeleteScreenHtml(self):
        screenSn = self.getSessionParameter("screenSN")
        html = '<div style="font-size: 9pt">Are you sure to delete screen [' + screenSn + ']?</div>'
        html += '<div style="color: red; font-size: 9pt; padding-top: 10px">Please note that it cannot be restored after deletion!</div>'
        return IkSccJsonResponse(data=html)

    def deleteLastScreen(self):
        screenSn = self.getSessionParameter("screenSN")
        isNewScreen = self.getSessionParameterBool("isNewScreen")
        if strUtils.isEmpty(screenSn) and not isNewScreen:
            return IkErrJsonResponse(message="Please select a Screen first.")
        boo = ScreenDfnManager.deleteLastScreen(self, screenSn)
        if boo.value:
            self.deleteSessionParameters(nameFilters=['isNewScreen', 'isNewFg', 'currentFgID', 'isNewFgLink', 'currentFgLinkID', 'isNewFgHeaderFooter', 'currentFgHeaderFooterID'])
        return boo.toIkJsonResponse1()

    def checkBeforeDeleteLast(self):
        requestData = self.getRequestData()
        currentCategoryRc = requestData.get('screenDtlFg', None)

        message = 'Are you sure to delete the last definition of screen [' + currentCategoryRc.screen_sn + ']?'
        return ikui.DialogMessage.getSuccessResponse(message=message)

    def copyScreen(self):
        userID = self.getCurrentUserId()
        screenSn = self.getSessionParameter("screenSN")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        dialogCopyPramsFg = self.getRequestData().get('dialogCopyPramsFg', None)
        if isNullBlank(dialogCopyPramsFg) or isNullBlank(dialogCopyPramsFg['screenSn']):
            return IkErrJsonResponse(message="Please set the Screen ID of new page.")
        newScreenSn = dialogCopyPramsFg['screenSn']
        screenRcs = Screen.objects.filter(screen_sn__iexact=newScreenSn)
        if len(screenRcs) > 0:
            return IkErrJsonResponse(message="This Screen ID [%s] already exists, please re-enter." % newScreenSn)
        boo = ScreenDfnManager.copyScreen(self, userID, screenSn, newScreenSn)
        return boo.toIkJsonResponse1()

    def exportScreen(self):
        '''
            Export the selected screen to file and download.
        '''
        screenSn = self.getSessionParameter("screenSN")
        if isNullBlank(screenSn):
            return Boolean2(False, 'Not yet saved, please save and then export.')
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by('-rev').first()
        b = ikuidb.screenDbWriteToExcel(screenRc)
        if not b.value:
            return b
        return self.downloadFile(b.data)

    def resetRev(self):
        userID = self.getCurrentUserId()
        screenSn = self.getSessionParameter("screenSN")
        resData = self.getRequestData()
        newRev = resData.get('dialogResetRevFg', {}).get('newRev', '')
        if isNullBlank(newRev):
            return IkErrJsonResponse(message="Please set the new screen revision.")
        try:
            newRev = int(newRev)
        except:
            return IkErrJsonResponse(message="New screen revision must be a number.")
        b = ScreenDfnManager.resetRev(userID, screenSn, newRev)
        return b.toIkJsonResponse1()

    def refresh(self):
        return IkSccJsonResponse(message='Refreshed.')

    # XH 2023-05-04 END

    # Recordset
    def getRecordsetRcs(self):
        recordsetRcs = []
        screenSn = self.getSessionParameter("screenSN")
        if not strUtils.isEmpty(screenSn):
            screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            recordsetRcs = list(ScreenRecordset.objects.filter(screen=screenRc))
            recordsetRcs.sort(key=lambda obj: (obj.seq, obj.recordset_nm))  # sort fields
            seq1 = 1
            for recordsetRc in recordsetRcs:
                recordsetRc.seq = seq1
                seq1 += 1
        return recordsetRcs

    # # check delete status records was be used.
    # def checkRecordsetIsRelated(self):
    #     # check recordset is been used
    #     screenSn = self.getSessionParameter("screenSN")
    #     if strUtils.isEmpty(screenSn):
    #         return IkErrJsonResponse(message="Please select a Screen first.")
    #     screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
    #     if screenRc is None:
    #         return IkErrJsonResponse(message=screenSn + " does not exist, please ask administrator to check.")
    #     recordsetLists = self.getRequestData().get("recordsetListFg", None)
    #     for rc in recordsetLists:
    #         if rc.ik_is_status_delete():
    #             relateFgRc = ScreenFieldGroup.objects.filter(screen=screenRc, recordset__id=rc.id).first()
    #             if relateFgRc:
    #                 return IkErrJsonResponse(message=rc.recordset_nm + " was used by field group: " + relateFgRc.fg_nm + ", please delete " + relateFgRc.fg_nm + " first.")
    #     return IkSccJsonResponse()

    def saveRecordsets(self):
        screenSn = self.getSessionParameter("screenSN")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        boo = ScreenDfnManager.saveScreenRecordsets(self, screenSn, True)
        return boo.toIkJsonResponse1()

    # Field Group
    # list screen's field group
    def getYesNoArr(self):
        return [{"value": True, "display": "Yes"}, {"value": False, "display": "No"}]

    def getFieldGroupRcs(self):
        screenSn = self.getSessionParameter("screenSN")
        data = []
        if not strUtils.isEmpty(screenSn):
            screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            data = ScreenFieldGroup.objects.filter(screen=screenRc).order_by("seq")
            data = [model_to_dict(instance) for instance in data]
            # set cursor
            fieldGroupId = self.getSessionParameterInt("currentFgID")
            for d in data:
                if fieldGroupId and int(fieldGroupId) == int(d['id']):
                    d['__CRR_'] = True
                d['fg_type_nm'] = ScreenFgType.objects.filter(id=d['fg_type']).first().type_nm if d['fg_type'] else None
                d['recordset_nm'] = ScreenRecordset.objects.filter(id=d['recordset']).first().recordset_nm if d['recordset'] else None
                d['deletable'] = "yes" if d['deletable'] else None
                d['editable'] = "yes" if d['editable'] else None
                d['insertable'] = "yes" if d['insertable'] else None
                d['highlight_row'] = "yes" if d['highlight_row'] else None
                d['selection_mode'] = d['selection_mode'] if d['selection_mode'] != 'none' else None
        return IkSccJsonResponse(data=data)

    # open field group detail
    def openFieldGroup(self):
        fieldGroupId = self.getRequestData().get('EditIndexField')
        fieldGroupId = fieldGroupId if not strUtils.isEmpty(fieldGroupId) else self.getSessionParameterInt("currentFgID")
        if strUtils.isEmpty(fieldGroupId):
            logger.error("open field group failed.")
            return IkErrJsonResponse(message="System error, please ask administrator to check.")
        else:  # click new -> open detail
            self.deleteSessionParameters("isNewFg")
        self.setSessionParameters({"currentFgID": fieldGroupId})
        return IkSccJsonResponse()

    # field group detail
    def getFieldGroupRc(self):
        fieldGroupId = self.getSessionParameterInt("currentFgID")
        isNewFg = self.getSessionParameterBool("isNewFg")
        data = {}
        if fieldGroupId and not isNewFg:
            data = ScreenFieldGroup.objects.filter(id=fieldGroupId).first()
        else:
            data['editable'] = True
        return IkSccJsonResponse(data=data)

    # field group types
    def getFgTypes(self):
        typeRcs = ScreenFgType.objects.all().order_by('type_nm')
        sysTypeList, usrTypeList = [], []
        for i in typeRcs:
            if i.type_nm in ikui.SCREEN_FIELD_NORMAL_GROUP_TYPES:
                sysTypeList.append({'id': i.id, 'type_nm': i.type_nm})
            else:
                usrTypeList.append({'id': i.id, 'type_nm': "Custom - " + i.type_nm})
        return IkSccJsonResponse(data=[*sysTypeList, *usrTypeList])

    # get screen recordsets
    def getScreenRecordsets(self):
        screenSn = self.getSessionParameter("screenSN")
        data = []
        if not strUtils.isEmpty(screenSn):
            screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            data = ScreenRecordset.objects.filter(screen=screenRc).order_by("id")
        return IkSccJsonResponse(data=data)

    # get field group page type
    def getSelectionModes(self):
        selectionMode = ScreenFieldGroup._meta.get_field('selection_mode')
        selectionModeChoices = selectionMode.choices
        data = [{"value": choice[0], "display": choice[1]} for choice in selectionModeChoices]
        return data

    # get field group page type
    def getFgPageTypes(self):
        pageType = ScreenFieldGroup._meta.get_field('data_page_type')
        pageTypeChoices = pageType.choices
        data = [{"value": choice[0], "display": choice[1]} for choice in pageTypeChoices]
        return data

    # get field group's fields
    def getFieldRcs(self):
        fieldGroupId = self.getSessionParameterInt("currentFgID")
        isNewFg = self.getSessionParameterBool("isNewFg")
        data = []
        if fieldGroupId and not isNewFg:
            data = ScreenField.objects.filter(field_group__id=fieldGroupId).order_by("seq")
        return IkSccJsonResponse(data=data)

    # get field all widget
    def getWidgets(self):
        widgetRcs = ScreenFieldWidget.objects.all().order_by('widget_nm')
        sysWidgetList, usrWidgetList = [{'widget_id': None, 'widget_nm': None}], []
        for i in widgetRcs:
            if i.widget_nm in ikui.SCREEN_FIELD_NORMAL_WIDGETS:
                sysWidgetList.append({'widget_id': i.id, 'widget_nm': i.widget_nm})
            else:
                usrWidgetList.append({'widget_id': i.id, 'widget_nm': "Custom - " + i.widget_nm})
        return IkSccJsonResponse(data=[*sysWidgetList, *usrWidgetList])

    def getUnique(self):
        uniqueRcs = [{'unique': None}, {'unique': 'true'}, {'unique': 'false'}]
        return IkSccJsonResponse(data=uniqueRcs)

    def getRequired(self):
        requiredRcs = [{'required': None}, {'required': 'true'}, {'required': 'false'}]
        return IkSccJsonResponse(data=requiredRcs)

    # events
    def newFieldGroup(self):
        self.deleteSessionParameters(nameFilters=['isNewScreen', 'isNewFg', 'currentFgID', 'isNewFgLink', 'currentFgLinkID', 'isNewFgHeaderFooter', 'currentFgHeaderFooterID'])
        self.setSessionParameters({"isNewFg": True})
        return IkSccJsonResponse()

    # XH 2023-04-24 START
    def checkFieldIsRelated(self):
        screenSn = self.getSessionParameter("screenSN")
        fieldGroupId = self.getSessionParameterInt("currentFgID")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        if screenRc is None:
            return IkErrJsonResponse(message=screenSn + " does not exist, please ask administrator to check.")

        fieldListFg = self.getRequestData().get("fieldListFg")
        message = "Are you sure save this field group?\n"
        delNum = 0
        for i in fieldListFg:
            if i.ik_is_status_delete():
                relatedFgHeaderFooterRc = ScreenFgHeaderFooter.objects.filter(screen=screenRc, field_group__id=fieldGroupId, field__id=i.id).first()
                if relatedFgHeaderFooterRc:
                    delNum += 1
                    message += "\nField name: " + i.field_nm + "  will be deleted"
        if delNum > 0:
            if delNum == 1:
                message += "\n\nThis field has been used for header and footer table."
            elif delNum > 1:
                message += "\nThese fields has been used for header and footer table."
            message += "\nAre you sure to delete?"
        return ikui.DialogMessage.getSuccessResponse(message=message)

    # XH 2023-04-24 END

    def saveFieldGroup(self):
        screenSn = self.getSessionParameter("screenSN")
        isNewFg = self.getSessionParameterBool("isNewFg")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        boo = ScreenDfnManager.saveFieldGroup(self, screenSn, isNewFg, True)
        if boo.value:
            self.openFieldGroup()
            self.deleteSessionParameters("isNewFg")
        return boo.toIkJsonResponse1()

    # check related table when delete field group
    def checkFgIsRelated(self):
        screenSn = self.getSessionParameter("screenSN")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        if screenRc is None:
            return IkErrJsonResponse(message=screenSn + " does not exist, please ask administrator to check.")

        fieldGroupId = self.getSessionParameterInt("currentFgID")
        message = "Are you sure delete this field group and all fields under this field group?"
        if fieldGroupId:
            # check field group link and header footer table
            relatedFgLinkRc = ScreenFgLink.objects.filter(screen=screenRc).filter((Q(field_group__id=fieldGroupId) | Q(parent_field_group__id=fieldGroupId))).first()
            relatedFgHeaderFooterRc = ScreenFgHeaderFooter.objects.filter(screen=screenRc, field_group__id=fieldGroupId).first()
            if relatedFgLinkRc or relatedFgHeaderFooterRc:
                message = "This field group has been used for field group links or header and footer table, are you sure to delete?"
        return ikui.DialogMessage.getSuccessResponse(message=message)

    # delete field group
    def deleteFieldGroup(self):
        screenSn = self.getSessionParameter("screenSN")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        fieldGroupId = self.getSessionParameterInt("currentFgID")
        if not fieldGroupId:
            logger.error("Delete Field Group function get field group Id failed.")
            return IkSysErrJsonResponse()
        self.setSessionParameters({"isDeleteFieldGroup": True})
        boo = ScreenDfnManager.deleteFieldGroup(self, screenSn, fieldGroupId)
        self.deleteSessionParameters("isDeleteFieldGroup")
        if boo.value:
            self.deleteSessionParameters("currentFgID")
            return IkSccJsonResponse(message="Deleted field group.")
        return boo.toIkJsonResponse1()

    def getScreenDfnRcs(self):
        screenSn = self.getSessionParameter("screenSN")
        data = []
        if isNotNullBlank(screenSn):
            screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            data = ScreenDfn.objects.filter(screen=screenRc).order_by('sub_screen_nm')
            if len(data) == 0:
                data = [ScreenDfn(sub_screen_nm=ikui.MAIN_SCREEN_NAME)]
        return IkSccJsonResponse(data=data)

    def saveSubScreen(self):
        screenSn = self.getSessionParameter("screenSN")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        boo = ScreenDfnManager.saveSubScreen(self, screenSn, True)
        return boo.toIkJsonResponse1()

    # Field Group Links
    # get field group's field group links
    def getFgLinkRcs(self):
        screenSn = self.getSessionParameter("screenSN")
        data = []
        if not strUtils.isEmpty(screenSn):
            screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            data = ScreenFgLink.objects.filter(screen=screenRc).select_related('field_group', 'parent_field_group').order_by("field_group__seq")
            data = [model_to_dict(instance) for instance in data]
            # set cursor
            fgLinkId = self.getSessionParameterInt("currentFgLinkID")
            for d in data:
                if fgLinkId and int(fgLinkId) == int(d['id']):
                    d['__CRR_'] = True
                d['field_group_nm'] = ScreenFieldGroup.objects.filter(id=d['field_group']).first().fg_nm
                d['parent_field_group_nm'] = ScreenFieldGroup.objects.filter(id=d['parent_field_group']).first().fg_nm
        return IkSccJsonResponse(data=data)

    # open field group link detail
    def openFgLink(self):
        fgLinkId = self.getRequestData().get('EditIndexField')
        fgLinkId = fgLinkId if not strUtils.isEmpty(fgLinkId) else self.getSessionParameterInt("currentFgLinkID")
        if strUtils.isEmpty(fgLinkId):
            logger.error("open field group link failed.")
            return IkErrJsonResponse(message="System error, please ask administrator to check.")
        else:  # click new -> open detail
            self.deleteSessionParameters("isNewFgLink")
        self.setSessionParameters({"currentFgLinkID": fgLinkId})
        return IkSccJsonResponse()

    # field group link detail
    # XH 2023-04-24 START
    # XH 2023-04-25 START
    def getFgLinkRc(self):
        fgLinkId = self.getSessionParameterInt("currentFgLinkID")
        isNewFgLink = self.getSessionParameterBool("isNewFgLink")
        data = {}
        if fgLinkId and not isNewFgLink:
            data = ScreenFgLink.objects.filter(id=fgLinkId).first()
        return IkSccJsonResponse(data=data)

    # all type field group for field group link
    def getFieldGroups(self):
        screenSn = self.getSessionParameter("screenSN")
        data = []
        if screenSn:
            screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            querySet = ScreenFieldGroup.objects.filter(screen=screenRc).exclude(recordset=None).exclude(recordset__sql_models__icontains="DummyModel").order_by("seq")
            # TODO DummyModel should preferably also support getting the fields we set
            data = [{'field_group_id': i.id, 'fg_nm': i.fg_nm} for i in querySet]
        return IkSccJsonResponse(data=data)

    def getParentFieldGroups(self):
        screenSn = self.getSessionParameter("screenSN")
        data = []
        if screenSn:
            screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            querySet = ScreenFieldGroup.objects.filter(screen=screenRc).exclude(recordset=None).exclude(recordset__sql_models__icontains="DummyModel").order_by("seq")
            data = [{'parent_field_group_id': i.id, 'fg_nm': i.fg_nm} for i in querySet]
        return IkSccJsonResponse(data=data)

    # onChange: field group change will change db keys and parent field group
    def changeDbKeyAndPFgs(self):
        screenSn = self.getSessionParameter("screenSN")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        fgLinkDtlFg = self.getRequestData().get("fgLinkDtlFg")
        fgId = fgLinkDtlFg['field_group_id']
        # parent field groups
        pFgQuerySet = ScreenFieldGroup.objects.filter(screen=screenRc).exclude(recordset=None).exclude(recordset__sql_models__icontains="DummyModel").exclude(
            id=fgId).order_by("seq")
        pFgData = [{'parent_field_group_id': i.id, 'fg_nm': i.fg_nm} for i in pFgQuerySet]
        # db keys
        dbKeyData = ScreenDfnManager.getFieldDBKeys(screenRc, ScreenFieldGroup.objects.filter(id=fgId).first())
        return self._returnComboboxQueryResult(fgName='fgLinkDtlFg', fgData=None, resultDict={'dtlFgLinkLocalKeyField': dbKeyData, 'dtlFgLinkParentFgNmField': pFgData})

    # onChange: field group change will change db keys
    def changeDbKeys(self):
        screenSn = self.getSessionParameter("screenSN")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        fgLinkDtlFg = self.getRequestData().get("fgLinkDtlFg")
        fgId = fgLinkDtlFg['parent_field_group_id']
        dbKeyData = ScreenDfnManager.getFieldDBKeys(screenRc, ScreenFieldGroup.objects.filter(id=fgId).first())
        return self._returnComboboxQueryResult(fgName='fgLinkDtlFg', fgData=None, resultDict={'dtlFgLinkParentKeyField': dbKeyData})

    # get field group's field db keys
    def getFgFieldDbKeys(self):
        screenSn = self.getSessionParameter("screenSN")
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        fgLinkId = self.getSessionParameterInt("currentFgLinkID")
        isNewFgLink = self.getSessionParameterBool("isNewFgLink")
        data = []
        if fgLinkId:
            if isNewFgLink:
                field_group = ScreenFieldGroup.objects.filter(screen=screenRc).exclude(recordset=None).exclude(
                    recordset__sql_models__icontains="DummyModel").order_by("seq").first()
                data = ScreenDfnManager.getFieldDBKeys(screenRc, field_group)
            else:
                field_group = ScreenFgLink.objects.filter(id=fgLinkId).first().field_group
                data = ScreenDfnManager.getFieldDBKeys(screenRc, field_group)
        return data

    def getParentFgFieldDbKeys(self):
        screenSn = self.getSessionParameter("screenSN")
        screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
        fgLinkId = self.getSessionParameterInt("currentFgLinkID")
        isNewFgLink = self.getSessionParameterBool("isNewFgLink")
        data = []
        if fgLinkId:
            if isNewFgLink:
                field_group = ScreenFieldGroup.objects.filter(screen=screenRc).exclude(recordset=None).exclude(
                    recordset__sql_models__icontains="DummyModel").order_by("seq").first()
                data = ScreenDfnManager.getFieldDBKeys(screenRc, field_group)
            else:
                parent_field_group = ScreenFgLink.objects.filter(id=fgLinkId).first().parent_field_group
                data = ScreenDfnManager.getFieldDBKeys(screenRc, parent_field_group)
        return data

    # XH 2023-04-25 END
    # XH 2023-04-24 END

    # events
    def newFgLink(self):
        self.deleteSessionParameters(nameFilters=['isNewScreen', 'isNewFg', 'currentFgID', 'isNewFgLink', 'currentFgLinkID', 'isNewFgHeaderFooter', 'currentFgHeaderFooterID'])
        self.setSessionParameters({"isNewFgLink": True})
        return IkSccJsonResponse()

    def saveFgLink(self):
        screenSn = self.getSessionParameter("screenSN")
        isNewFgLink = self.getSessionParameterBool("isNewFgLink")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        boo = ScreenDfnManager.saveFgLink(self, screenSn, isNewFgLink, True)
        if boo.value and isNewFgLink:
            self.deleteSessionParameters("isNewFgLink")
        return boo.toIkJsonResponse1()

    def deleteFgLink(self):
        screenSn = self.getSessionParameter("screenSN")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        fgLinkId = self.getSessionParameterInt("currentFgLinkID")
        if not fgLinkId:
            logger.error("Delete Field Group Link function get field group link Id failed.")
            return IkSysErrJsonResponse()
        self.setSessionParameters({"isDeleteFgLink": True})
        boo = ScreenDfnManager.deleteFgLink(self, screenSn, fgLinkId)
        self.deleteSessionParameters("isDeleteFgLink")
        if boo.value:
            self.deleteSessionParameters("currentFgLinkID")
            return IkSccJsonResponse(message="Deleted field group link.")
        return boo.toIkJsonResponse1()

    # Header And Footer
    # get field group's header and footer
    def getFgHeaderFooterRcs(self):
        screenSn = self.getSessionParameter("screenSN")
        data = []
        if not strUtils.isEmpty(screenSn):
            screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            data = ScreenFgHeaderFooter.objects.filter(screen=screenRc).order_by("field_group__seq", "field__seq")
            data = [model_to_dict(instance) for instance in data]
            # set cursor
            fgHeaderFooterId = self.getSessionParameterInt("currentFgHeaderFooterID")
            for d in data:
                if fgHeaderFooterId and int(fgHeaderFooterId) == int(d['id']):
                    d['__CRR_'] = True
                d['field_group_nm'] = ScreenFieldGroup.objects.filter(id=d['field_group']).first().fg_nm
                d['field_nm'] = ScreenField.objects.filter(id=d['field']).first().field_nm
        return IkSccJsonResponse(data=data)

    # open header and footer detail
    def openFgHeaderFooter(self):
        fgHeaderFooterId = self.getRequestData().get('EditIndexField')
        fgHeaderFooterId = fgHeaderFooterId if not strUtils.isEmpty(fgHeaderFooterId) else self.getSessionParameterInt("currentFgHeaderFooterID")
        if strUtils.isEmpty(fgHeaderFooterId):
            logger.error("open Table Header and Footer detail failed.")
            return IkErrJsonResponse(message="System error, please ask administrator to check.")
        else:  # click new -> open detail
            self.deleteSessionParameters("isNewFgHeaderFooter")
        self.setSessionParameters({"currentFgHeaderFooterID": fgHeaderFooterId})
        return IkSccJsonResponse()

    # header and footer detail
    # XH 2023-04-25 START
    def getFgHeaderFooterRc(self):
        fgHeaderFooterId = self.getSessionParameterInt("currentFgHeaderFooterID")
        isNewFgHeaderFooter = self.getSessionParameterBool("isNewFgHeaderFooter")
        screenSn = self.getSessionParameter("screenSN")
        data = {}
        if fgHeaderFooterId and not isNewFgHeaderFooter:
            data = ScreenFgHeaderFooter.objects.filter(id=fgHeaderFooterId).first()
            if data:
                data = model_to_dict(data)
                data['field_group_id'] = data['field_group']
                data['field_id'] = data['field']
        return IkSccJsonResponse(data=data)

    # XH 2023-04-25 END

    # just get table type field group for header and footer table
    def getTableFieldGroups(self):
        screenSn = self.getSessionParameter("screenSN")
        data = []
        if screenSn:
            screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
            data = ScreenFieldGroup.objects.filter(screen=screenRc, fg_type__type_nm__icontains="table").order_by("seq")
        return IkSccJsonResponse(data=data)

    # onChange
    # get selected field group's field
    def changeFgFields(self):
        fgHeaderFooterDtlFg = self.getRequestData().get("fgHeaderFooterDtlFg")
        fgId = fgHeaderFooterDtlFg['field_group_id']
        data = []
        if fgId:
            data = ScreenField.objects.filter(field_group__id=fgId).order_by("seq")  # .values_list('id', flat=True))
        return self._returnComboboxQueryResult(fgName='fgHeaderFooterDtlFg', fgData=None, resultDict={'dtlFgHfFieldNmField': data})

    # XH 2023-04-25 START
    def getFgFields(self):
        fgHeaderFooterId = self.getSessionParameterInt("currentFgHeaderFooterID")
        isNewFgHeaderFooter = self.getSessionParameterBool("isNewFgHeaderFooter")
        screenSn = self.getSessionParameter("screenSN")
        data = []
        if fgHeaderFooterId:
            if isNewFgHeaderFooter:
                screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
                field_group = ScreenFieldGroup.objects.filter(screen=screenRc).filter(fg_type__type_nm__icontains="table").order_by("seq").first()
                if field_group:
                    data = ScreenField.objects.filter(screen=screenRc, field_group=field_group).order_by("seq")
            else:
                field_group = ScreenFgHeaderFooter.objects.filter(id=fgHeaderFooterId).first().field_group
                if field_group:
                    data = ScreenField.objects.filter(field_group=field_group)
        return IkSccJsonResponse(data=data)

    # XH 2023-04-25 END

    # events
    def newFgHeaderFooter(self):
        self.deleteSessionParameters(nameFilters=['isNewScreen', 'isNewFg', 'currentFgID', 'isNewFgLink', 'currentFgLinkID', 'isNewFgHeaderFooter', 'currentFgHeaderFooterID'])
        self.setSessionParameters({"isNewFgHeaderFooter": True})
        return IkSccJsonResponse()

    def saveFgHeaderFooter(self):
        screenSn = self.getSessionParameter("screenSN")
        isNewFgHeaderFooter = self.getSessionParameterBool("isNewFgHeaderFooter")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        boo = ScreenDfnManager.saveFgHeaderFooter(self, screenSn, isNewFgHeaderFooter, True)
        if boo.value and isNewFgHeaderFooter:
            self.deleteSessionParameters("isNewFgHeaderFooter")
        return boo.toIkJsonResponse1()

    def deleteFgHeaderFooter(self):
        screenSn = self.getSessionParameter("screenSN")
        if strUtils.isEmpty(screenSn):
            return IkErrJsonResponse(message="Please select a Screen first.")
        fgHeaderFooterId = self.getSessionParameterInt("currentFgHeaderFooterID")
        if not fgHeaderFooterId:
            logger.error("Delete Field Group Header And Footer function get field group link Id failed.")
            return IkSysErrJsonResponse()
        self.setSessionParameters({"isDeleteFgHeaderFooter": True})
        boo = ScreenDfnManager.deleteFgHeaderFooter(self, screenSn, fgHeaderFooterId)
        self.deleteSessionParameters("isDeleteFgHeaderFooter")
        if boo.value:
            self.deleteSessionParameters("currentFgHeaderFooterID")
            return IkSccJsonResponse(message="Deleted header and footer table.")
        return boo.toIkJsonResponse1()

    def hideFgDetail(self):
        return self.deleteSessionParameters(nameFilters=["currentFgID", "isNewFg"])

    def hideFgLinkDetail(self):
        return self.deleteSessionParameters(nameFilters=["currentFgLinkID", "isNewFgLink"])

    def hideFgHeaderFooterDetail(self):
        return self.deleteSessionParameters(nameFilters=["currentFgHeaderFooterID", "isNewFgHeaderFooter"])

    def getDialogWidgetPramsRc(self):
        widgetNm = self.getSessionParameter('widgetNm')
        widgetPrams = self.getSessionParameter('widgetPrams')
        dialogWidgetPramsRc = self.getSessionParameter('dialogWidgetPramsRc')
        if isNotNullBlank(dialogWidgetPramsRc):
            self.deleteSessionParameters('dialogWidgetPramsRc')
            return IkSccJsonResponse(data=dialogWidgetPramsRc)

        if widgetNm == ikui.SCREEN_FIELD_WIDGET_DATE_BOX and widgetPrams == {}:
            widgetPrams = {'format': 'yyyy-MM-dd'}
        elif widgetNm == ikui.SCREEN_FIELD_WIDGET_CHECK_BOX and widgetPrams == {}:
            widgetPrams = {'stateNumber': '2', 'captionPosition': 'left'}
        elif (widgetNm == ikui.SCREEN_FIELD_WIDGET_ICON_AND_TEXT or widgetNm == ikui.SCREEN_FIELD_WIDGET_BUTTON):
            if 'type' not in widgetPrams:
                widgetPrams['type'] = 'normal'
        elif (widgetNm in ikui.SCREEN_FIELD_SELECT_WIDGETS or widgetNm == ikui.SCREEN_FIELD_WIDGET_LABEL):
            # if 'values' not in widgetPrams:
            #     widgetPrams['value'] = "value"
            #     widgetPrams['display'] = "display"
            if 'recordset' in widgetPrams:
                screenSn = self.getSessionParameter("screenSN")
                screenRc = Screen.objects.filter(screen_sn__iexact=screenSn).order_by("-rev").first()
                recordsetRc = ScreenRecordset.objects.filter(screen=screenRc, recordset_nm=widgetPrams['recordset']).first()
                if isNotNullBlank(recordsetRc):
                    widgetPrams['recordset'] = recordsetRc.id

        if isNotNullBlank(widgetPrams):
            if "values" in widgetPrams and isNotNullBlank(widgetPrams['values']):
                values = json.loads(widgetPrams['values'].replace("'", '"'))
                widgetPrams['value'] = values["value"]
                widgetPrams['display'] = values["display"]
            if "dialog" in widgetPrams and isNotNullBlank(widgetPrams['dialog']):
                dialogs = widgetPrams['dialog'].split(";")
                dialog = {}
                for d in dialogs:
                    if isNotNullBlank(d):
                        parts = d.split(":", 1)
                        dialog[parts[0]] = parts[1]
                widgetPrams['name'] = dialog["name"] if 'name' in dialog else ''
                widgetPrams['title'] = dialog["title"] if 'title' in dialog else ''
                widgetPrams['uploadTip'] = dialog["uploadTip"] if 'uploadTip' in dialog else ''
                widgetPrams['beforeDisplayEvent'] = dialog["beforeDisplayEvent"] if 'beforeDisplayEvent' in dialog else ''
                widgetPrams['continueName'] = dialog["continueName"] if 'continueName' in dialog else ''
                widgetPrams['cancelName'] = dialog["cancelName"] if 'cancelName' in dialog else ''
                widgetPrams['width'] = dialog["width"] if 'width' in dialog else ''
                widgetPrams['height'] = dialog["height"] if 'height' in dialog else ''
                widgetPrams['content'] = dialog["content"] if 'content' in dialog else ''
        return IkSccJsonResponse(data=widgetPrams)

    def postRow(self):
        row = self.getRequestData().get('row', {})
        widgetID = row.get('widget_id', '')
        widgetPrams = row.get('widget_parameters', '')
        self.deleteSessionParameters('dialogWidgetPramsRc')
        self.setSessionParameters({'widgetPrams': ikui.IkUI.parseWidgetPrams(widgetPrams)})

        message = ''
        if isNullBlank(widgetID):
            self.setSessionParameters({'widgetNm': ''})
            message = 'Please select a Widget first.'
        else:
            widgetRc = ScreenFieldWidget.objects.filter(id=widgetID).first()
            if isNotNullBlank(widgetRc):
                self.setSessionParameters({'widgetNm': widgetRc.widget_nm})
                if widgetRc.widget_nm in ScreenDfnManager.NO_PARAMETERS_WIDGET:
                    message = 'This widget does not require parameters.'
        return ikui.DialogMessage.getSuccessResponse(message=message)

    def getFormat(self):
        data = [{
            'value': 'yyyy-MM-dd',
            'display': 'yyyy-MM-dd (default)'
        }, {
            'value': 'YYYY-MM-DD HH:mm:ss',
            'display': 'YYYY-MM-DD HH:mm:ss'
        }, {
            'value': 'HH:mm:ss',
            'display': 'HH:mm:ss'
        }]
        return IkSccJsonResponse(data=data)

    def getStateNum(self):
        data = [{'value': '2', 'display': '2 (default)'}, {'value': '3', 'display': '3'}]
        return IkSccJsonResponse(data=data)

    def getBttType(self):
        widgetNm = self.getSessionParameter('widgetNm')
        data = [{'value': 'normal', 'display': 'normal (default)'}, {'value': 'download', 'display': 'download'}]
        if widgetNm == ikui.SCREEN_FIELD_WIDGET_BUTTON:
            data.append({'value': 'uploadDialog', 'display': 'upload dialog'})
        if widgetNm == ikui.SCREEN_FIELD_WIDGET_ICON_AND_TEXT:
            data.append({'value': 'uploadDialog', 'display': 'upload dialog'})
            data.append({'value': 'uploadButton', 'display': 'upload button'})
        return IkSccJsonResponse(data=data)

    def saveBttType(self):
        resData = self.getRequestData()
        dialogWidgetPramsFg = resData.get('dialogWidgetPramsFg', {})
        dialogWidgetDialogPramsFg = resData.get('dialogWidgetDialogPramsFg', {})
        return self.setSessionParameters({'dialogWidgetPramsRc': {**dialogWidgetPramsFg, **dialogWidgetDialogPramsFg}})

    def getCaptionPosition(self):
        data = [{'value': 'left', 'display': 'left (default)'}, {'value': 'right', 'display': 'right'}]
        return IkSccJsonResponse(data=data)

    def uploadWidgetPrams(self):
        resData = self.getRequestData()
        widgetPrams = resData.get('dialogWidgetPramsFg', '')
        widgetDialogPrams = resData.get('dialogWidgetDialogPramsFg', '')
        cleanedDict = {}
        if isNotNullBlank(widgetPrams):
            cleanedDict = {k: v for k, v in widgetPrams.items() if isNotNullBlank(v)}
            if 'recordset' in cleanedDict and isNotNullBlank(cleanedDict['recordset']):
                recordsetRc = ScreenRecordset.objects.filter(id=cleanedDict['recordset']).first()
                recordsetClass = modelUtils.getModelClass(recordsetRc.sql_models)
                if 'DummyModel' not in recordsetRc.sql_models:
                    if 'value' in cleanedDict and not hasattr(recordsetClass, cleanedDict['value']):
                        return IkErrJsonResponse(message='The recordset [%s] does not have the field [%s].' % (recordsetRc.recordset_nm, cleanedDict['value']))
                    if 'display' in cleanedDict and not hasattr(recordsetClass, cleanedDict['display']):
                        return IkErrJsonResponse(message='The recordset [%s] does not have the field [%s].' % (recordsetRc.recordset_nm, cleanedDict['display']))
                cleanedDict['recordset'] = recordsetRc.recordset_nm
            if 'value' in cleanedDict and 'display' in cleanedDict and (cleanedDict['value'] != 'value' or cleanedDict['display'] != 'display'):
                cleanedDict['values'] = '{"value": "%s", "display": "%s"}' % (cleanedDict['value'], cleanedDict['display'])
            if 'value' in cleanedDict:
                cleanedDict.pop('value')
            if 'display' in cleanedDict:
                cleanedDict.pop('display')
            if 'type' in cleanedDict and isNotNullBlank(cleanedDict['type']) and cleanedDict['type'] == 'normal':
                cleanedDict.pop('type')
            if 'multiple' in cleanedDict and cleanedDict['multiple'] == 'false':
                cleanedDict.pop('multiple')
            if 'stateNumber' in cleanedDict and cleanedDict['stateNumber'] == '2':
                cleanedDict.pop('stateNumber')
            if 'captionPosition' in cleanedDict and cleanedDict['captionPosition'] == 'left':
                cleanedDict.pop('captionPosition')
        if isNotNullBlank(widgetDialogPrams):
            dialogPrams = []
            for k, v in widgetDialogPrams.items():
                if isNotNullBlank(v):
                    dialogPrams.append(f"{k}:{v}")
            if len(dialogPrams) > 0:
                cleanedDict['dialog'] = ";".join(dialogPrams)
        newWidgetPrams = '\n'.join(f"{k}: {v}" for k, v in cleanedDict.items())
        data = {'value': newWidgetPrams, 'display': newWidgetPrams}
        return IkSccJsonResponse(data=data)

    def postPreAdditionalProps(self):
        preAdditionalProps = self.getRequestData().get('dtlFgAdditionalPropsField', '')
        return self.setSessionParameter('additionalProps', preAdditionalProps)

    def getDialogAdditionalPropsRc(self):
        additionalProps = self.getSessionParameter("additionalProps", delete=True)
        if isNotNullBlank(additionalProps):
            additionalProps = ikui.IkUI.parseWidgetPrams(additionalProps)
        return IkSccJsonResponse(data=additionalProps)

    def uploadAdditionalProps(self):
        resData = self.getRequestData()
        additionalProps = resData.get('dialogAdditionalPropsFg', '')
        data = ''
        if isNotNullBlank(additionalProps):
            cleanedDict = {k: v for k, v in additionalProps.items() if isNotNullBlank(v) and (k != 'sortNewRows' or v != 'false')}
            newWidgetPrams = '\n'.join(f"{k}: {v}" for k, v in cleanedDict.items())
            data = {'value': newWidgetPrams, 'display': newWidgetPrams}
        return IkSccJsonResponse(data=data)
