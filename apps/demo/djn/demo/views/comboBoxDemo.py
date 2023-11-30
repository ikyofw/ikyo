import random

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


comboBoxTestList = []
for i in range(10):
    comboBoxTestList.append({"id": str(i), "rmk_id": i, "rmk1": "test{}".format(random.randint(1, 5)), "rmk2": "test{}".format(random.randint(1, 5))})


class ComboBoxDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def getClockins(self):
        tableData = self.getSessionParameter('tableData')
        if tableData is not None:
            return IkSccJsonResponse(data=tableData)
        return IkSccJsonResponse(data=comboBoxTestList)

    def getDetails(self):
        searchID = self.getSessionParameter('search-id')
        data = {}
        if searchID:
            for i in comboBoxTestList:
                if i['id'] == searchID:
                    data = i
        else:
            data = {'schRmk1': '0,1,2'}
        return IkSccJsonResponse(data=data)

    # def getType(self):
    #     field = IkScreenFgType._meta.get_field('type_nm')
    #     choice = field.choices
    #     data = []
    #     # for i in choice:
    #     #     data.append({'type_id': i[0], 'type_nm': i[1]})
    #     return IkSccJsonResponse(data=data)

    # def save(self):
    #     requestData = self.getRequestData()
    #     return

    def getRmk1(self):
        data = [{
            'rmk_id': 0,
            'rmk': 'test1'
        }, {
            'rmk_id': 1,
            'rmk': 'test2test2test2test2'
        }, {
            'rmk_id': 2,
            'rmk': 'test3'
        }, {
            'rmk_id': 3,
            'rmk': 'test4'
        }, {
            'rmk_id': 4,
            'rmk': 'test5'
        }, {
            'rmk_id': 5,
            'rmk': 'test6'
        }, {
            'rmk_id': 6,
            'rmk': 'test6'
        }, {
            'rmk_id': 7,
            'rmk': 'test6'
        }, {
            'rmk_id': 8,
            'rmk': 'test6'
        }, {
            'rmk_id': 9,
            'rmk': 'test6'
        }, {
            'rmk_id': 10,
            'rmk': 'test6'
        }, {
            'rmk_id': 11,
            'rmk': 'test6'
        }, {
            'rmk_id': 12,
            'rmk': 'test6'
        }, {
            'rmk_id': 13,
            'rmk': 'test6'
        }, {
            'rmk_id': 14,
            'rmk': 'test6'
        }]
        return IkSccJsonResponse(data=data)

    def getRmk2(self):
        schData = self.getSessionParameter('schData')
        data = []
        if schData:
            data = [{'rmk': 'test1'}, {'rmk': 'test2'}, {'rmk': 'test3'}, {'rmk': 'test4'}, {'rmk': 'test5'}]
        return IkSccJsonResponse(data=data)

    def search(self):
        requestData = self.getRequestData()
        searchRmk1 = requestData.get('searchFg')['schRmk1']
        searchRmk2 = requestData.get('searchFg')['schRmk2']
        data = []
        for i in comboBoxTestList:
            if searchRmk1 in i['rmk1'] and searchRmk2 in i['rmk2']:
                data.append(i)
        self.setSessionParameters({'tableData': data})
        return IkSccJsonResponse()

    def showDetails(self):
        requestData = self.getRequestData()
        id = requestData["EditIndexField"]
        self.setSessionParameters({'search-id': id})
        return IkSccJsonResponse()

    def updateDefaultValues1(self):
        self.setSessionParameters({'schData': True})
        return IkSccJsonResponse()

    def updateDefaultValues2(self):
        # simpleData = devDemoGetRequestData(self.request).get("simpleFg")
        # simpleData = json.loads(simpleData)
        # simpleData['rmk2'] = simpleData['rmk1']
        schRmk2 = [{'value': 'test1', 'display': 'test1'}, {'value': 'test2', 'display': 'test2'}, {'value': 'test3', 'display': 'test3'}]
        return self._returnComboboxQueryResult(fgName='searchFg', fgData=None, resultDict={'schRmk2': schRmk2})

    def save(self):
        requestData = self.getRequestData()
        pass
