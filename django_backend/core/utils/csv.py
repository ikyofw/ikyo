'''
.. list-table:: ycsv - Function Toolbox for input.csv 
   :widths: 10, 15, 15, 75
   :header-rows: 1

   * - Version
     - Date
     - Author
     - Description
   * - v1
     - 2023-11-10
     - Li
     - Copied from yio.py v22.
   * - v2
     - 2024-01-31
     - Li
     - 1. Modify function CreateVariables: change variables to be a optional parameter. 
       2. Add CSV file encoding check.
'''
import chardet
import logging, csv, os
from pathlib import Path

COMMENT_LINE_FLAG = '#'
SINGLE_VALUE_FLAG = 's'
TABLE_VALUE_FLAG = 't'

SUPPORT_1000_SEPATATOR_NUMBER = True


def ReadData(csvFile: object) -> dict:
    """Read-in an existing "input.csv" as current input values.

    Args:
        csvFile (str/Path): full file path of "input.csv"

    Returns:
        list: a dict contain current input data which stored in "input.csv"
    """
    if not csvFile:
        raise Exception('Parameter [csvFile] is mandatory.')
    pCsvFile = Path(csvFile)
    if not pCsvFile.is_file():
        raise Exception('File [%s] is not exists.' % csvFile)

    chardetInfo = None
    with open(pCsvFile, 'rb') as f:
        content = f.read()
        chardetInfo = chardet.detect(content)
    fileEncoding = chardetInfo['encoding']
    if fileEncoding == 'ISO-8859-1':
        fileEncoding = 'ansi'

    # 1. read data without comment line
    csvData = {}
    csvDataType = {}
    variableType = None
    variableName = None
    variableValue = None
    rowNo = 0
    with open(pCsvFile, newline='', encoding=fileEncoding) as csvfile:
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            rowNo += 1
            if len(row) == 0:
                logging.warning('Ignore the blank line %s.' % rowNo)
            else:
                flag = row[0]
                if flag.startswith(COMMENT_LINE_FLAG):
                    continue # ignore comment line
                if flag == SINGLE_VALUE_FLAG or flag == TABLE_VALUE_FLAG:
                    variableType = flag
                    if len(row) < 2:
                        raise Exception('Variable name is not found. Please check row %s' % rowNo)
                    variableName = row[1]
                    if not variableName.strip():
                        raise Exception('Variable name cannot be empty. Please check row %s' % rowNo)
                    csvData[variableName] = [] if flag == TABLE_VALUE_FLAG else None # init value
                    csvDataType[variableName] = variableType
                elif variableType == SINGLE_VALUE_FLAG:
                    if len(row) > 1:
                        variableValue = row[1]
                        csvData[variableName] = variableValue
                    variableType = None
                    variableName = None
                    variableValue = None
                elif variableType == TABLE_VALUE_FLAG:
                    tableData = csvData[variableName]
                    tableData.append(row[1:])
                elif variableType:
                    raise Exception('Unknown variable type [%s]' % variableType)

    # 2. proces values. Always convert a string to a number first.
    values = {}
    for name, value in csvData.items():
        variableType = csvDataType[name]
        if variableType == SINGLE_VALUE_FLAG:
            values[name] = __ToNumber(value)
        elif variableType == TABLE_VALUE_FLAG:
            tableValues = []
            for row in value:
                rowValues = []
                for item in row:
                    rowValues.append(__ToNumber(item))
                tableValues.append(rowValues)
            values[name] = tableValues
        else:
            raise Exception('Unsupport data type [%s].' % variableType)
    return values


def CreateVariables(csvFile: object, variables: dict = None) -> dict:
    """Read-in an existing "input.csv" as current input values.

    Args:
        csvFile (str/Path): full file path of "input.csv"
        variables (dict): e.g. globals() or a specified dict.

    Returns:
        list: a dict contain current input data which stored in "input.csv"
    """
    csvData = ReadData(csvFile)
    if variables:
        for name, value in csvData.items():
            if value is None:
                exec('%s = None' % (name), variables)
            elif type(value) == str:
                exec('%s = "%s"' % (name, value.replace('"', '\\"')), variables)
            elif type(value) == int:
                exec('%s = %i' % (name, value), variables)
            elif type(value) == float:
                exec('%s = %f' % (name, value), variables)
            else:
                exec('%s = %s' % (name, str(value).replace('"', '\\"')), variables)
    return csvData


def Write2CsvFile(csvFile: object, data: dict, overwrite: bool = True, specifiedTableValues: list = None, comments: object = None, sort_keys: bool = False) -> None:
    """ write data to csv file

    Args:
        csvFile (str/Path): output file
        data (dict): csv file content
        overwrite (bool): overwrite the existing files. Default to True.
        specifiedTableValues (list[str]): specify a variable is a table. 
                                            E.g. when its value is None, then need to specify this value is a table, 
                                                otherwrise it should be a single value.
        comments (str/list): output comments

    Returns:
        void: void
    """
    pFile = Path(csvFile)
    if pFile.is_file():
        if overwrite:
            os.remove(pFile)
    os.makedirs(pFile.parent, exist_ok=True)

    csvData = []
    if comments:
        if type(comments) == list:
            for row in comments:
                if type(row) == list:
                    row2 = [COMMENT_LINE_FLAG]
                    for item in row:
                        row2.append(str(item) if item else None)
                    csvData.append(row2) 
                else:
                    csvData.append([COMMENT_LINE_FLAG, str(row)])        
        else:
            csvData.append([COMMENT_LINE_FLAG, str(comments)])

    if data:
        keys = sorted([key for key in data.keys()]) if sort_keys else [key for key in data.keys()]
        for i in range(len(keys)):
            name = keys[i]
            value = data[name]
            if type(value) == list or (specifiedTableValues and name in specifiedTableValues):
                # table values
                csvData.append([TABLE_VALUE_FLAG, name])
                if value:
                    for tableRow in value:
                        outputValues = [item for item in tableRow]
                        outputValues.insert(0, None)
                        csvData.append(outputValues)
            else:
                # single value
                # all None are single value
                csvData.append([SINGLE_VALUE_FLAG, name])
                csvData.append([None,value])

    with open(pFile, mode='a+', newline='', encoding="utf-8") as csvfile: # Append to the exist file.
        csvwriter = csv.writer(csvfile)
        for row in csvData:
            csvwriter.writerow(row)


def __ToNumber(value: str) -> object:
    if not value:
        return None # 
    if value.startswith('0') and not value.startswith('0.'):
        # E.g. "000123", this should be a string, "0.123" should be a number
        return value
    # try int, then float, else return itself
    value2 = value.replace(',', '') if SUPPORT_1000_SEPATATOR_NUMBER else value # supports 1000 separator (,)
    try:
        return int(value2)
    except:
        try:
            return float(value2)
        except:
            pass
    return value
