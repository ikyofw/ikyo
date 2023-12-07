"""Example Table Header/Footer defined in spreadsheets.

Author:
    Li

Date:
    2023-02-06

"""

from core.db.model import DummyModel
from core.core.lang import Boolean2
from core.view.screenView import ScreenAPIView


class TableHeaderFooterDemo(ScreenAPIView):
    '''
        http://localhost:8000/IkTableHeaderFooterDemo
    '''

    def getTableDataRcs(self):
        # return DummyModel record list
        rcs = self.getSessionParameter('data', delete=True)
        if rcs is not None:
            return rcs

        rcs = []
        for i in range(1, 5):
            rc = DummyModel()
            for j in range(1, 10):
                rc['f%s' % j] = i * 100 + j  # 101, 102 ... 201, 202 ...
            rc.ik_set_status_retrieve()
            rcs.append(rc)
        return rcs
