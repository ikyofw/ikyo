import random

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


iconAndTextTestList = []
for i in range(10):
    iconAndTextTestList.append({"id": i, "rmk1": "test{}\ntest".format(i), "rmk2": 100 - i})


class IconAndTextDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def getClockins(self):
        rcs = iconAndTextTestList
        return IkSccJsonResponse(data=rcs)

    def getMessage(self):
        data = {'title': '', 'message': 'message in backend\n new line', 'uploadLabel': 'test label'}
        return IkSccJsonResponse(data=data)

    def save(self):
        requestData = devDemoGetRequestData(self.request)
        fgNames = list(requestData.keys())
        updatedRmk = False
        data = requestData.get(fgNames[0]).get('data')
        for i in range(len(data)):
            rc = {"id": data[i][2], "rmk1": data[i][3], "rmk2": data[i][4]}
            if data[i][0] == "~":
                for j in range(len(iconAndTextTestList)):
                    if str(iconAndTextTestList[j]["id"]) == str(rc["id"]):
                        iconAndTextTestList[j] = rc
                        break
                updatedRmk = True
            elif data[i][0] == "+":
                iconAndTextTestList.append(rc)
                updatedRmk = True
            elif data[i][0] == "-":
                for j in range(len(iconAndTextTestList)):
                    if str(iconAndTextTestList[j]["id"]) == str(rc["id"]):
                        del iconAndTextTestList[j]
                        break
                updatedRmk = True
        if updatedRmk:
            return IkSccJsonResponse(message="Saved")
        else:
            return IkErrJsonResponse(message="No modification")
