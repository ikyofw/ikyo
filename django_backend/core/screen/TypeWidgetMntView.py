'''
Description: Field Group Type and Field Widget Management
version: 
Author: XH
Date: 2023-07-12 16:16:21
'''
import core.ui.ui as ikui
from core.core.http import IkSccJsonResponse
from core.db.transaction import IkTransaction
from core.utils.langUtils import isNullBlank, isNotNullBlank
from core.models import ScreenFgType, ScreenFieldWidget
from core.view.screenView import ScreenAPIView

from core.ui import uiCache as ikuiCache


class TypeWidgetMntView(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    def getSystemFgTypeRcs(self):
        sysTypeList = ikui.SCREEN_FIELD_NORMAL_GROUP_TYPES
        typeRcs = ScreenFgType.objects.filter(type_nm__in=sysTypeList).order_by('type_nm')
        return IkSccJsonResponse(data=typeRcs)

    def getCustomFgTypeRcs(self):
        sysTypeList = ikui.SCREEN_FIELD_NORMAL_GROUP_TYPES
        typeRcs = ScreenFgType.objects.exclude(type_nm__in=sysTypeList).order_by('type_nm')
        return IkSccJsonResponse(data=typeRcs)

    def saveFgType(self):
        customFgTypeFg = self.getRequestData().get('customFgTypeFg', None)
        ptrn = IkTransaction(self)
        if isNotNullBlank(customFgTypeFg):
            ptrn.add(customFgTypeFg)
        b = ptrn.save()
        if b.value:
            ikuiCache.setFieldGroupTypeCache()
        return b.toIkJsonResponse1()

    def getSystemFieldWidgetRcs(self):
        sysWidgetList = ikui.SCREEN_FIELD_NORMAL_WIDGETS
        typeRcs = ScreenFieldWidget.objects.filter(widget_nm__in=sysWidgetList).order_by('widget_nm')
        return IkSccJsonResponse(data=typeRcs)

    def getCustomFieldWidgetRcs(self):
        sysWidgetList = ikui.SCREEN_FIELD_NORMAL_WIDGETS
        typeRcs = ScreenFieldWidget.objects.exclude(widget_nm__in=sysWidgetList).order_by('widget_nm')
        return IkSccJsonResponse(data=typeRcs)

    def saveWidget(self):
        customFieldWidgetFg = self.getRequestData().get('customFieldWidgetFg', None)
        ptrn = IkTransaction(self)
        if isNotNullBlank(customFieldWidgetFg):
            ptrn.add(customFieldWidgetFg)
        b = ptrn.save()
        if b.value:
            ikuiCache.setFieldWidgetCache()
        return b.toIkJsonResponse1()