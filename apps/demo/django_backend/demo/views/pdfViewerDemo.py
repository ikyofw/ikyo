import random
from pathlib import Path

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView
from core.core.http import responseFile
import core.core.fs as ikfs

from .baseViews import devDemoGetRequestData


PDFViewerTestList = []
for i in range(10):
    PDFViewerTestList.append({"a": str(i), "b": "test{}".format(random.randint(1, 5)),
                             "c": "test{}".format(random.randint(1, 5)), "d": "test{}".format(random.randint(1, 5))})


class PDFViewerDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen):
            screen.classNm = {'display': 'grid', 'grid-template-columns': '1fr 1fr', 'grid-template-rows': 'auto', 'grid-gap': '5px'}
            screen.getFieldGroup('PDFViewer').classNm = {'grid-area': '1 / 1 / 3 / 2'}
            screen.getFieldGroup('Table1').classNm = {'grid-area': '1 / 2 / 2 / 3'}

        self.beforeDisplayAdapter = beforeDisplayAdapter

    def getTestRcs(self):
        return IkSccJsonResponse(data=PDFViewerTestList)

    def getPDFViewer(self):
        filePath = Path(ikfs.getRootFolder(), 'var/demo-files/PDFViewerDemo.pdf')
        if not Path(filePath).exists():
            return IkErrJsonResponse(message="File does not exist.")
        return responseFile(filePath)
