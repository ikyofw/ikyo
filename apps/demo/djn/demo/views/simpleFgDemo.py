import json

import core.ui.ui as ikui
from core.core.http import IkErrJsonResponse, IkSccJsonResponse
from core.utils.langUtils import isNullBlank
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


class SimpleFgDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def getCombo(self):
        data = [{'nm': 'option 1'}, {'nm': 'option 2'}]
        return IkSccJsonResponse(data=data)

    def getCombo2(self):
        data = [{'id': '11', 'nm': 'option 11'}, {'id': '22', 'nm': 'option 22'}]
        return IkSccJsonResponse(data=data)

    def getSimpleFg(self):
        rmk1 = self.getSessionParameter('rmk1')
        simpleFg = self.getSessionParameter('simpleFg')
        if isNullBlank(rmk1):
            rmk1 = '11'
        if isNullBlank(simpleFg):
            schItems = {
                'schTextbox': 'init',
                'schCombobox1': 'option 1',
                'schCombobox': 'option 1',
                'schCheckbox1': 'True',
                'schCheckbox2': 'Y',
                'schDatebox': '2023-10-19',
                'schAdvancedSelection': rmk1
            }
        else:
            simpleFg['schAdvancedSelection'] = rmk1
            schItems = simpleFg
        return IkSccJsonResponse(data=schItems)

    def getMsg(self):
        return ikui.DialogMessage.getSuccessResponse(message='message', title="message in backend")

    def updateSelect(self):
        requestData = devDemoGetRequestData(self.request)
        dialogFg = requestData.get("dialogFg")
        # simpleFg = requestData.get("simpleFg")
        aaa = json.loads(dialogFg)
        # bbb = json.loads(simpleFg)
        # return self.setSessionParameters({'rmk1': aaa['rmk'], 'simpleFg': bbb})
        return IkSccJsonResponse(data={'value': aaa['rmk']})

    def submit(self):
        requestData = self.getRequestData()
        schItems = requestData.get('simpleFg')
        self.setSessionParameters({'schItems': schItems})
        return IkSccJsonResponse()

    def getShowFg(self):
        schItems = self.getSessionParameter('schItems')
        data = [schItems] if schItems else []
        return IkSccJsonResponse(data=data)

    def clearSearchFg(self):
        return self.deleteSessionParameters('schItems')
