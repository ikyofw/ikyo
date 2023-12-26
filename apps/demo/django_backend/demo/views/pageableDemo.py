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