"""Example Table Header/Footer defined in spreadsheets.

Author:
    Li

Date:
    2023-02-06

"""

import json

import core.ui.ui as ikui
from core.view.screenView import ScreenAPIView
from core.utils.langUtils import isNullBlank, isNotNullBlank
from core.core.http import IkSccJsonResponse, IkErrJsonResponse

from .baseViews import devDemoGetRequestData


DialogList = [{
    'id': '1',
    'office': 'NY',
    'full_nm': 'New York'
}, {
    'id': '2',
    'office': 'LA',
    'full_nm': 'Los Angeles'
}, {
    'id': '3',
    'office': 'CH',
    'full_nm': 'Chicago'
}, {
    'id': '4',
    'office': 'HO',
    'full_nm': 'Houston'
}, {
    'id': '5',
    'office': 'PH',
    'full_nm': 'Phoenix'
}, {
    'id': '6',
    'office': 'SA',
    'full_nm': 'San Antonio'
}, {
    'id': '7',
    'office': 'SD',
    'full_nm': 'San Diego'
}, {
    'id': '8',
    'office': 'DA',
    'full_nm': 'Dallas'
}, {
    'id': '9',
    'office': 'SJ',
    'full_nm': 'San Jose'
}, {
    'id': '10',
    'office': 'AU',
    'full_nm': 'Austin'
}]
officeList = [{
    'id': '1',
    'office': 'NY',
    'full_nm': 'New York'
}, {
    'id': '2',
    'office': 'LA',
    'full_nm': 'Los Angeles'
}, {
    'id': '3',
    'office': 'CH',
    'full_nm': 'Chicago'
}, {
    'id': '4',
    'office': 'HO',
    'full_nm': 'Houston'
}]


class TableHeaderFooterDemo(ScreenAPIView):
    '''
        http://localhost:8000/IkTableHeaderFooterDemo
    '''

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen: ikui.Screen):
            if screen.subScreenName == 'dialog':
                pass
                # dialogTableAttr = self.getSessionParameter('dialogTableAttr')
                # if not dialogTableAttr or dialogTableAttr == 'check':
                #     screen.setFieldsVisible(fieldGroupName='dialogBar', fieldNames='save', visible=False)
                # else:
                #     screen.getFieldGroup('dialogFg2').editable = True
                #     screen.getFieldGroup('dialogFg2').groupType = 'table'

        self.beforeDisplayAdapter = beforeDisplayAdapter
    
    def getComboData(self):
        data = [
            {'value': ' ', 'display': ' '},
            {'value': 106, 'display': 'option 1'},
            {'value': 206, 'display': 'option 2'},
            {'value': 306, 'display': 'option 3'},
            {'value': 0, 'display': 'option 4'}
        ]
        return IkSccJsonResponse(data=data)
    
    def getOffice(self):
        return IkSccJsonResponse(data=officeList)

    def getTableDataRcs(self):
        # return DummyModel record list
        rcs = self.getSessionParameter('data', delete=True)
        if rcs is not None:
            return rcs

        rcs = []
        for i in range(1, 5):
            rc = {'id': i}
            for j in range(0, 10):
                rc['f%s' % j] = i * 100 + j + 1  # 101, 102 ... 201, 202 ...
                if j == 6:
                    rc['f6'] = True
                if j == 7:
                    rc['f7'] = "2023-09-06"
                if j == 8:
                    rc['f8'] = "NY"
            rcs.append(rc)
        rcs[1], rcs[2] = rcs[2], rcs[1]

        style = [
            {'row': '3', 'col': 'f1', 'style': {'background-color': 'rgb(102, 204, 255)'}},
            {'row': '4', 'style': {'height': '50px'}},
            {'col': 'f2', 'style': {'fontWeight': '700'}}
        ]

        return self.getSccJsonResponse(data=rcs, cssStyle=style)
    
    def buttonClick(self):
        return IkSccJsonResponse(message="Button Click!")
    
    def pluginClick(self):
        return IkSccJsonResponse(message="Plugin Click!")
    
    def submit(self):
        data = self.getRequestData()
        print(data)
        pass

    def postRowItem1(self):
        requestData = devDemoGetRequestData(self.request)
        currentOffices = requestData.get('row', {}).get('f8', None)
        self.setSessionParameters({'currentOffices1': currentOffices})
        return ikui.DialogMessage.getSuccessResponse(message='message2', title="message2 in backend")

    def uploadPage(self):
        requestData = devDemoGetRequestData(self.request)
        dialogFg1 = json.loads(requestData.get("dialogFg1"))

        data = {}
        print(dialogFg1['data'])
        for i in dialogFg1['data']:
            if i[0] == 'true':
                data = {'value': i[2], 'display': i[3]}
        return IkSccJsonResponse(data=data)

    def getDialogRcs(self):
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
            if currentOffices1 and i['office'] in currentOffices1:
                data.append({'__SLT_': True, 'id': i['id'], 'office': i['office'], 'full_nm': i['full_nm']})
            else:
                data.append({'id': i['id'], 'office': i['office'], 'full_nm': i['full_nm']})
        return IkSccJsonResponse(data=data)