"""
    The methods in __SessionManager are used for developing in port 3000.
"""
import inspect
import json
from pathlib import Path

from core.core.exception import IkException
from core.db.transaction import IkTransaction
from core.models import UsrSessionPrm, UsrToken
from django.contrib.sessions.backends.db import SessionStore
from django.core.handlers.wsgi import WSGIHandler
from rest_framework.views import APIView


class ObjectSerializer(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__


def dumps(obj) -> str:
    return json.dumps(obj, cls=ObjectSerializer)


def loads(objStr):
    return json.loads(objStr)


class __SessionManager:
    def __init__(self) -> None:
        pass

    def __getView(self) -> APIView:
        '''
            return django_backend.core.view.screenView.ScreenAPIView
        '''
        screenView = None
        stacks = inspect.stack()
        for stack in stacks:
            caller = stack.frame.f_locals.get('self', None)
            if caller is not None:
                if isinstance(caller, APIView):
                    screenView = caller
                    break
                elif isinstance(caller, WSGIHandler):
                    break
        if screenView is None:
            raise IkException('Unsupport session caller.')
        return screenView

    def __getSession(self) -> SessionStore:
        return self.__getView().request.session

    def getPrms(self, user, name, defaultValue=None):
        '''
            return object
        '''
        tokenRc = UsrToken.objects.filter(usr=user).first()
        if tokenRc is None:
            return None
        prmRc = UsrSessionPrm.objects.filter(token=tokenRc, key=name).first()
        v = prmRc.value if prmRc is not None else None
        return defaultValue if v is None else loads(v)

    def updatePrms(self, user, name, value):
        tokenRc = UsrToken.objects.filter(usr=user).first()
        if tokenRc is None:
            return None
        if isinstance(value, Path):
            value = str(value)
        return UsrSessionPrm.objects.update_or_create(token=tokenRc, key=name, defaults={'value': None if value is None else dumps(value)})

    def deletePrms(self, user, nameFilters) -> bool:
        '''
            user: mandatory

            nameFilter: str: "dog" / "*dog" / "*dog*" / "*dog" or a list
        '''
        if nameFilters is None or type(nameFilters) == list and len(nameFilters) == 0:
            return True
        if type(nameFilters) == str:
            nameFilters = [nameFilters]

        tokenRc = UsrToken.objects.filter(usr=user).first()
        if tokenRc is None:
            return True
        allRcs = []
        for nameFilter in nameFilters:
            rcs = None
            if '*' in nameFilter:
                if len(nameFilter) > 2 and nameFilter[0] == '*' and nameFilter[-1] == '*':
                    rcs = UsrSessionPrm.objects.filter(token=tokenRc, key__contains=nameFilter[1:-1])
                elif nameFilter[0] != '*' and nameFilter[-1] == '*':
                    # start with: __startswith
                    rcs = UsrSessionPrm.objects.filter(token=tokenRc, key__startswith=nameFilter[0:-1])
                elif nameFilter[-1] != '*' and nameFilter[0] == '*':
                    # end with: __endswith
                    rcs = UsrSessionPrm.objects.filter(token=tokenRc, key__endswith=nameFilter[1:])
                else:
                    rcs = UsrSessionPrm.objects.filter(token=tokenRc, key=nameFilter)
            else:
                rcs = UsrSessionPrm.objects.filter(token=tokenRc, key=nameFilter)
            if rcs is not None and len(rcs) > 0:
                allRcs.extend(rcs)
        if len(allRcs) == 0:
            return True
        ikTrn = IkTransaction()
        ikTrn.delete(allRcs)
        b = ikTrn.save()
        return b.value

    def getPrmAndDelete(self, user, name, defaultValue=None) -> str:
        v = self.getPrms(user, name, defaultValue)
        self.deletePrms(user, name)
        return v


SessionManager = __SessionManager()
