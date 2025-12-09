from enum import Enum

import core.user.user_manager as UserManager2
from django.db import connection


class IkSession(Enum):
    KEY_USER_HAS_LOGIN = '__USER_HAS_LOGIN'
    KEY_USER_ID = '__CURRENT_USR_ID'


class UserManager:

    def GetCurrentUserId():
        return UserManager2.GUEST_USER_ID

    def GetUserId(request):  # TODO
        return UserManager.GetCurrentUserId()

    def HasLogin(request) -> bool:
        # b = request.session.get(IkSession.KEY_USER_HAS_LOGIN.value)
        # a = request.session.get(IkSession.KEY_USER_HAS_LOGIN.value, False)
        # return a
        return request.user is not None and request.auth is not None

    def Login(request, userId):
        request.session[IkSession.KEY_USER_HAS_LOGIN.value] = True
        request.session[IkSession.KEY_USER_ID.value] = userId

    def Logout(request):
        del request.session[IkSession.KEY_USER_HAS_LOGIN.value]
        del request.session[IkSession.KEY_USER_ID.value]

    def getUserName(usrId) -> str:
        with connection.cursor() as cursor:
            cursor.execute('select usr_nm from ik_usr where id=%s' % usrId)
            users = cursor.fetchall()
            if users is not None and len(users) > 0:
                return users[0]
        return None
