import random
import json


import core.ui.ui as ikui
from core.utils.langUtils import isNullBlank, isNotNullBlank
from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


dialogTestList = []
for i in range(2):
    dialogTestList.append({
        "id": str(i),
        "rmk1": "test{}".format(random.randint(1, 5)),
        "office": "SZ",
        "offices1": "SZ,WH",
        "offices2": "SG,HK",
        "color": "none",
        "default": "false"
    })
DialogList = [{
    'id': '1',
    'office': 'SG',
    'full_nm': 'Singapore'
}, {
    'id': '2',
    'office': 'HK',
    'full_nm': 'HONG KONG'
}, {
    'id': '3',
    'office': 'WH',
    'full_nm': 'WuHan'
}, {
    'id': '4',
    'office': 'SZ',
    'full_nm': 'ShenZhen'
}, {
    'id': '5',
    'office': 'NY',
    'full_nm': 'New York'
}, {
    'id': '6',
    'office': 'LD',
    'full_nm': 'London'
}, {
    'id': '7',
    'office': 'TK',
    'full_nm': 'Tokyo'
}, {
    'id': '8',
    'office': 'SY',
    'full_nm': 'Sydney'
}, {
    'id': '9',
    'office': 'BR',
    'full_nm': 'Berlin'
}, {
    'id': '10',
    'office': 'PA',
    'full_nm': 'Paris'
}]

officeList = [{
    'id': '1',
    'office': 'SG',
    'full_nm': 'Singapore'
}, {
    'id': '2',
    'office': 'HK',
    'full_nm': 'HONG KONG'
}, {
    'id': '3',
    'office': 'WH',
    'full_nm': 'WuHan'
}, {
    'id': '4',
    'office': 'SZ',
    'full_nm': 'ShenZhen'
}]


class DialogDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen: ikui.Screen):
            if screen.subScreenName == 'dialog2':
                dialogTableAttr = self.getSessionParameter('dialogTableAttr')
                if not dialogTableAttr or dialogTableAttr == 'check':
                    screen.setFieldsVisible(fieldGroupName='dialogBar', fieldNames='save', visible=False)
                else:
                    screen.getFieldGroup('dialogFg2').editable = True
                    screen.getFieldGroup('dialogFg2').groupType = 'table'

        self.beforeDisplayAdapter = beforeDisplayAdapter

    def getClockins(self):
        return IkSccJsonResponse(data=dialogTestList)

    def getCombo2(self):
        return IkSccJsonResponse(data=officeList)

    def uploadPage1(self):
        return IkSccJsonResponse(message='button click')

    def postRowItem(self):
        requestData = devDemoGetRequestData(self.request)
        currentOffice = requestData.get('row', {}).get('office', None)
        self.setSessionParameters({'currentOffice': currentOffice})
        self.deleteSessionParameters(['currentOffices1', 'currentOffices2'])
        return ikui.DialogMessage.getSuccessResponse(message='message1', title="message1 in backend")

    def uploadPage2(self):
        requestData = devDemoGetRequestData(self.request)
        dialogFg2 = requestData.get("dialogFg2")

        data = {}
        for i in dialogFg2['data']:
            if i[0] == 'true':
                data = {'value': i[2], 'display': i[3]}
        return IkSccJsonResponse(data=data)

    def uploadPage3(self):
        requestData = devDemoGetRequestData(self.request)
        dialogFg3 = requestData.get("dialogFg3")

        values, displays = [], []
        for i in dialogFg3['data']:
            if i[0] == 'true':
                values.append(str(i[2]))
                displays.append(str(i[3]))
        data = {'value': ",".join(values), 'display': ",".join(displays)}
        return IkSccJsonResponse(data=data)

    def uploadPage4(self):
        DialogOfficeList = self.getSessionParameter('DialogOfficeList')
        requestData = devDemoGetRequestData(self.request)
        dialogFg1 = requestData.get("dialogFg1")
        values = json.loads(dialogFg1)['advancedComboBoxField']

        offices = [item.strip() for item in values.split(",")]
        displays = []
        for i in DialogOfficeList:
            if i['office'] in offices:
                displays.append(i['full_nm'])
        data = {'value': values, 'display': ",".join(displays)}
        return IkSccJsonResponse(data=data)

    def getDtlRc(self):
        data = officeList[0]
        return IkSccJsonResponse(data=data)

    def getOffice(self):
        return IkSccJsonResponse(data=officeList)

    def updateSelect(self):
        requestData = devDemoGetRequestData(self.request)
        dialogFg2 = requestData.get("dialogFg2")

        data = {'value': ''}
        for i in dialogFg2['data']:
            if i[0] == 'true':
                data = {'value': i[2], 'display': i[3]}
        return IkSccJsonResponse(data=data)

    def postRowItem1(self):
        requestData = devDemoGetRequestData(self.request)
        currentOffices = requestData.get('row', {}).get('offices1', None)
        self.setSessionParameters({'currentOffices1': currentOffices})
        self.deleteSessionParameters(['currentOffice', 'currentOffices2'])
        return ikui.DialogMessage.getSuccessResponse(message='message2', title="message2 in backend")

    def postRowItem2(self):
        requestData = devDemoGetRequestData(self.request)
        currentOffices = requestData.get('row', {}).get('offices2', None)
        self.setSessionParameters({'currentOffices2': currentOffices})
        self.deleteSessionParameters(['currentOffice', 'currentOffices1'])
        return ikui.DialogMessage.getSuccessResponse(message='message2', title="message2 in backend")

    def getDialogRc(self):
        currentOffices = self.getSessionParameter('currentOffices2')
        return IkSccJsonResponse(data={'advancedComboBoxField': currentOffices})

    def schDialog(self):
        requestData = devDemoGetRequestData(self.request)
        dialogSchFg = requestData.get('dialogSchFg', '')
        schOffice = json.loads(dialogSchFg)['officeField']
        return self.setSessionParameters({'schOffice': schOffice})

    def getDialogRcs(self):
        currentOffice = self.getSessionParameter('currentOffice')
        currentOffices1 = self.getSessionParameter('currentOffices1')
        schOffice = self.getSessionParameter('schOffice')
        DialogOfficeList = self.getSessionParameter('DialogOfficeList')
        if isNullBlank(DialogOfficeList):
            DialogOfficeList = DialogList
            self.setSessionParameters({'DialogOfficeList': DialogOfficeList})
        data = []
        for i in DialogOfficeList:
            if schOffice and schOffice.lower() not in i['full_nm'].lower():
                continue
            if (currentOffice and i['office'] in currentOffice) or (currentOffices1 and i['office'] in currentOffices1):
                data.append({'__SLT_': True, 'id': i['id'], 'office': i['office'], 'full_nm': i['full_nm']})
            else:
                data.append({'id': i['id'], 'office': i['office'], 'full_nm': i['full_nm']})
        return IkSccJsonResponse(data=data)

    def save(self):
        DialogOfficeList = self.getSessionParameter('DialogOfficeList')
        requestData = devDemoGetRequestData(self.request)
        dialogFg2 = requestData.get('dialogFg2', {}).get('data', [])
        for index, row in enumerate(dialogFg2):
            if row[0] == "~":
                DialogOfficeList[index] = {'id': row[1], 'office': row[2], 'full_nm': row[3]}
        return self.setSessionParameters({'DialogOfficeList': DialogOfficeList})

    def change(self):
        dialogTableAttr = self.getSessionParameter('dialogTableAttr')
        if dialogTableAttr == 'edit':
            self.setSessionParameters({'dialogTableAttr': 'check'})
        else:
            self.setSessionParameters({'dialogTableAttr': 'edit'})
        return IkSccJsonResponse()
