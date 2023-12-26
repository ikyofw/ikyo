import random

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


class SearchFgDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def getSchFg(self):
        schItems = self.getSessionParameter('schItems')
        return IkSccJsonResponse(data=schItems)

    def getCombo(self):
        data = [{'nm': 'option 1'}, {'nm': 'option 2'}]
        return IkSccJsonResponse(data=data)

    # def search(self):
    #     requestData = self.getRequestData()
    #     schItems = requestData.get('searchFg')
    #     self.setSessionParameters({'schItems': schItems})
    #     return IkSccJsonResponse()

    def search(self):
        requestData = self.getRequestData()
        schItems = requestData.get('searchFg')
        style = [
            {
                'col': 'text',
                'style': {
                    'backgroundColor': '#66CCFF'
                }
            },
        ]
        return self._returnQueryResult('showFg', [schItems], style=style)

    def getShowFg(self):
        schItems = self.getSessionParameter('schItems')
        data = [schItems] if schItems else []
        return IkSccJsonResponse(data=data)

    def clearSearchFg(self):
        return self.deleteSessionParameters('schItems')
