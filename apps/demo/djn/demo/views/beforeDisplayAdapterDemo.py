import random

from core.core.http import IkErrJsonResponse, IkSccJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData

beforeDisplayAdapterDemoList = []
for i in range(10):
    beforeDisplayAdapterDemoList.append({"id": str(i), "rmk1": "test{}".format(random.randint(1, 5)), "rmk2": "test{}".format(random.randint(1, 5))})


class BeforeDisplayAdapterDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen):
            if screen.getFieldGroup('outputFg').visible:
                func = "function xxx(tableDat, rowData, rowIndex, columnIndex, cell){\n"
                func += "if ((rowIndex === 2 && columnIndex === 3) || (rowIndex === 8 && columnIndex === 0)) {cell.innerHTML = ''}\n"
                func += "const value = cell.querySelector('span') ? cell.querySelector('span').innerHTML : ''\n"
                func += "if (value.indexOf('t2') !== -1) {cell.style.background = '#A0C32D'}"
                func += "};"
                screen.getFieldGroup('outputFg').beforeDisplayAdapter = func

        self.beforeDisplayAdapter = beforeDisplayAdapter

    def getClockins(self):
        return IkSccJsonResponse(data=beforeDisplayAdapterDemoList)
