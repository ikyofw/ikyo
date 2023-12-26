import hashlib
import logging
import os
from datetime import datetime as datetime_
from pathlib import Path

import core.core.fs as ikfs
import core.utils.modelUtils as ikModelUtils
import core.utils.spreadsheet as ikSpreadsheet
import django.core.files.uploadedfile as djangoUploadedfile
from core.core.exception import IkValidateException
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.models import *
from core.utils.langUtils import isNullBlank

from . import ui as ikui

logger = logging.getLogger('ikyo')


def syncScreenDefinitions(userID=None):
    from core.db.db import getSqlFileFile, executeSqlFiles
    executeSqlFiles(getSqlFileFile('InitSDN.sql'))

    # excel to database
    screenFileFolder = Path(os.path.join(ikfs.getVarFolder(), 'sys', 'views'))
    if not screenFileFolder.is_dir():
        return Boolean2(False, 'Folder %s does not exist' % screenFileFolder)
    else:
        screenFiles = {}
        for f in os.listdir(screenFileFolder):
            fp = Path(os.path.join(screenFileFolder, f))
            if fp.is_dir():
                if not ikui.acceptScreenFolder(fp.name):
                    logger.debug('ignore folder: %s' % fp.name)
                    continue  # ignore "-Templates-" folder.

                fileNms = []
                for f2 in os.listdir(fp):
                    if not f2.lower().endswith(".xlsx"):
                        continue
                    if '-v' in f2:
                        index = f2.find('-v')
                        fileNm = os.path.splitext(f2)[0][:index]
                    else:
                        fileNm = os.path.splitext(f2)[0]
                    if fileNm not in fileNms:
                        fileNms.append(fileNm)
                        path = ikfs.getLastRevisionFile(fp, fileNm + ".xlsx")
                        if os.path.isfile(path) and ikui.acceptScreenFile(f2):
                            screenFiles[f + '.' + fileNm] = str(path)

        for name, path in screenFiles.items():
            sp = ikSpreadsheet.SpreadsheetParser(path)
            if '.' in name:
                i = name.rindex('.')
                shortName = name[i + 1:]
                if shortName == '':
                    return Boolean2(False, "[%s]'s parent folder name cannot be empty. Please check: %s" % (name, path))
            if isNullBlank(shortName):
                shortName = name
            screenDefinition = ikui.ScreenDefinition(name=shortName, fullName=name, filePath=path, definition=sp.data)
            b = _updateDatabaseWithExcelFiles(screenDefinition, userID)
            if not b.value:
                return b

    # database to excel
    screenSNs = Screen.objects.values('screen_sn').distinct().order_by('screen_sn')
    for screenSN in screenSNs:
        b = __createExcelWithDatabase(screenSN, userID)
        if not b.value:
            return b
    return Boolean2(True, "Reloaded")


def updateDatabaseWithImportExcel(ImportScreen: djangoUploadedfile.UploadedFile, userID):
    dfn = ikSpreadsheet.SpreadsheetParser(ImportScreen).data
    try:
        viewClass = ikModelUtils.getModelClass(dfn['viewName'])
    except Exception as e:
        return Boolean2(False, "The format of Class Name is error: %s" % e)
    __updateScreenDatabase(dfn, userID)

    # The imported Excel file's content is updated to the database, then the Excel file is saved at the corresponding location in 'var/views/xxx'.
    latestScreen = Screen.objects.filter(screen_sn__iexact=__strip(dfn['viewID'])).order_by('-rev').first()
    filePath = __getImportScreenFilePath(latestScreen.class_nm)
    filename = '%s-v%s.xlsx' % (latestScreen.screen_sn, latestScreen.rev)
    importFile = os.path.join(filePath, filename)
    if os.path.isfile(importFile):
        os.remove(importFile)
    sw = ikSpreadsheet.SpreadsheetWriter(parameters=None, templateFile=ImportScreen, outputFile=importFile)
    b = sw.write()
    if not b.value:
        return b

    # ik_screen_file
    screenFileRc = ScreenFile()
    screenFileRc.screen = latestScreen
    screenFileRc.file_nm = filename
    screenFileRc.file_size = ImportScreen.size
    screenFileRc.file_path = filePath
    screenFileRc.file_dt = datetime_.now()
    screenFileRc.file_md5 = _getExcelMD5(ImportScreen)
    screenFileRc.rmk = 'Import by Screen Definition'
    ptrn = IkTransaction()
    ptrn.add(screenFileRc)
    b = ptrn.save()
    if not b.value:
        raise IkValidateException(b.dataStr)
    return Boolean2(True, "Imported")


# Output the definition of the target page (screenRc) as an Excel file in a specific format (templateFile) at the specified location (outputFile).
def screenDbWriteToExcel(screenRc, templateFile, outputFile) -> Boolean2:
    # get screen definitions from database
    rsRcs = ScreenRecordset.objects.filter(screen=screenRc).order_by('recordset_nm', 'id')
    fgRcs = ScreenFieldGroup.objects.filter(screen=screenRc).order_by('seq', 'id')
    for rc in fgRcs:
        rc.deletable = 'yes' if rc.deletable == True else ''
        rc.editable = 'yes' if rc.editable == True else ''
        rc.insertable = 'yes' if rc.insertable == True else ''
        rc.highlight_row = 'yes' if rc.highlight_row == True else ''
        rc.sort_new_rows = 'yes' if rc.sort_new_rows == True else ''
        rc.selection_mode = rc.selection_mode if rc.selection_mode != 'none' else ''

    fgFieldRcs = ScreenField.objects.filter(screen=screenRc).order_by('field_group', 'seq', 'id')
    fgNm = ''
    for rc in fgFieldRcs:
        rc.visible = '' if rc.visible == True else 'yes'  # column title: hide
        rc.editable = '' if rc.editable == True else 'no'
        if not rc.field_group:
            continue
        elif fgNm == rc.field_group.fg_nm:
            rc.field_group.fg_nm = ''
        else:
            fgNm = rc.field_group.fg_nm

    dfnRcs = ScreenDfn.objects.filter(screen=screenRc).order_by('sub_screen_nm')

    fgLinkRcs = ScreenFgLink.objects.filter(screen=screenRc).order_by('field_group', 'parent_field_group', 'id')
    hfRcs = ScreenFgHeaderFooter.objects.filter(screen=screenRc).order_by('field_group', 'field__seq')
    fgNm = ''
    for rc in hfRcs:
        if not rc.field_group:
            continue
        if fgNm == rc.field_group.fg_nm:
            rc.field_group.fg_nm = ''
        else:
            fgNm = rc.field_group.fg_nm

    # prepare spreadsheet data
    # screen headers
    expData = {}  # export data
    expData['viewAPIRev'] = screenRc.api_version
    expData['viewID'] = screenRc.screen_sn
    expData['viewTitle'] = screenRc.screen_title
    expData['viewDesc'] = screenRc.screen_dsc
    expData['layoutType'] = screenRc.layout_type
    expData['layoutParams'] = screenRc.layout_params
    expData['viewName'] = screenRc.class_nm
    expData['apiUrl'] = screenRc.api_url
    expData['editable'] = 'yes' if screenRc.editable == True else 'no'
    # expData['autoRefresh'] = ikui.IkUI.getAutoRefreshInfo(screenRc.auto_refresh_interval, screenRc.auto_refresh_action)
    expData['autoRefresh'] = ikui.__ScreenManager.getAutoRefreshInfo(
        None, interval=screenRc.auto_refresh_interval, action=screenRc.auto_refresh_action)
    expData['rev'] = screenRc.rev
    expData['rmk'] = screenRc.rmk
    # screen tables
    expData['recordsetTable'] = ikModelUtils.redcordsets2List(
        rsRcs, ['recordset_nm', 'sql_fields', 'sql_models', 'sql_where', 'sql_order', 'sql_limit', 'rmk'])
    expData['fieldGroupTable'] = ikModelUtils.redcordsets2List(fgRcs, ['fg_nm', 'fg_type.type_nm', 'caption', 'recordset.recordset_nm', 'deletable', 'editable', 'insertable',
                                                                       'highlight_row', 'selection_mode', 'cols', 'sort_new_rows', 'data_page_type', 'data_page_size',
                                                                       'outer_layout_params', 'inner_layout_type', 'inner_layout_params', 'html', 'rmk'])
    expData['fieldTable'] = ikModelUtils.redcordsets2List(fgFieldRcs, ['field_group.fg_nm', 'field_nm', 'caption', 'tooltip', 'visible', 'editable',
                                                                       'widget.widget_nm', 'widget_parameters', 'db_field', 'md_format', 'md_validation', 'event_handler', 'styles', 'rmk'])
    expData['subScreenTable'] = ikModelUtils.redcordsets2List(dfnRcs, ['sub_screen_nm', 'field_group_nms', 'rmk'])
    expData['fieldGroupLinkTable'] = ikModelUtils.redcordsets2List(
        fgLinkRcs, ['field_group.fg_nm', 'local_key', 'parent_field_group.fg_nm', 'parent_key', 'rmk'])
    expData['headerFooterTable'] = ikModelUtils.redcordsets2List(hfRcs,
                                                                 ['field_group.fg_nm', 'field.field_nm', 'header_level1', 'header_level2', 'header_level3', 'footer', 'rmk'])

    # write to file and download if success
    sw = ikSpreadsheet.SpreadsheetWriter(parameters=expData, templateFile=templateFile, outputFile=outputFile)
    b = sw.write()
    return b


def _updateDatabaseWithExcelFiles(screenDefinition, userID):
    if screenDefinition is None:
        return Boolean2(False, 'screenDefinition is None')
    elif screenDefinition.definition is None:
        # for bugfix checking
        logger.error('getScreenDefinition(%s).data=None' % screenDefinition.name)
        return Boolean2(False, 'getScreenDefinition(%s).data=None' % screenDefinition.name)
    dfn = screenDefinition.definition
    lastModifyDtExcel = os.path.getmtime(screenDefinition.filePath)
    lastModifyDtExcel = datetime_.fromtimestamp(lastModifyDtExcel)

    # ik_screen
    latestScreen = Screen.objects.filter(screen_sn__iexact=__strip(dfn['viewID'])).order_by('-rev').first()
    if not isNullBlank(latestScreen) and not __excelHasModify(latestScreen.rev, screenDefinition.filePath):
        # If the screen data already exists in the database and there are no changes compared to the Excel content, then exit the update method directly. 
        return Boolean2(True)
    else:
        filePath = __getImportScreenFilePath(dfn['viewName'])
        # Otherwise, update all the corresponding database tables for that page.
        __updateScreenDatabase(dfn, userID)

        latestScreen = Screen.objects.filter(screen_sn__iexact=__strip(dfn['viewID'])).order_by('-rev').first()
        filename = '%s-v%s.xlsx' % (latestScreen.screen_sn, latestScreen.rev)
        outputFile = os.path.join(filePath, filename)

        # If the name of the Excel file added by the user differs from the name of the next version of the Excel file generated automatically by the system, 
        # then delete the user-added Excel file and use the file generated automatically by the system based on the revision number.
        usrPath = Path(screenDefinition.filePath).resolve()
        sysPath = Path(outputFile).resolve()
        if usrPath != sysPath:
            if os.path.isfile(usrPath):
                os.remove(usrPath)
            while True:
                # If there are multiple Excel files with version numbers higher than that in the database, only the one with the highest version number will be updated to the database, 
                # and the others will be ignored.
                lastRevPath = ikfs.getLastRevisionFile(filePath, screenDefinition.name + ".xlsx")
                if __excelHasModify(latestScreen.rev, str(lastRevPath)):
                    os.remove(lastRevPath)
                else:
                    break
            templateFileFolder = Path(os.path.join(ikfs.getVarFolder(), 'sys', 'views', '-Templates-'))
            templateFile = ikfs.getLastRevisionFile(templateFileFolder, 'template.xlsx')
            if isNullBlank(templateFile):
                logger.error("Template file does not exist in folder [%s]." % templateFileFolder.absolute())
                return Boolean2(False, 'Screen template file is not found. Please check.')
            if os.path.isfile(sysPath):
                os.remove(sysPath)
            c = screenDbWriteToExcel(latestScreen, templateFile, sysPath)
            if not c.value:
                return c

        # ik_screen_file
        screenFileRc = ScreenFile()
        if not isNullBlank(userID):
            screenFileRc.cre_usr_id = userID
            screenFileRc.rmk = 'Reload by Screen Definition'
        else:
            screenFileRc.rmk = 'Create by System'
        screenFileRc.screen = latestScreen
        screenFileRc.file_nm = os.path.basename(outputFile)
        screenFileRc.file_size = os.path.getsize(outputFile)
        screenFileRc.file_path = os.path.dirname(outputFile)
        screenFileRc.file_dt = lastModifyDtExcel
        screenFileRc.file_md5 = _getExcelMD5(outputFile)
        ptrn = IkTransaction()
        ptrn.add(screenFileRc)
        b = ptrn.save()
        if not b.value:
            raise IkValidateException(b.dataStr)
        return Boolean2(True)


def __createExcelWithDatabase(screenSN, userID):
    latestScreen = Screen.objects.filter(screen_sn__iexact=screenSN['screen_sn']).order_by('-rev').first()
    lastScreenFile = ScreenFile.objects.filter(screen=latestScreen).first()
    if isNullBlank(lastScreenFile) or isNullBlank(lastScreenFile.file_path) or "\\" in lastScreenFile.file_path:
        filePath = __getImportScreenFilePath(latestScreen.class_nm)
        filename = '%s-v%s.xlsx' % (latestScreen.screen_sn, latestScreen.rev)
        outputFile = os.path.join(filePath, filename)
        if os.path.isfile(outputFile):
            os.remove(outputFile)
        templateFileFolder = Path(os.path.join(ikfs.getVarFolder(), 'sys', 'views', '-Templates-'))
        templateFile = ikfs.getLastRevisionFile(templateFileFolder, 'template.xlsx')
        if isNullBlank(templateFile):
            logger.error("Template file does not exist in folder [%s]." % templateFileFolder.absolute())
            return Boolean2(False, 'Screen template file is not found. Please check.')
        c = screenDbWriteToExcel(latestScreen, templateFile, outputFile)
        if not c.value:
            return c

        # ik_screen_file
        if isNullBlank(lastScreenFile):
            screenFileRc = ScreenFile()
        else:
            screenFileRc = lastScreenFile
            screenFileRc.ik_set_status_modified()
        if not isNullBlank(userID):
            screenFileRc.cre_usr_id = userID
            screenFileRc.rmk = 'Reload by Screen Definition'
        else:
            screenFileRc.rmk = 'Create by System'
        screenFileRc.screen = latestScreen
        screenFileRc.file_nm = os.path.basename(outputFile)
        screenFileRc.file_size = os.path.getsize(outputFile)
        screenFileRc.file_path = os.path.dirname(outputFile)
        screenFileRc.file_dt = datetime_.now()
        screenFileRc.file_md5 = _getExcelMD5(outputFile)
        ptrn = IkTransaction()
        ptrn.add(screenFileRc)
        b = ptrn.save()
        if not b.value:
            raise IkValidateException(b.dataStr)
        return Boolean2(True)
    else:
        filePath = lastScreenFile.file_path

    path = ikfs.getLastRevisionFile(filePath, latestScreen.screen_sn + ".xlsx")
    if not isNullBlank(path) and not __databaseHasModify(latestScreen):
        # If there is a corresponding Excel file and the database content has not changed compared to the Excel file, then directly iterate to the next screen_sn.
        return Boolean2(True)
    else:
        # Otherwise, create a new Excel file based on the updated database content.
        filename = '%s-v%s.xlsx' % (latestScreen.screen_sn, latestScreen.rev)
        outputFile = os.path.join(filePath, filename)
        # templateFileFolder = ikui.IkUI.getScreenFileTemplateFolder()
        templateFileFolder = Path(os.path.join(ikfs.getVarFolder(), 'sys', 'views', '-Templates-'))
        templateFile = ikfs.getLastRevisionFile(templateFileFolder, 'template.xlsx')
        if isNullBlank(templateFile):
            logger.error("Template file does not exist in folder [%s]." % templateFileFolder.absolute())
            return Boolean2(False, 'Screen template file is not found. Please check.')
        if os.path.isfile(outputFile):
            os.remove(outputFile)
        c = screenDbWriteToExcel(latestScreen, templateFile, outputFile)
        if not c.value:
            return c

        # A new Excel is created, so the Excel file is modified; but the screen definition is not changed, then only the "file_dt" attribute in the ik_screen_file is updated.
        lastScreenFile.file_dt = datetime_.now()
        lastScreenFile.ik_set_status_modified()
        ptrn = IkTransaction()
        ptrn.add(lastScreenFile)
        b = ptrn.save()
        if not b.value:
            raise IkValidateException(b.dataStr)
        return Boolean2(True)


def __toBool(yesNo, default=None) -> bool:
    if isinstance(yesNo, bool):
        return yesNo
    if isNullBlank(yesNo) and default is not None:
        return default
    return yesNo is not None and yesNo.lower() == 'yes'


def __strip(item):
    if isinstance(item, str):
        return item.strip()
    return item


def _getExcelMD5(file):
    if isinstance(file, djangoUploadedfile.UploadedFile):
        excel = file
    elif os.path.isfile(file):
        excel = open(file, 'rb')
    else:
        raise IkValidateException("File is not Found: %s" % (file))

    md5 = hashlib.md5()
    while True:
        data = excel.read(8192) 
        if not data:
            break
        md5.update(data)
    excel.close()
    return md5.hexdigest()


def __getImportScreenFilePath(classNm):
    if isNullBlank(classNm):
        raise IkValidateException("The Class Name of [%s] is None." % (classNm))
    ss = classNm.split('.')
    if len(ss) == 2 and ss[1] != 'views':  # default to app.views.className
        ss.insert(1, 'views')
    if len(ss) > 2:
        subPath = os.path.join('sys', 'views', ss[0])
        return ikfs.getRelativeVarFolder(subPath=subPath)
    else:
        raise IkValidateException("The format of Class Name in [%s] is error." % (classNm))


def __excelHasModify(dbLastRev, filePath) -> bool:
    indexLeft = filePath.find("-v")
    if indexLeft == -1:
        excelRev = 0
    else:
        indexRight = filePath.find(".xlsx")
        excelRev = filePath[indexLeft + 2:indexRight]
    try:
        # if 'rev' in dfn.keys():
        #     if isNullBlank(dfn['rev']) or int(dfn['rev']) != int(excelRev):
        #         logger.error("The version number on the filename of the excel file does not match the internal version number of the file, File name: " + screenDefinition.name)
        #         return False
        if int(excelRev) > dbLastRev:
            return True
    except Exception as e:
        logger.error(e, exc_info=True)
        raise IkValidateException("Get excel file revision error, File path: " + filePath)
    return False


def __databaseHasModify(ScreenRc: Screen) -> bool:
    filePath = __getImportScreenFilePath(ScreenRc.class_nm)
    lastFilePath = ikfs.getLastRevisionFile(filePath, ScreenRc.screen_sn + '.xlsx')
    lastFilePath = str(lastFilePath)

    indexLeft = lastFilePath.find("-v")
    if indexLeft == -1:
        lastRev = 0
    else:
        indexRight = lastFilePath.find(".xlsx")
        lastRev = lastFilePath[indexLeft + 2:indexRight]
    try:
        if int(lastRev) < ScreenRc.rev:
            return True
    except Exception as e:
        logger.error(e, exc_info=True)
        raise IkValidateException("Get excel file revision error, File path: " + lastFilePath)
    return False


def __getAutoRefresh(autoRefresh):
    data = [None, None]
    if not isNullBlank(autoRefresh):
        autoRefresh = autoRefresh.split(";")
        if len(autoRefresh) > 0:
            data[0] = autoRefresh[0]
        if len(autoRefresh) == 2:
            data[1] = autoRefresh[1]
    return data


def __updateScreenDatabase(dfn, userID):
    latestScreen = Screen.objects.filter(screen_sn__iexact=__strip(dfn['viewID'])).order_by('-rev').first()
    rev = 0 if isNullBlank(latestScreen) else latestScreen.rev + 1
    createUsrID = -1 if isNullBlank(userID) else userID

    screenRc = Screen()
    screenRc.assignPrimaryID()
    screenRc.cre_dt = datetime_.now()
    screenRc.screen_sn = __strip(dfn['viewID'])
    screenRc.screen_title = __strip(dfn['viewTitle'])
    screenRc.screen_dsc = __strip(dfn['viewDesc'])
    screenRc.layout_type = __strip(dfn['layoutType'])
    screenRc.layout_params = __strip(dfn['layoutParams'])
    screenRc.class_nm = __strip(dfn['viewName'])
    screenRc.api_url = __strip(dfn['apiUrl'])
    screenRc.editable = __toBool(__strip(dfn['editable']), default=True)
    screenRc.api_version = dfn['viewAPIRev']
    screenRc.auto_refresh_interval = __getAutoRefresh(dfn['autoRefresh'])[0]
    screenRc.auto_refresh_action = __getAutoRefresh(dfn['autoRefresh'])[1]
    screenRc.rev = rev
    screenRc.rmk = dfn['rmk']

    # ik_screen_recordset
    screenRecordsetRcs = []
    if 'recordsetTable' in dfn and len(dfn['recordsetTable']) > 0:
        for i in dfn['recordsetTable']:
            i = [__strip(item) for item in i]
            screenRecordsetRc = ScreenRecordset()
            screenRecordsetRc.cre_dt = datetime_.now()
            screenRecordsetRc.screen = screenRc
            screenRecordsetRc.recordset_nm = i[0]
            screenRecordsetRc.sql_fields = '*' if isNullBlank(i[1]) else i[1]
            screenRecordsetRc.sql_models = i[2]
            screenRecordsetRc.sql_where = i[3]
            screenRecordsetRc.sql_order = i[4]
            screenRecordsetRc.sql_limit = i[5]
            screenRecordsetRc.rmk = i[6]
            screenRecordsetRcs.append(screenRecordsetRc)

    # ik_screen_field_group
    screenFieldGroupRcs = []
    if 'fieldGroupTable' in dfn and len(dfn['fieldGroupTable']) > 0:
        seq = 0
        for j in dfn['fieldGroupTable']:
            j = [__strip(item) for item in j]
            screenFieldGroupRc = ScreenFieldGroup()
            screenFieldGroupRc.cre_dt = datetime_.now()
            screenFieldGroupRc.screen = screenRc
            screenFieldGroupRc.fg_nm = j[0]
            screenFieldGroupRc.fg_type = ScreenFgType.objects.filter(type_nm__iexact=j[1]).first()
            screenFieldGroupRc.seq = seq
            screenFieldGroupRc.caption = j[2]
            screenFieldGroupRc.recordset = next((item for item in screenRecordsetRcs if item.recordset_nm.lower() == str(j[3]).lower()), None)
            screenFieldGroupRc.deletable = __toBool(j[4])
            screenFieldGroupRc.editable = __toBool(j[5])
            screenFieldGroupRc.insertable = __toBool(j[6])
            screenFieldGroupRc.highlight_row = __toBool(j[7])
            screenFieldGroupRc.selection_mode = ikui.getScreenFieldGroupSelectionMode(j[8])
            screenFieldGroupRc.cols = j[9]
            screenFieldGroupRc.sort_new_rows = __toBool(j[10])
            screenFieldGroupRc.data_page_type = ikui.getScreenFieldGroupDataPageType(j[11])
            screenFieldGroupRc.data_page_size = j[12]
            screenFieldGroupRc.outer_layout_params = j[13]
            screenFieldGroupRc.inner_layout_type = j[14]
            screenFieldGroupRc.inner_layout_params = j[15]
            screenFieldGroupRc.html = j[16]
            screenFieldGroupRc.rmk = j[17]
            screenFieldGroupRcs.append(screenFieldGroupRc)
            seq += 1

    # ik_screen_field
    screenFieldRcs = []
    if 'fieldTable' in dfn and len(dfn['fieldTable']) > 0:
        seq = 0
        fgNm = None
        for k in dfn['fieldTable']:
            k = [__strip(item) for item in k]
            if not isNullBlank(k[0]):
                fgNm = k[0]
                seq = 0
            screenFieldRc = ScreenField()
            screenFieldRc.cre_dt = datetime_.now()
            screenFieldRc.screen = screenRc
            screenFieldRc.field_group = next((item for item in screenFieldGroupRcs if item.fg_nm.lower() == str(fgNm).lower()), None)
            screenFieldRc.field_nm = k[1]
            screenFieldRc.seq = seq
            screenFieldRc.caption = k[2]
            screenFieldRc.tooltip = k[3]
            screenFieldRc.visible = not __toBool(k[4])
            screenFieldRc.editable = __toBool(k[5], default=True)
            screenFieldRc.widget = ScreenFieldWidget.objects.filter(widget_nm__iexact=k[6]).first()
            screenFieldRc.widget_parameters = k[7]
            screenFieldRc.db_field = k[8]
            screenFieldRc.md_format = k[9]
            screenFieldRc.md_validation = k[10]
            screenFieldRc.event_handler = k[11]
            screenFieldRc.styles = k[12]
            screenFieldRc.rmk = k[13]
            screenFieldRcs.append(screenFieldRc)
            seq += 1

    # ik_screen_dfn
    screenDfnRcs = []
    if 'subScreenTable' in dfn and len(dfn['subScreenTable']) > 0:
        for l in dfn['subScreenTable']:
            l = [__strip(item) for item in l]
            screenDfnRc = ScreenDfn()
            screenDfnRc.cre_dt = datetime_.now()
            screenDfnRc.screen = screenRc
            screenDfnRc.sub_screen_nm = l[0]
            screenDfnRc.field_group_nms = l[1]
            screenDfnRc.rmk = l[2]
            screenDfnRcs.append(screenDfnRc)

    # ik_screen_fg_link
    screenFgLinkRcs = []
    if 'fieldGroupLinkTable' in dfn and len(dfn['fieldGroupLinkTable']) > 0:
        for l in dfn['fieldGroupLinkTable']:
            l = [__strip(item) for item in l]
            screenFgLinkRc = ScreenFgLink()
            screenFgLinkRc.cre_dt = datetime_.now()
            screenFgLinkRc.screen = screenRc
            screenFgLinkRc.field_group = next((item for item in screenFieldGroupRcs if item.fg_nm.lower() == str(l[0]).lower()), None)
            screenFgLinkRc.local_key = l[1]
            screenFgLinkRc.parent_field_group = next((item for item in screenFieldGroupRcs if item.fg_nm.lower() == str(l[2]).lower()), None)
            screenFgLinkRc.parent_key = l[3]
            screenFgLinkRc.rmk = l[4]
            screenFgLinkRcs.append(screenFgLinkRc)

    # ik_screen_fg_header_footer
    screenFgHeaderFooterRcs = []
    if 'headerFooterTable' in dfn and len(dfn['headerFooterTable']) > 0:
        fgNm = None
        seq = 0
        for m in dfn['headerFooterTable']:
            m = [__strip(item) for item in m]
            if not isNullBlank(m[0]):
                fgNm = m[0]
                seq = 0
            fieldGroup = next((item for item in screenFieldGroupRcs if item.fg_nm.lower() == str(fgNm).lower()), None)
            fieldRcs = sorted([item for item in screenFieldRcs if item.field_group == fieldGroup], key=lambda x: x.seq)
            field = fieldRcs[seq] if len(fieldRcs) > seq else None
            screenFgHeaderFooterRc = ScreenFgHeaderFooter()
            screenFgHeaderFooterRc.cre_dt = datetime_.now()
            screenFgHeaderFooterRc.screen = screenRc
            screenFgHeaderFooterRc.field_group = fieldGroup
            screenFgHeaderFooterRc.field = field
            screenFgHeaderFooterRc.header_level1 = m[2]
            screenFgHeaderFooterRc.header_level2 = m[3]
            screenFgHeaderFooterRc.header_level3 = m[4]
            screenFgHeaderFooterRc.footer = m[5]
            screenFgHeaderFooterRc.rmk = m[6]
            screenFgHeaderFooterRcs.append(screenFgHeaderFooterRc)
            seq += 1

    ptrn = IkTransaction(userID=createUsrID)
    ptrn.add(screenRc)
    ptrn.add(screenRecordsetRcs)
    ptrn.add(screenFieldGroupRcs)
    ptrn.add(screenFieldRcs)
    ptrn.add(screenDfnRcs)
    ptrn.add(screenFgLinkRcs)
    ptrn.add(screenFgHeaderFooterRcs)
    b = ptrn.save()
    if not b.value:
        raise IkValidateException(b.dataStr)
