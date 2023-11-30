import random
import traceback
import json

import core.core.fs as fs
from core.core.lang import *
from core.core.http import IkSccJsonResponse
from core.core.http import *

from core.utils import templateManager

from core.view.screenView import ScreenAPIView


def devDemoGetRequestData(request) -> IkRequestData:
    data0 = {}
    try:
        requestBodyStr = request.body.decode()
        data0 = json.loads(requestBodyStr)
    except Exception as e:
        for key, value in request.data.items():
            data0[key] = value
    data = IkRequestData()
    data.setRequest(request)
    for key, value in data0.items():
        data[key] = value
    return data
