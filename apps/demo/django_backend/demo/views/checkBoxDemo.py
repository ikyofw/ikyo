import random

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


checkBoxTestList = []
for i in range(2):
    checkBoxTestList.append({"id": str(i), "rmk1": "test{}".format(random.randint(1, 5)), "color": "none", "default": "false"})


class CheckBoxDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def getClockins(self):
        return IkSccJsonResponse(data=checkBoxTestList)

    def save(self):
        requestData = devDemoGetRequestData(self.request)
        fgNames = list(requestData.keys())
        updatedRmk = False
        data = requestData.get(fgNames[0]).get('data')
        for i in range(len(data)):
            rc = {"id": data[i][2], "rmk1": data[i][3], "color": data[i][4], "default": data[i][5]}
            if data[i][0] == "~":
                for j in range(len(checkBoxTestList)):
                    if str(checkBoxTestList[j]["id"]) == str(rc["id"]):
                        checkBoxTestList[j] = rc
                        break
                updatedRmk = True
            elif data[i][0] == "+":
                checkBoxTestList.append(rc)
                updatedRmk = True
            elif data[i][0] == "-":
                for j in range(len(checkBoxTestList)):
                    if str(checkBoxTestList[j]["id"]) == str(rc["id"]):
                        del checkBoxTestList[j]
                        break
                updatedRmk = True
        if updatedRmk:
            return IkSccJsonResponse(message="Saved")
        else:
            return IkErrJsonResponse(message="No modification")
