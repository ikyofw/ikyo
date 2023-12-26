import random

from core.core.http import IkSccJsonResponse, IkErrJsonResponse
from core.view.screenView import ScreenAPIView

from .baseViews import devDemoGetRequestData


tableStyleTestList = []
for i in range(10):
    tableStyleTestList.append({"id": str(i), "rmk1": "test{}".format(random.randint(1, 5)), "rmk2": "test{}".format(random.randint(1, 5))})


class TableStyleDemo(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def getClockins(self):
        style = [
            {
                'row': 1,
                'col': 'id',
                'style': {
                    'fontWeight': 'bold',
                }
            },
            {
                'row': 3,
                'col': 'rmk2',
                'style': {
                    'text-align': 'right'
                },
                'class': 'testCSS1, testCSS2'
            },
            {
                'row': 5,
                'style': {
                    'height': '50px'
                }
            },
            {
                'col': 'rmk2',
                'style': {
                    'backgroundColor': '#66CCFF'
                }
            },
            {
                'row': 12,
                'col': 'id',
                'style': {
                    'backgroundColor': '#66CCFF'
                }
            },
            {
                'row': 12,
                'style': {
                    'backgroundColor': '#66CCFF'
                }
            },
            {
                'col': 'RMK3',
                'style': {
                    'backgroundColor': '#66CCFF'
                }
            },
        ]
        return IkSccJsonResponse(data={'outputFg': tableStyleTestList, 'style': style})

    # def _getClockinsTableDataStyle(self):
    #     style = [
    #                 {'row': 1, 'col': 'id', 'style': {'backgroundColor': '#66CCFF'}},
    #                 {'row': 3, 'col': 'rmk2', 'style': {'text-align': 'right'}, 'class': 'testCSS1, testCSS2'},
    #                 {'row': 5, 'style': {'height': '50px'}},
    #                 {'col': 'rmk2', 'style': {'fontWeight': 'bold'}},
    #                 {'row': 12, 'col': 'id', 'style': {'backgroundColor': '#66CCFF'}},
    #                 {'row': 12, 'style': {'backgroundColor': '#66CCFF'}},
    #                 {'col': 'RMK3', 'style': {'backgroundColor': '#66CCFF'}},
    #             ]
    #     return IkSccJsonResponse(data=style)

    # def _getClockinsTableDataStyle(self):
    #     style = [
    #                 {'style': {'fontWeight': 'bold'}}
    #             ]
    #     return IkSccJsonResponse(data=style)
