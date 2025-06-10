import hashlib
import os
import threading
import re
from datetime import datetime as datetime_
from pathlib import Path

import django.core.files.uploadedfile as djangoUploadedfile
from django.db import connection

import core.core.fs as ikfs
import core.utils.csv as csv
import core.utils.modelUtils as ikModelUtils
import core.utils.spreadsheet as ikSpreadsheet
from iktools import getAppNames
from core.log.logger import logger
from core.core.exception import IkException, IkValidateException
from core.core.lang import Boolean2
from core.db.transaction import IkTransaction
from core.models import *
from core.utils.langUtils import isNotNullBlank, isNullBlank
from iktools import IkConfig
from . import ui as ikui


def syncScreenDefinitions(userID: int = None):
    if IkConfig.getSystem('supportSpreadsheetScreenDefinition', 'true').lower() == 'false':
        return

    # excel to database
    template_file = ikfs.getLastRevisionFile(ikui.getScreenFileTemplateFolder(), 'template.xlsx')
    template_rev = _extract_version_from_path(template_file)
    
    def get_app_screen_files(fp, app_name) -> dict:
        screen_files = {}
        if not ikui.acceptScreenFolder(fp.name):
            logger.debug('syncScreenDefinitions ignore folder: %s' % fp)
            return screen_files# ignore folder starts with "-"

        excelRevs = {}
        for f2 in os.listdir(fp):
            if not ikui.acceptScreenFile(f2):
                logger.debug('syncScreenDefinitions ignore file: %s/%s' % (fp, fp.name))
                continue

            path = Path(os.path.join(fp, f2))
            spData = ikSpreadsheet.SpreadsheetParser(path).data
            screenSN = __strip(spData['viewID'])
            if 'templateVersion' not in spData.keys():
                logger.error("[%s] spreadsheet format is incorrect: missing field [templateVersion]." % path) 
                continue
            if template_rev != spData['templateVersion']:
                logger.error("Screen [%s.%s] excel template file version [v%s] is not the latest. The latest version is [v%s]." % (
                    app_name, screenSN, spData['templateVersion'], template_rev))
                continue
            if screenSN not in excelRevs:
                latestScreen = Screen.objects.filter(screen_sn__iexact=screenSN).order_by('-rev').first()
                dbRev = latestScreen.spreadsheet_rev if isNotNullBlank(latestScreen) and isNotNullBlank(latestScreen.spreadsheet_rev) else -1
                excelRevs[screenSN] = dbRev
            if screenSN not in screen_files:
                screen_files[screenSN] = []

            try:
                if isNullBlank(spData['rev']):
                    spData['rev'] = 0
                    excelRev = 0
                else:
                    excelRev = int(spData['rev'])
            except Exception:
                logger.error('Excel "Reversion" field must be an integer. Invalid file: %s' % path)
            if isNotNullBlank(excelRev) and excelRev > excelRevs[screenSN]:
                screenDefinition = ikui.ScreenDefinition(name=screenSN, fullName=app_name + '.' + screenSN, filePath=path, definition=spData)
                screen_files[screenSN].append([path, excelRev, screenDefinition])
        return screen_files
    
    def process_app_screen_files(app_name):
        screen_file_folder = Path(os.path.join(app_name, ikui.SCREEN_RESOURCE_FOLDER_PATH))
        if screen_file_folder.is_dir():
            screen_files = get_app_screen_files(screen_file_folder, app_name)
            for screenSN, screenDefinitions in screen_files.items():
                if len(screenDefinitions) > 0:
                    screenDefinitions = sorted(screenDefinitions, key=lambda x: x[1])
                    for file_path, file_rev, screenDefinition in screenDefinitions:
                        b = _updateDatabaseWithExcelFiles(screenDefinition, userID)
                        if not b.value:
                            logger.error("Process screen [%s], Path=%s, Rev=%s, failed: %s" % (screenSN, str(file_path), file_rev, b.dataStr))

    app_names = getAppNames()
    for app_name in app_names:
        process_app_screen_files(app_name)

    # database to excel: Screen Dfn
    screenSNs = Screen.objects.values('screen_sn').distinct().order_by('screen_sn')
    for screenSN in screenSNs:
        b1 = __createExcelWithDatabase(screenSN, userID)
        if not b1.value:
            return b1

    # database to excel: Screen Dfn CSV
    if not IkConfig.get("production", False):
        thread = threading.Thread(target=createCSVFileWithDatabase)
        thread.start()
    return Boolean2(True, "Reloaded")


def createCSVFileWithDatabase(screenSN: str = None):
    try:
        if isNotNullBlank(screenSN):
            screenSNs = [{'screen_sn': screenSN}]
        else:
            screenSNs = Screen.objects.values('screen_sn').distinct().order_by('screen_sn')
            logger.info('Export all screen definition to csv file start ...')
        for screenSNDict in screenSNs:
            latestScreen = Screen.objects.filter(screen_sn__iexact=screenSNDict['screen_sn']).order_by('-rev').first()

            if isNotNullBlank(latestScreen):
                app_nms = getAppNames()
                if latestScreen.app_nm not in app_nms:
                    continue

                filename = '%s.csv' % latestScreen.screen_sn
                outputFile = Path(os.path.join(latestScreen.app_nm, ikui.SCREEN_RESOURCE_FOLDER_PATH, 'csv', filename))

                if isNotNullBlank(screenSN):
                    logger.info('Export screen definition [%s] to csv file [%s] start ...' % (screenSN, outputFile))
                if os.path.isfile(outputFile):
                    try:
                        os.remove(outputFile)
                    except PermissionError:
                        raise IkException("PermissionError: Please check File [%s] is already open. If it is open, please close it and try again." % filename)

                try:
                    expData = __getExpDataFromDB(latestScreen, isCSV=True)
                except Exception as exc:
                    logger.error('Get screen=%s (Rev %s) data from database failed: %s' % (latestScreen.screen_sn, latestScreen.rev, str(exc)))
                    logger.error(exc, exc_info=True)
                    continue

                # change \n to \r\n for compate the files using git tools.
                # ( The new line flag in a excel cell is \r\n.)
                for key, value in expData.items():
                    if value is not None:
                        if type(value) == list or type(value) == tuple:
                            for row in value:
                                for i in range(len(row)):
                                    if type(row[i]) == str:
                                        row[i] = row[i].replace('\r\n', '\n').replace('\n', '\r\n')
                        elif type(value) == str:
                            value = value.replace('\r\n', '\n').replace('\n', '\r\n')
                        expData[key] = value

                csv.Write2CsvFile(outputFile, expData, comments="This is a comment line.", sort_keys=True)

        if isNotNullBlank(screenSN):
            logger.info('Export screen definition [%s] to csv file [%s] success.' % (screenSN, outputFile))
        else:
            logger.info('Export all screen definition to csv file success.')
        return Boolean2(True, 'Create CSV File Success.')
    except Exception as e:
        logger.error(e, exc_info=True)
        return Boolean2(False, 'Create CSV File error! Screen ID: [%s]' % screenSN)


def updateDatabaseWithImportExcel(ImportScreen: djangoUploadedfile.UploadedFile, userID):
    dfn = ikSpreadsheet.SpreadsheetParser(ImportScreen).data
    latestScreen = Screen.objects.filter(screen_sn__iexact=__strip(dfn['viewID'])).order_by('-rev').first()
    # if isNotNullBlank(latestScreen) and not __excelHasModify(latestScreen, dfn):
    #     return Boolean2(True, 'No changes detected. Nothing to import.')

    __updateScreenDatabase(dfn, userID)

    # The imported Excel file's content is updated to the database, then the Excel file is saved at the corresponding location in 'var/views/xxx'.
    latestScreen = Screen.objects.filter(screen_sn__iexact=__strip(dfn['viewID'])).order_by('-rev').first()
    if isNullBlank(latestScreen):
        return Boolean2(False, "Database save failed.")
    b = screenDbWriteToExcel(latestScreen, 'Import by Screen Definition')
    if not b.value:
        raise IkValidateException(b.dataStr)
    return Boolean2(True, "Imported")


# Output the definition of the target page (screenRc) as an Excel file at the specified location (outputFile).
def screenDbWriteToExcel(screenRc: Screen, fileRmk: str = None) -> Boolean2:
    if isNullBlank(screenRc):
        return Boolean2(False, 'Screen does not exist. Please check.')

    filename = '%s.xlsx' % screenRc.screen_sn
    outputFile = Path(os.path.join(screenRc.app_nm, ikui.SCREEN_RESOURCE_FOLDER_PATH, filename))

    # ik_screen_file
    if isNotNullBlank(fileRmk):
        screenFileRc = ScreenFile.objects.filter(screen=screenRc).order_by('-file_dt').first()
        if isNotNullBlank(screenFileRc) and 'Delete last Screen' in fileRmk:
            screenFileRc.rmk = fileRmk
            screenFileRc.ik_set_status_modified()
        else:
            screenFileRc = ScreenFile()
            screenFileRc.screen = screenRc
            screenFileRc.file_nm = filename
            screenFileRc.file_size = 0
            screenFileRc.file_path = screenRc.app_nm
            screenFileRc.file_dt = datetime_.now()
            screenFileRc.file_md5 = ''
            screenFileRc.rmk = fileRmk + ' (Export excel failed.)'
        ptrn = IkTransaction()
        ptrn.add(screenFileRc)
        c = ptrn.save()
        if not c.value:
            return c

        d = createCSVFileWithDatabase(screenSN=screenRc.screen_sn)
        if not d.value:
            return d

    templateFileFolder = ikui.getScreenFileTemplateFolder()
    template_file = ikfs.getLastRevisionFile(templateFileFolder, 'template.xlsx')
    if isNullBlank(template_file):
        return Boolean2(False, 'Screen template file not found. Please check.')

    logger.info('Export screen definition [%s] to excel file [%s] start ...' % (screenRc.screen_sn, outputFile))
    if os.path.isfile(outputFile):
        try:
            os.remove(outputFile)
        except PermissionError:
            raise IkException("PermissionError: Please check File [%s] is already open. If it is open, please close it and try again." % filename)

    # write to file if success
    def spreadsheetWriter(expData, template_file, outputFile):
        try:
            sw = ikSpreadsheet.SpreadsheetWriter(parameters=expData, templateFile=template_file, outputFile=outputFile)
            b = sw.write()
            if not b.value:
                raise b.dataStr
            logger.info('Export screen definition [%s] to excel file [%s] success' % (screenRc.screen_sn, outputFile))

            screenFileRc = ScreenFile.objects.filter(screen=screenRc).order_by('-file_dt').first()
            screenFileRc.file_size = os.path.getsize(outputFile)
            screenFileRc.file_md5 = _getExcelMD5(outputFile)
            screenFileRc.rmk = fileRmk
            screenFileRc.ik_set_status_modified()
            ptrn = IkTransaction()
            ptrn.add(screenFileRc)
            c = ptrn.save()
            if not c.value:
                raise c.dataStr
        finally:
            connection.close()

    expData = __getExpDataFromDB(screenRc)
    thread = threading.Thread(target=spreadsheetWriter, args=(expData, template_file, outputFile))
    thread.start()
    thread.join()

    return Boolean2(True, outputFile)


# get screen definition from database
def __getExpDataFromDB(screenRc: Screen, isCSV: bool = None):
    template_file = ikfs.getLastRevisionFile(ikui.getScreenFileTemplateFolder(), 'template.xlsx')
    template_rev = _extract_version_from_path(template_file)

    rsRcs = ScreenRecordset.objects.filter(screen=screenRc).order_by('seq', 'id')
    fgRcs = ScreenFieldGroup.objects.filter(screen=screenRc).order_by('seq', 'id')
    for rc in fgRcs:
        rc.deletable = 'yes' if rc.deletable == True else None
        rc.editable = 'yes' if rc.editable == True else None
        rc.insertable = 'yes' if rc.insertable == True else None
        rc.highlight_row = 'yes' if rc.highlight_row == True else None
        rc.selection_mode = rc.selection_mode if rc.selection_mode != 'none' else None

    fgFieldRcs = ScreenField.objects.filter(screen=screenRc).order_by('field_group', 'seq', 'id')
    fgNm = ''
    for rc in fgFieldRcs:
        rc.visible = None if rc.visible == True else 'yes'  # column title: hide
        rc.editable = None if rc.editable == True else 'no'
        rc.db_unique = 'yes' if rc.db_unique == True else 'no' if rc.db_unique == False else None
        rc.db_required = 'yes' if rc.db_required == True else 'no' if rc.db_required == False else None
        if isCSV:
            if isNotNullBlank(rc.widget_parameters) and "\r\n" in rc.widget_parameters:
                rc.widget_parameters = rc.widget_parameters.replace("\r\n", "\n")
            continue
        if not rc.field_group:
            continue
        elif fgNm == rc.field_group.fg_nm:
            rc.field_group.fg_nm = None
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
            rc.field_group.fg_nm = None
        else:
            fgNm = rc.field_group.fg_nm

    # prepare spreadsheet data
    # screen headers
    expData = {}  # export data
    expData['templateVersion'] = template_rev
    expData['viewID'] = screenRc.screen_sn
    expData['viewTitle'] = screenRc.screen_title
    expData['viewDesc'] = screenRc.screen_dsc
    expData['layoutType'] = screenRc.layout_type
    expData['layoutParams'] = screenRc.layout_params
    expData['appName'] = screenRc.app_nm
    expData['viewName'] = screenRc.class_nm
    expData['apiUrl'] = screenRc.api_url
    expData['editable'] = 'yes' if screenRc.editable == True else 'no'
    # expData['autoRefresh'] = ikui.IkUI.getAutoRefreshInfo(screenRc.auto_refresh_interval, screenRc.auto_refresh_action)
    expData['autoRefresh'] = ikui.__ScreenManager.getAutoRefreshInfo(None, interval=screenRc.auto_refresh_interval, action=screenRc.auto_refresh_action)
    if not isCSV:
        expData['rev'] = screenRc.spreadsheet_rev if isNotNullBlank(screenRc.spreadsheet_rev) else screenRc.rev
    expData['rmk'] = screenRc.rmk
    # screen tables
    expData['recordsetTable'] = ikModelUtils.redcordsets2List(rsRcs, ['recordset_nm', 'sql_fields', 'sql_models', 'sql_where', 'sql_order', 'sql_limit', 'rmk'])
    expData['fieldGroupTable'] = ikModelUtils.redcordsets2List(fgRcs, [
        'fg_nm', 'fg_type.type_nm', 'caption', 'recordset.recordset_nm', 'deletable', 'editable', 'insertable', 'highlight_row', 'selection_mode', 'cols', 'data_page_type',
        'data_page_size', 'outer_layout_params', 'inner_layout_type', 'inner_layout_params', 'html', 'additional_props', 'rmk'
    ])
    expData['fieldTable'] = ikModelUtils.redcordsets2List(fgFieldRcs, [
        'field_group.fg_nm', 'field_nm', 'caption', 'tooltip', 'visible', 'editable', 'db_unique', 'db_required', 'widget.widget_nm', 'widget_parameters', 'db_field',
        'event_handler', 'styles', 'rmk'
    ])
    expData['subScreenTable'] = ikModelUtils.redcordsets2List(dfnRcs, ['sub_screen_nm', 'field_group_nms', 'rmk'])
    expData['fieldGroupLinkTable'] = ikModelUtils.redcordsets2List(fgLinkRcs, ['field_group.fg_nm', 'local_key', 'parent_field_group.fg_nm', 'parent_key', 'rmk'])
    expData['headerFooterTable'] = ikModelUtils.redcordsets2List(hfRcs, ['field_group.fg_nm', 'field.field_nm', 'header_level1', 'header_level2', 'header_level3', 'footer', 'rmk'])
    return expData


def _updateDatabaseWithExcelFiles(screenDefinition, userID) -> Boolean2:
    if screenDefinition is None:
        return Boolean2(False, 'screenDefinition is None')
    elif screenDefinition.definition is None:
        # for bugfix checking
        logger.error('getScreenDefinition(%s).data=None' % screenDefinition.name)
        return Boolean2(False, 'getScreenDefinition(%s).data=None' % screenDefinition.name)
    dfn = screenDefinition.definition

    # ik_screen
    latestScreen = Screen.objects.filter(screen_sn__iexact=__strip(dfn['viewID'])).order_by('-rev').first()
    if isNotNullBlank(latestScreen) and not __excelHasModify(latestScreen, dfn):
        # If the screen data already exists in the database and there are no changes compared to the Excel content, then exit the update method directly.
        logger.info('Screen definition [%s] no changed. File path is [%s].' % (screenDefinition.fullName, screenDefinition.filePath))
        return Boolean2(True)
    else:
        processResult = Boolean2(False)
        try:
            lastModifyDtExcel = os.path.getmtime(screenDefinition.filePath)
            lastModifyDtExcel = datetime_.fromtimestamp(lastModifyDtExcel)

            logger.info('Import screen definition [%s] from file [%s] ...' % (screenDefinition.fullName, screenDefinition.filePath))
            # Otherwise, update all the corresponding database tables for that page.
            __updateScreenDatabase(dfn, userID)

            if isNotNullBlank(latestScreen) and latestScreen.app_nm != __strip(dfn['appName']):
                latestScreenFileRc = ScreenFile.objects.filter(screen=latestScreen).first()
                if isNotNullBlank(latestScreenFileRc):
                    _deleteExcelAndCSV(latestScreenFileRc)

            latestScreen = Screen.objects.filter(screen_sn__iexact=__strip(dfn['viewID'])).order_by('-rev').first()
            if isNotNullBlank(userID):
                rmk = 'Reload by Screen Definition'
            else:
                rmk = 'Import from spreadsheet.'
            b = screenDbWriteToExcel(latestScreen, rmk)
            if not b.value:
                logger.error('Import screen definition [%s] from file [%s], create excel failed: [%s]' % (screenDefinition.fullName, screenDefinition.filePath, b.dataStr))
                processResult = Boolean2(False, b.data)
                return b
            processResult = Boolean2(True, 'Success')
            return processResult
        except Exception as e:
            logger.error('Save screen error! Excel file path: [%s] ' % (screenDefinition.filePath))
            return Boolean2(False, e)
        finally:
            if processResult.value:
                logger.info('Import screen definition [%s] from file [%s] success. Last Revision is %s.' % (screenDefinition.fullName, screenDefinition.filePath, latestScreen.rev))
            else:
                logger.error('Import screen definition [%s] from file [%s] failed: %s' % (screenDefinition.fullName, screenDefinition.filePath, processResult.dataStr))


def __createExcelWithDatabase(screenSN, userID):
    latestScreen = Screen.objects.filter(screen_sn__iexact=screenSN['screen_sn']).order_by('-rev').first()
    lastScreenFile = ScreenFile.objects.filter(screen=latestScreen).order_by('-file_dt').first()
    if isNotNullBlank(userID):
        fileRmk = 'Reload by Screen Definition'
    else:
        fileRmk = 'Import from spreadsheet'

    if isNullBlank(lastScreenFile) or isNullBlank(lastScreenFile.file_path) or "var" in lastScreenFile.file_path:
        b = screenDbWriteToExcel(latestScreen, fileRmk)
        if not b.value:
            return b
        return Boolean2(True)

    if not __databaseHasModify(lastScreenFile):
        # If there is a corresponding Excel file and the database content has not changed compared to the Excel file, then directly iterate to the next screen_sn.
        return Boolean2(True)
    else:
        # Otherwise, create a new Excel file based on the updated database content.
        d = screenDbWriteToExcel(latestScreen, fileRmk)
        if not d.value:
            return d
        return Boolean2(True)


def __toBool(yesNo, default=None) -> bool:
    if isinstance(yesNo, bool):
        return yesNo
    if isNullBlank(yesNo) and default is not None:
        if default == "":
            return None
        return default
    return yesNo is not None and yesNo.lower() == 'yes'


def _extract_version_from_path(file_path):
    file_path_str = str(file_path)
    match = re.search(r'v(\d+)', file_path_str)
    if match:
        return int(match.group(1))
    return None


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
        raise IkValidateException("File not Found: %s" % (file))

    md5 = hashlib.md5()
    while True:
        data = excel.read(8192)
        if not data:
            break
        md5.update(data)
    excel.close()
    return md5.hexdigest()


def _deleteExcelAndCSV(screenFileRc: ScreenFile):
    if isNullBlank(screenFileRc):
        return
    fp = os.path.join(screenFileRc.file_path, ikui.SCREEN_RESOURCE_FOLDER_PATH, screenFileRc.file_nm)
    if os.path.isfile(fp):
        try:
            ikfs.deleteEmptyFolderAndParentFolder(fp)
        except PermissionError:
            raise IkException("PermissionError: Please check File [%s] is already open. If it is open, please close it and try again." % fp)

    fp2 = os.path.join(screenFileRc.file_path, ikui.SCREEN_RESOURCE_FOLDER_PATH, 'csv', screenFileRc.file_nm.replace(".xlsx", ".csv"))
    if os.path.isfile(fp2):
        try:
            ikfs.deleteEmptyFolderAndParentFolder(fp2)
        except PermissionError:
            raise IkException("PermissionError: Please check File [%s] is already open. If it is open, please close it and try again." % fp2)


def __excelHasModify(lastScreen: Screen, newScreenDfn) -> bool:
    if isNullBlank(lastScreen.spreadsheet_rev):
        return True
    if lastScreen.spreadsheet_rev >= int(newScreenDfn['rev']):
        return False
    lastScreenDfn = __getExpDataFromDB(lastScreen)
    lastScreen.rev = newScreenDfn['rev']
    return not (lastScreenDfn == newScreenDfn)


def __databaseHasModify(screenFileRc: ScreenFile) -> bool:
    if isNullBlank(screenFileRc):
        return True
    app_nms = getAppNames()
    filePath = Path(os.path.join(screenFileRc.file_path, ikui.SCREEN_RESOURCE_FOLDER_PATH, screenFileRc.file_nm))
    if os.path.isfile(filePath) or screenFileRc.screen.app_nm not in app_nms:
        return False
    return True


def __getAutoRefresh(autoRefresh):
    data = [None, None]
    if isNotNullBlank(autoRefresh):
        autoRefreshPrp = []
        if ";" in autoRefresh:
            autoRefreshPrp = autoRefresh.split(";")
        elif "," in autoRefresh:
            autoRefreshPrp = autoRefresh.split(",")
        if len(autoRefreshPrp) > 0:
            data[0] = int(autoRefreshPrp[0].strip())
            if len(autoRefreshPrp) > 1:
                data[1] = autoRefreshPrp[1].strip()
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
    screenRc.app_nm = __strip(dfn['appName'])
    screenRc.class_nm = __strip(dfn['viewName'])
    screenRc.api_url = __strip(dfn['apiUrl'])
    screenRc.editable = __toBool(__strip(dfn['editable']), default=True)
    screenRc.template_version = dfn['templateVersion']
    screenRc.auto_refresh_interval = __getAutoRefresh(dfn['autoRefresh'])[0]
    screenRc.auto_refresh_action = __getAutoRefresh(dfn['autoRefresh'])[1]
    screenRc.spreadsheet_rev = dfn['rev']
    screenRc.rev = rev
    screenRc.rmk = dfn['rmk']

    # ik_screen_recordset
    screenRecordsetRcs = []
    if 'recordsetTable' in dfn and len(dfn['recordsetTable']) > 0:
        seq = 0
        for i in dfn['recordsetTable']:
            i = [__strip(item) for item in i]
            screenRecordsetRc = ScreenRecordset()
            screenRecordsetRc.cre_dt = datetime_.now()
            screenRecordsetRc.screen = screenRc
            screenRecordsetRc.recordset_nm = i[0]
            screenRecordsetRc.seq = seq
            screenRecordsetRc.sql_fields = '*' if isNullBlank(i[1]) else i[1]
            screenRecordsetRc.sql_models = i[2]
            screenRecordsetRc.sql_where = i[3]
            screenRecordsetRc.sql_order = i[4]
            screenRecordsetRc.sql_limit = i[5]
            screenRecordsetRc.rmk = i[6]
            screenRecordsetRcs.append(screenRecordsetRc)
            seq += 1

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
            # screenFieldGroupRc.sort_new_rows = __toBool(j[10])
            screenFieldGroupRc.data_page_type = ikui.getScreenFieldGroupDataPageType(j[10])
            screenFieldGroupRc.data_page_size = j[11]
            screenFieldGroupRc.outer_layout_params = j[12]
            screenFieldGroupRc.inner_layout_type = j[13]
            screenFieldGroupRc.inner_layout_params = j[14]
            screenFieldGroupRc.html = j[15]
            screenFieldGroupRc.additional_props = j[16]
            screenFieldGroupRc.rmk = j[17]
            screenFieldGroupRcs.append(screenFieldGroupRc)
            seq += 1

    # ik_screen_field
    screenFieldRcs = []
    if 'fieldTable' in dfn and len(dfn['fieldTable']) > 0:
        seq = 0
        fgNm = None
        fieldNmList = []
        for k in dfn['fieldTable']:
            k = [__strip(item) for item in k]
            if isNotNullBlank(k[0]):
                fgNm = k[0]
                seq = 0
            if isNotNullBlank(k[1]):
                fieldNm = '%s.%s' % (fgNm, k[1])
                if fieldNm in fieldNmList:
                    logger.error('Field name in the same field group must be unique.')
                    raise IkValidateException('Field name in the same field group must be unique.')
                fieldNmList.append(fieldNm)
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
            screenFieldRc.db_unique = __toBool(k[6], default='')
            screenFieldRc.db_required = __toBool(k[7], default='')
            screenFieldRc.widget = ScreenFieldWidget.objects.filter(widget_nm__iexact=k[8]).first()
            screenFieldRc.widget_parameters = k[9]
            screenFieldRc.db_field = k[10]
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
        fieldGroup = None
        seq = 0
        for m in dfn['headerFooterTable']:
            m = [__strip(item) for item in m]
            if isNotNullBlank(m[0]):
                seq = 0
                fieldGroup = next((item for item in screenFieldGroupRcs if item.fg_nm.lower() == str(m[0]).lower()), None)
                if isNullBlank(fieldGroup):
                    logger.error('Header Footer Table error. Field group [%s] is not found.' % m[0])
                    raise IkValidateException('Header Footer Table error. Field group [%s] is not found.' % m[0])
            field = next((item for item in screenFieldRcs if item.field_group == fieldGroup and item.field_nm == m[1]), None)
            if isNullBlank(field):
                logger.error('Header Footer Table error. Field Group [%s] Field [%s] is not found.' % (fieldGroup.fg_nm, m[1]))
                raise IkValidateException('Header Footer Table error. Field Group [%s] Field [%s] is not found.' % (fieldGroup.fg_nm, m[1]))
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
