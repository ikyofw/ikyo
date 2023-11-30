import random

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


pageableTestList = []
for i in range(50):
    pageableTestList.append({"id": i, "rmk1": "test{}".format(random.randint(1, 10)), "rmk2": "test{}".format(random.randint(1, 10))})


class PageableDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()
        self.pageNm = 1

    def getClockins(self):
        res = self.getRequestData()
        if len(res) == 0:
            return IkSccJsonResponse(data=pageableTestList)

        pageSize = self._getPaginatorPageSize("clockInFg")  # screen
        pageNum = self._getPaginatorPageNumber("clockInFg")  # from client
        self.pageNm = pageNum

        start = (pageNum - 1) * pageSize
        end = pageNum * pageSize
        # rcs = pageabletest.objects.all().order_by("id")
        rcs = pageableTestList
        if pageNum == 0:
            return IkSccJsonResponse(data={"clockInFg": rcs, "__dataLen__": len(rcs)})
        else:
            return IkSccJsonResponse(data={"clockInFg": rcs[start:end], "__dataLen__": len(rcs)})

    def getClockins1(self):
        return IkSccJsonResponse(data=pageableTestList)

    def save(self):
        requestData = devDemoGetRequestData(self.request)
        fgNames = list(requestData.keys())
        updatedRmk = False
        data = requestData.get(fgNames[0]).get('data')
        for i in range(len(data)):
            rc = {"id": data[i][2], "rmk1": data[i][3], "rmk2": data[i][4]}
            if data[i][0] == "~":
                for j in range(len(pageableTestList)):
                    if str(pageableTestList[j]["id"]) == str(rc["id"]):
                        pageableTestList[j] = rc
                        break
                updatedRmk = True
            elif data[i][0] == "+":
                pageableTestList.append(rc)
                updatedRmk = True
            elif data[i][0] == "-":
                for j in range(len(pageableTestList)):
                    if str(pageableTestList[j]["id"]) == str(rc["id"]):
                        del pageableTestList[j]
                        break
                updatedRmk = True
        if updatedRmk:
            return IkSccJsonResponse(message="Saved")
        else:
            return IkErrJsonResponse(message="No modification")
