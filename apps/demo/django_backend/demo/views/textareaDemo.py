import random

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


textareaTestList = []
for i in range(10):
    textareaTestList.append({"id": str(i), "rmk1": "test{}test\ntesttest\n".format(
        random.randint(1, 5)), "rmk2": "test{}".format(random.randint(1, 5))})


class TextareaDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def getClockins(self):
        return IkSccJsonResponse(data=textareaTestList)

    def save(self):
        requestData = devDemoGetRequestData(self.request)
        fgNames = list(requestData.keys())
        updatedRmk = False
        data = requestData.get(fgNames[0]).get('data')
        for i in range(len(data)):
            rc = {"id": data[i][2], "rmk1": data[i][3], "rmk2": data[i][4]}
            if data[i][0] == "~":
                for j in range(len(textareaTestList)):
                    if str(textareaTestList[j]["id"]) == str(rc["id"]):
                        textareaTestList[j] = rc
                        break
                updatedRmk = True
            elif data[i][0] == "+":
                textareaTestList.append(rc)
                updatedRmk = True
            elif data[i][0] == "-":
                for j in range(len(textareaTestList)):
                    if str(textareaTestList[j]["id"]) == str(rc["id"]):
                        del textareaTestList[j]
                        break
                updatedRmk = True
        if updatedRmk:
            return IkSccJsonResponse(message="Saved")
        else:
            return IkErrJsonResponse(message="No modification")
