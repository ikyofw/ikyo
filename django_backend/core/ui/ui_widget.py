COMBOBOX_DATA_NAME = 'data'

def addComboboxData(comboboxField, recordSets, dataDisplayField, dataValueField):
    data = []
    for r in recordSets:
        data.append({'display': r[dataDisplayField], 'value': r[dataValueField]})
    comboboxField[COMBOBOX_DATA_NAME] = data

def addComboboxData2(comboboxField, dataList):
    data = []
    for r in dataList:
        data.append({'value': r[0], 'display': r[1]})
    comboboxField[COMBOBOX_DATA_NAME] = data



