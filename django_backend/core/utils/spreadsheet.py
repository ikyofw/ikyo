import copy
import logging
import math
import os
import pathlib
import string
import traceback

import django.core.files.uploadedfile as djangoUploadedfile
import pandas as pd
from core.core.exception import IkValidateException
from core.core.lang import Boolean2
from core.utils.langUtils import isNullBlank
from openpyxl import load_workbook

logger = logging.getLogger('backend')


def columnName2Index(colname):
    colname = colname.upper()
    if type(colname) is not str:
        return colname
    col = 0
    power = 1
    for i in range(len(colname) - 1, -1, -1):
        ch = colname[i]
        col += (ord(ch) - ord('A') + 1) * power
        power *= 26
    return col


def columnIndex2Name(i) -> str:
    nm = ''
    ci = i - 1
    index = ci // 26
    if index > 0:
        nm += columnIndex2Name(index)
    nm += string.ascii_uppercase[ci % 26]
    return nm


def copyCellStyle(fromCell, toCell):
    fromCell.fill = copy.copy(toCell.fill)
    fromCell.font = copy.copy(toCell.font)
    fromCell.number_format = copy.copy(toCell.number_format)
    fromCell.border = copy.copy(toCell.border)
    fromCell._style = copy.copy(toCell._style)
    fromCell.alignment = copy.copy(toCell.alignment)
    fromCell.protection = copy.copy(toCell.protection)


DATA_START_COLUMN_INDEX = 3  # column index starts from 1. "3" = "C"

'''
    Screen definition.
    Please reference to View-v14.xlsx
    Usage example:
        file=r'var\ikyo\screen\office.xlsx'                  
        sp = SpreadsheetParser(file)
        print(sp.data)
'''


class SpreadsheetParser:
    TABLE_END_FLAG = 'End of Table'
    '''
        End of Table
    '''

    def __init__(self, excelFile, ignoreBlankLines=True, tableNames=None):
        self.__firstDataColumnIndex = DATA_START_COLUMN_INDEX - 1  # starts from 0 . the value is (3-1)=2
        # If the line is blank, then igmore it if set to True
        self.__ignoreBlankLines = ignoreBlankLines
        self.__tableNames = tableNames
        # 1. read data from spreadsheet file

        if isinstance(excelFile, djangoUploadedfile.UploadedFile):
            self.__inputs = {}
            self.__file = excelFile.name
        elif os.path.isfile(excelFile):
            self.__inputs = {}
            self.__file = excelFile
        else:
            raise Exception('[' + excelFile + '] file is not exists.')
        # f = pd.ExcelFile(excelFile)
        with pd.ExcelFile(excelFile) as f:
            sheetData = []
            for sheetName in f.sheet_names:
                d = pd.read_excel(f, sheet_name=sheetName)
            sheetData = []
            for sheetName in f.sheet_names:
                d = pd.read_excel(excelFile, sheet_name=sheetName)
                if len(d.columns) > 0 and d.columns[0] is not None \
                        and type(d.columns[0]) == str \
                        and d.columns[0].lower() == 'do not modify this column':
                    d = d.where(d.notnull(), None)
                    d = d.to_numpy()
                    sheetData.append(d)
            # 2 .read user's input data
            for data in sheetData:
                for i in range(len(data)):
                    row = data[i]
                    prmName = row[0]
                    if prmName is not None and len(prmName) > 0:
                        if prmName.upper() == 'EOD':
                            break
                        elif prmName[0] != '>':  # ignore output parameters. e.g. ">projectName"
                            v = self.__readPrm(prmName, data, i)
                            self.__inputs[prmName] = v

    def __readPrm(self, name, data, startRowNo):
        isTable = self.__isTable(name, data, startRowNo)
        v = None
        if not isTable:
            row = data[startRowNo]
            v = row[self.__firstDataColumnIndex]
        else:
            v = []
            titles = data[startRowNo]
            if len(titles) > self.__firstDataColumnIndex:  # table's first column is column "C"
                totalTableColumns = 0
                titles = titles[self.__firstDataColumnIndex:]
                for title in titles:
                    if title is not None and (type(title) == str and title != '' or type(title) == float and not math.isnan(title)):
                        totalTableColumns += 1
                    else:
                        break
                titles = titles[0:totalTableColumns]
                # table data starts from next line
                i = startRowNo + 1
                while True:
                    row = data[i]
                    row = row[self.__firstDataColumnIndex:]
                    endTableFlag = row[0]
                    if endTableFlag is not None and type(endTableFlag) == str \
                            and endTableFlag == SpreadsheetParser.TABLE_END_FLAG:
                        break
                    rowCellData = row[0:totalTableColumns].tolist()
                    if self.__ignoreBlankLines:
                        isAllBlank = True
                        for item in rowCellData:
                            if not isNullBlank(item):
                                isAllBlank = False
                                break
                        if not isAllBlank:
                            v.append(rowCellData)
                    else:
                        v.append(rowCellData)
                    i += 1
        return v

    def __isTable(self, name, sheetData, startRowNo):
        if self.__tableNames is not None and name in self.__tableNames:
            return True
        # check the end "End of Table" flag
        for i in range(startRowNo + 1, len(sheetData)):
            row = sheetData[i]
            prmName, tableFlag = row[0], row[2]
            if not isNullBlank(prmName):
                return False
            if tableFlag == SpreadsheetParser.TABLE_END_FLAG:
                return True
        return False

    '''
    def cell_background_is_cyan ( workbook, cell ):
        # Returns TRUE if the given cell from the given workbook has a solid cyan RGB (0,255,255) background.
        # Note that the workbook must be opened with formatting_info = True, i.e.
        #     xlrd.open_workbook(xls_filename, formatting_info=True)
        assert type (cell) is xlrd.sheet.Cell
        assert type (workbook) is xlrd.book.Book

        xf_index = cell.xf_index
        xf_style = workbook.xf_list[xf_index]
        xf_background = xf_style.background

        fill_pattern = xf_background.fill_pattern
        pattern_colour_index = xf_background.pattern_colour_index
        background_colour_index = xf_background.background_colour_index

        pattern_colour = workbook.colour_map[pattern_colour_index]
        background_colour = workbook.colour_map[background_colour_index]

        # If the cell has a solid cyan background, then:
        #  - fill_pattern will be 0x01
        #  - pattern_colour will be cyan (0,255,255)
        #  - background_colour is not used with fill pattern 0x01. (undefined value)
        #    So despite the name, for a solid fill, the background colour is not actually the background colour.
        # Refer https://www.openoffice.org/sc/excelfileformat.pdf S. 2.5.12 'Patterns for Cell and Chart Background Area'
        if fill_pattern == 0x01 and pattern_colour == (0,255,255):
            return True
        return False
    '''

    @property
    def file(self):
        return self.__file

    @property
    def data(self):
        return self.__inputs

    def get(self, name):
        return None if name not in self.__inputs.keys() else self.__inputs[name]

    def __str__(self):
        return str(self.__inputs.keys())


class SpreadsheetWriter:
    def __init__(self, parameters, templateFile, outputFile) -> None:
        if not isinstance(templateFile, djangoUploadedfile.UploadedFile):
            if templateFile is None or not os.path.isfile(templateFile):
                logger.error('Template file [%s] is not found.', templateFile)
                raise IkValidateException('Template file is not found.')
        if isNullBlank(outputFile):
            logger.error('Output file can not be empty.', outputFile)
            raise IkValidateException('Template file is not found.')
        if os.path.isfile(outputFile):
            logger.error('Output file [%s] is exists.', outputFile)
            raise IkValidateException('Output file is exists.')
        self.__parameters = {} if parameters is None else parameters
        self.__templateFile = templateFile
        self.__outputFile = outputFile

    def write(self) -> Boolean2:
        wb = None
        try:
            wb = load_workbook(self.__templateFile)
            if len(self.__parameters) > 0:
                self.__write(wb)
            if os.path.isfile(self.__outputFile):
                logger.error('Output file [%s] is exists.', self.__outputFile)
                raise IkValidateException('Output file is exists.')
            pathlib.Path(pathlib.Path(self.__outputFile).parent).mkdir(parents=True, exist_ok=True)
            wb.save(self.__outputFile)
            return Boolean2(True, 'success')
        except Exception as e:
            traceback.print_exc()
            logger.error('export failed: %s', e)
            return Boolean2(trueFalse=False, data='System error.')
        finally:
            if wb is not None:
                try:
                    wb.close()
                except:
                    logger.error('Close workbook [%s] failed', self.__outputFile)

    def __write(self, wb):
        # 1. get all parameters in the template file
        nameSheetDict = {}
        for stname in wb.sheetnames:
            st = wb[stname]
            if st[1] is None or st[1][0].value is None or str(st[1][0].value).lower() != 'Do not modify this column'.lower():
                continue
            i = 1   # starts from row 2
            while True:
                i += 1
                if i > st.max_row:
                    break
                cell = st[i][0]
                if cell is not None:
                    content = cell.value
                    if content is not None:
                        if str(content).upper() == 'EOD':
                            break
                        elif content.strip() != '':
                            nameSheetDict[content.strip()] = st
        for name, value in self.__parameters.items():
            if name not in nameSheetDict.keys():
                print('Parameter [%s] is not found in the tempate file [%s]' % (name, self.__templateFile))
            st = nameSheetDict.get(name, None)
            data = value
            sheetName = None
            columnIndex = DATA_START_COLUMN_INDEX
            rowIndex = None
            if type(value) == dict:  # Example: 'segmentation': {'data': segmentation, 'sheet': 'segmentation','rowIndex': 17, 'columnIndex': 'E'}
                sheetName = value.get('sheet', None)
                if sheetName is not None:
                    st = wb[sheetName]
                    if st is None:
                        raise IkValidateException('Sheet [%s] is not exists. Plesae check.' % sheetName)
                data = value.get('data', None)
                columnIndex = value.get('columnIndex', DATA_START_COLUMN_INDEX)
                if columnIndex is not None and type(columnIndex) == str:
                    columnIndex = columnName2Index(columnIndex)
                rowIndex = value.get('rowIndex', None)
            if st is None:
                raise IkValidateException('Parameter name [%s] is not exists. Plesae check.' % name)

            if self.__isSingleValue(st, name, data):
                self.__writeSingleValue(st, name, data, columnIndex=columnIndex, rowIndex=rowIndex)
            else:
                self.__writeTableValue(st, name, data, columnIndex=columnIndex, rowIndex=rowIndex)

    def __isSingleValue(self, st, name, value) -> bool:
        return type(value) != list  # None can be single value or table value

    def __getNameRowIndex(self, st, name) -> int:
        i = 1   # starts from row 2
        while True:
            i += 1
            if i > st.max_row:
                break
            cell = st[i][0]
            if cell is not None:
                content = cell.value
                if content is not None and content == name:
                    return i
        return -1

    def __writeSingleValue(self, st, name, value, columnIndex=DATA_START_COLUMN_INDEX, rowIndex=None):
        rowNo = rowIndex if rowIndex is not None else self.__getNameRowIndex(st, name)
        st[columnIndex2Name(columnIndex) + str(rowNo)] = value

    def __writeTableValue(self, st, name, values, columnIndex=DATA_START_COLUMN_INDEX, rowIndex=None):
        if values is None or len(values) == 0:
            return
        v2 = [(v if type(v) == list else [v]) for v in values]

        lastTitleRow = rowIndex - 1 if rowIndex is not None else self.__getNameRowIndex(st, name)

        tableColumnTitles = []
        firstRowCells = []
        for colIndex in range(columnIndex, len(st[lastTitleRow]) + 1):
            title = st[columnIndex2Name(colIndex) + str(lastTitleRow)].value
            if title is None or title == '':
                break
            else:
                tableColumnTitles.append(title)
                firstRowCells.append(st[columnIndex2Name(colIndex) + str(lastTitleRow + 1)])
        rowIndex = lastTitleRow + 1

        # clean table data if exists
        rowNo = rowIndex
        totalEmptyRows = 0
        while True:
            tableEndFlag = st[columnIndex2Name(columnIndex) + str(rowNo)].value
            if tableEndFlag is not None and tableEndFlag == SpreadsheetParser.TABLE_END_FLAG:
                break
            for j in range(len(tableColumnTitles)):
                cellName = columnIndex2Name(columnIndex + j) + str(rowNo)
                st[cellName] = None  # clean
            rowNo += 1
            if rowNo > st.max_row or rowNo > 1048576:
                break
            totalEmptyRows += 1

        for i in range(len(v2)):
            rowData = v2[i]
            if i > 0:   # tempate table has a blank row
                rowIndex += 1
                if totalEmptyRows == 1:
                    st.insert_rows(rowIndex)
                else:
                    totalEmptyRows -= 1
            for j in range(len(rowData)):
                cellName = columnIndex2Name(columnIndex + j) + str(rowIndex)
                try:
                    st[cellName] = rowData[j]
                except Exception as e:
                    msg = 'Fill in cell [%s].[%s] failed: %s' % (st.title, cellName, str(e))
                    logger.error(msg)
                    raise e
            if i > 0:    # update the cell styles (starts from the 2nd row)
                for j in range(len(firstRowCells)):
                    toCell = firstRowCells[j]
                    cellName = columnIndex2Name(columnIndex + j) + str(rowIndex)
                    copyCellStyle(st[cellName], toCell)
