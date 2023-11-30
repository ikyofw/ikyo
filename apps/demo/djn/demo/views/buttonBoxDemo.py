import random

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


buttonBoxTestList = []
for i in range(3):
    buttonBoxTestList.append({
        "id": str(i),
        "rmk0": "test{}".format(random.randint(1, 5)),
        "rmk1": "test{}".format(random.randint(1, 5)),
        "rmk2": "test{}".format(random.randint(1, 5)),
        "enable": True
    })


class ButtonBoxDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def getButtonBoxFg(self):
        currentID = self.getSessionParameter("currentID")
        if currentID:
            for i in buttonBoxTestList:
                if i['id'] == currentID:
                    i['enable'] = False
                else:
                    i['enable'] = True
        self.deleteSessionParameters("currentID")
        return IkSccJsonResponse(data=buttonBoxTestList)

    def buttonClick(self):
        currentID = self.getRequestData().get('id', None)
        self.setSessionParameters({"currentID": currentID})
        return IkSccJsonResponse(message="test")
