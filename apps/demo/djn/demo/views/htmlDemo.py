import random

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


htmlTestList = []
for i in range(3):
    htmlTestList.append({"id": str(i), "rmk": "test{}".format(random.randint(1, 5)), "html": "<div style=\"background-color: yellow;\">test</div>"})


class HtmlDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

        def beforeDisplayAdapter(screen):
            refresh = self.getSessionParameter('refresh')
            # if refresh:
            #     # screen.getField('tableHtml', 'rmk').visible = False
            #     self._addStaticResource('static/js/test.js')

        self.beforeDisplayAdapter = beforeDisplayAdapter

        # self._addStaticResource('static/js/test.js')

    def getHtmlHtmlComponent(self):
        f = './var/devdemo/htmlExample.html'
        with open(f, 'r', encoding='utf-8') as f:
            content = f.read()
        return IkSccJsonResponse(data=content)

    def getHtmlFg(self):
        for i in htmlTestList:
            i['html1'] = "<a href='mailto:dexiang.li@ywlgroup.com'>dexiang.li@ywlgroup.com</a>"
            i['html2'] = "<div style=\"background-color: yellow;\">test</div>"
        return IkSccJsonResponse(data=htmlTestList)

    def getDialogHtml(self):
        return IkSccJsonResponse(data="<div>test</div>")

    def showID(self):
        return IkSccJsonResponse(message="showID")

    def refresh(self):
        self.setSessionParameters({"refresh": "true"})
        return IkSccJsonResponse(message="Refreshed")
