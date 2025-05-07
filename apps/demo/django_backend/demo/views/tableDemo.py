import random

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


IKTableDemoList = []
checkList = ["true", "false", "null"]
for i in range(10):
    IKTableDemoList.append({
        "id": str(i),
        "Label": str(i),
        "TextBox": str(i),
        "Invisible": str(i),
        "Textarea": "abcd\n1234",
        "ComboBox": "test{}".format(random.randint(1, 3)),
        "CheckBox1": checkList[random.randint(0, 2)],
        "CheckBox2": checkList[random.randint(0, 1)],
        "DateBox": "2022-08-31 05:39:22"
    })


class TableDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def getIKTableDemo(self):
        res = self.getRequestData()
        if len(res) == 0:
            return IkSccJsonResponse(data=IKTableDemoList)

        pageSize = self._getPaginatorPageSize("IKTableDemoServerFg")  # screen
        pageNum = self._getPaginatorPageNumber("IKTableDemoServerFg")  # from client

        start = (pageNum - 1) * pageSize
        end = pageNum * pageSize
        results = IKTableDemoList
        if pageNum == 0:
            return IkSccJsonResponse(data={"data": results, "paginatorDataAmount": len(results)})
        else:
            return IkSccJsonResponse(data={"data": results[start:end], "paginatorDataAmount": len(results)})

    def getComboBox(self):
        dataList = [{'comboBox': 'test1'}, {'comboBox': 'test2'}, {'comboBox': 'test3'}]
        return IkSccJsonResponse(data=dataList)

    def buttonShowID(self):
        requestData = self.getRequestData()
        id = requestData["id"]
        return IkSccJsonResponse(message="button: The id of the clicked row is {}".format(id))

    def pluginShowID(self):
        requestData = self.getRequestData()
        id = requestData["EditIndexField"]
        return IkSccJsonResponse(message="Plugin: The id of the clicked row is {}".format(id))

    def save(self):
        requestData = devDemoGetRequestData(self.request)
        fgNames = list(requestData.keys())
        updatedRmk = False
        data = requestData.get(fgNames[0]).get('data')
        for i in range(len(data)):
            rc = {
                "id": data[i][2],
                "Label": data[i][3],
                "TextBox": data[i][4],
                "Invisible": data[i][5],
                "Textarea": data[i][6],
                "ComboBox": data[i][7],
                "CheckBox1": data[i][8],
                "CheckBox2": data[i][9],
                "DateBox": data[i][10]
            }
            if data[i][0] == "~":
                for j in range(len(IKTableDemoList)):
                    if str(IKTableDemoList[j]["id"]) == str(rc["id"]):
                        IKTableDemoList[j] = rc
                        break
                updatedRmk = True
            elif data[i][0] == "+":
                IKTableDemoList.append(rc)
                updatedRmk = True
            elif data[i][0] == "-":
                for j in range(len(IKTableDemoList)):
                    if str(IKTableDemoList[j]["id"]) == str(rc["id"]):
                        del IKTableDemoList[j]
                        break
                updatedRmk = True
        if updatedRmk:
            return IkSccJsonResponse(message="Saved")
        else:
            return IkErrJsonResponse(message="No modification")
