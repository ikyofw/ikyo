import random

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


detailTableDemoList = []
for i in range(10):
    detailTableDemoList.append({"id": str(i), "rmk1": "test{}".format(random.randint(1, 5)), "rmk2": "test{}".format(random.randint(1, 5))})


class DetailTableDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen):
            if not self.getSessionParameterInt('search-id') is not None:
                screen.setFieldGroupsVisible(fieldGroupNames=['simpleFg', 'actionBar2'], visible=False)

        self.beforeDisplayAdapter = beforeDisplayAdapter

    def getClockins(self):
        return IkSccJsonResponse(data=detailTableDemoList)

    def getDetails(self):
        searchID = self.getSessionParameter('search-id')
        data = []
        if searchID:
            for i in detailTableDemoList:
                if i['id'] == searchID:
                    data.append(i)
        return IkSccJsonResponse(data=data)

    def getRmk2(self):
        data = [1, None, True, "2"]
        return IkSccJsonResponse(data=data)

    def search(self):
        requestData = self.getRequestData()
        searchRmk = requestData.get('searchFg')['schPiers']
        data = []
        for i in detailTableDemoList:
            if searchRmk in i['rmk1']:
                data.append(i)
        return self._returnQueryResult('outputFg', data)

    def showDetails(self):
        requestData = self.getRequestData()
        id = requestData["EditIndexField"]
        self.setSessionParameters({'search-id': id})
        return IkSccJsonResponse()

    def save(self):
        requestData = devDemoGetRequestData(self.request)
        fgNames = list(requestData.keys())
        updatedRmk = False
        data = requestData.get(fgNames[0]).get('data')
        for i in range(len(data)):
            rc = {"id": data[i][2], "rmk1": data[i][3], "rmk2": data[i][4]}
            if data[i][0] == "~":
                for j in range(len(detailTableDemoList)):
                    if str(detailTableDemoList[j]["id"]) == str(rc["id"]):
                        detailTableDemoList[j] = rc
                        break
                updatedRmk = True
            elif data[i][0] == "+":
                detailTableDemoList.append(rc)
                updatedRmk = True
            elif data[i][0] == "-":
                for j in range(len(detailTableDemoList)):
                    if str(detailTableDemoList[j]["id"]) == str(rc["id"]):
                        del detailTableDemoList[j]
                        break
                updatedRmk = True
        if updatedRmk:
            return IkSccJsonResponse(message="Saved")
        else:
            return IkErrJsonResponse(message="No modification")

    def saveDetail(self):
        requestData = devDemoGetRequestData(self.request)
        fgNames = list(requestData.keys())
        data = requestData.get(fgNames[0]).get('data')[0]
        for i in range(len(detailTableDemoList)):
            if str(detailTableDemoList[i]["id"]) == str(data[1]):
                detailTableDemoList[i] = {"id": data[1], "rmk1": data[3], "rmk2": data[4]}
                break
        return IkSccJsonResponse(message="Saved")

    def hideDetail(self):
        self.deleteSessionParameters(nameFilters='search-id')
        return IkSccJsonResponse()
