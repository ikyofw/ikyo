import logging

from django.db.models import OuterRef, Prefetch, Subquery

import core.ui.ui_db as ikuidb
from core.core.http import *
from core.db.transaction import IkTransaction
from core.models import *
from core.utils.lang_utils import isNotNullBlank, isNullBlank
from core.view.screen_view import ScreenAPIView

logger = logging.getLogger('ikyo')


class AppMntView(ScreenAPIView):

    def __init__(self) -> None:
        super().__init__()

    # override
    def beforeInitScreenData(self, screen) -> None:
        super().beforeInitScreenData(screen)
        screen_selection_fg = self.getSessionParameter('screen_selection_fg')
        show_save_btt = isNotNullBlank(screen_selection_fg) and isNotNullBlank(screen_selection_fg['app_nm'])

        screen.setFieldGroupsVisible(fieldGroupNames=['appFg', 'actionBar'], visible=show_save_btt)

    def getApps(self):
        # get all last rev screens
        latest = Screen.objects.filter(screen_sn=OuterRef('screen_sn')).order_by('-rev').values('id')[:1]
        qs = Screen.objects.filter(id__in=Subquery(latest))

        # get app names
        app_nms = qs.exclude(app_nm__isnull=True).exclude(app_nm='').values_list('app_nm', flat=True).distinct().order_by('app_nm')
        return IkSccJsonResponse(data=app_nms)

    # get all screens combobox
    def getScreens(self):
        screen_selection_fg = self.getSessionParameter('screen_selection_fg')
        data = []
        if isNotNullBlank(screen_selection_fg) and isNotNullBlank(screen_selection_fg['app_nm']):
            app_nm = screen_selection_fg['app_nm']
            subquery = Screen.objects.filter(screen_sn=OuterRef('screen_sn')).order_by('-rev').values('id')[:1]
            screen_rcs = Screen.objects.filter(id__in=Subquery(subquery))
            screen_rcs = screen_rcs.filter(app_nm=app_nm).order_by('screen_sn')
            for screen_rc in screen_rcs:
                data.append({'screen_sn': screen_rc.screen_sn})
        return data

    # get selected screen
    def getScreenSelectRc(self):
        return IkSccJsonResponse(data=self.getSessionParameter("screen_selection_fg"))

    def changeApp(self):
        screen_selection_fg = self.getRequestData().get('screenSelectionFg', None)
        return self.setSessionParameters({'screen_selection_fg': screen_selection_fg})

    # screenSelectFg change event
    def changeScreen(self):
        screen_selection_fg = self.getRequestData().get('screenSelectionFg', None)
        return self.setSessionParameters({'screen_selection_fg': screen_selection_fg})

    def getScreenRcs(self):
        screen_selection_fg = self.getSessionParameter('screen_selection_fg')
        data = []
        if isNotNullBlank(screen_selection_fg):
            if isNotNullBlank(screen_selection_fg['screen_sn']):
                screen_sn = screen_selection_fg['screen_sn']
                screen_rc = Screen.objects.filter(screen_sn=screen_sn).order_by('-rev').first()
                file_dt = ScreenFile.objects.filter(screen=screen_rc).order_by('-file_dt').first().file_dt
                data.append({'screen_sn': screen_rc.screen_sn, 'screen_title': screen_rc.screen_title, 'rev': screen_rc.rev, 'file_dt': file_dt})
            elif isNotNullBlank(screen_selection_fg['app_nm']):
                app_nm = screen_selection_fg['app_nm']
                subquery = Screen.objects.filter(screen_sn=OuterRef('screen_sn')).order_by('-rev').values('id')[:1]
                screen_rcs = Screen.objects.filter(id__in=Subquery(subquery))
                screen_rcs = screen_rcs.filter(app_nm=app_nm).order_by('screen_sn')

                # Pre-fetch the latest ScreenFile for each Screen
                screen_file_rcs = ScreenFile.objects.filter(screen__in=screen_rcs).order_by('screen', '-file_dt')
                # Use Prefetch to fetch related ScreenFile objects into Screen objects
                screen_rcs = screen_rcs.prefetch_related(Prefetch('screenfile_set', queryset=screen_file_rcs, to_attr='screen_files'))

                for screen_rc in screen_rcs:
                    if len(screen_rc.screen_files) == 1:
                        screen_file_rc = screen_rc.screen_files[0]
                    elif len(screen_rc.screen_files) > 1:
                        screen_file_rc = sorted(screen_rc.screen_files, key=lambda x: x.file_dt, reverse=True)[0]
                    else:
                        screen_file_rc = None
                    if isNullBlank(screen_file_rc):
                        file_dt = ''
                    else:
                        file_dt = screen_file_rc.file_dt.strftime('%Y-%m-%d %H:%M:%S')
                    data.append({'screen_sn': screen_rc.screen_sn, 'screen_title': screen_rc.screen_title, 'rev': screen_rc.rev, 'file_dt': file_dt})
        return data

    def save(self):
        screen_selection_fg = self.getSessionParameter('screen_selection_fg')
        request_data = self.getRequestData()
        new_app_nm = request_data.get("appFg", {}).get("appField", None)
        screen_fg = request_data.get("screenFg", None)
        self.setSessionParameters({"screen_selection_fg": {"app_nm": new_app_nm, "screen_sn": None}})

        if isNullBlank(screen_selection_fg):
            return IkErrJsonResponse(message="Please select a app or screen.")
        if isNullBlank(new_app_nm):
            return IkErrJsonResponse(message="Please set the new app name.")

        pre_app_nm = screen_selection_fg['app_nm']
        screen_sn = screen_selection_fg['screen_sn']
        if isNotNullBlank(pre_app_nm):
            if isNotNullBlank(screen_sn):
                self.__changeAppName(screen_sn, pre_app_nm, new_app_nm)
                return IkSccJsonResponse(message="Screen [%s] app name change from [%s] to [%s]. Please ensure corresponding backend code for this screen is updated."
                                         % (screen_sn, pre_app_nm, new_app_nm))
            else:
                screen_sns = []
                for screen in screen_fg:
                    screen_sns.append(screen['screen_sn'])
                    self.__changeAppName(screen['screen_sn'], pre_app_nm, new_app_nm)
                return IkSccJsonResponse(message="Screen %s app name change from [%s] to [%s]. Please ensure corresponding backend code for these screens is updated."
                                         % (screen_sns, pre_app_nm, new_app_nm))

    def __changeAppName(self, screen_sn, pre_app_nm, new_app_nm):
        screen_rc = Screen.objects.filter(screen_sn=screen_sn).order_by('-rev').first()
        screen_file_rcs = ScreenFile.objects.filter(screen=screen_rc).order_by('-file_dt')
        recordset_rcs = ScreenRecordset.objects.filter(screen=screen_rc)

        screen_rc.app_nm = new_app_nm
        screen_rc.class_nm = screen_rc.class_nm.replace(pre_app_nm, new_app_nm.lower())
        screen_rc.ik_set_status_modified()

        for recordset_rc in recordset_rcs:
            recordset_rc.sql_models = recordset_rc.sql_models.replace(pre_app_nm, new_app_nm.lower())
            recordset_rc.ik_set_status_modified()

        ptrn = IkTransaction()
        ptrn.add(screen_rc)
        ptrn.add(recordset_rcs)
        c = ptrn.save()
        if not c.value:
            raise c.dataStr
        if len(screen_file_rcs) > 0:
            ikuidb._deleteExcelAndCSV(screen_file_rcs[0])

        b = ikuidb.screenDbWriteToExcel(screen_rc, 'Saved on App Management')
        if not b.value:
            return b
