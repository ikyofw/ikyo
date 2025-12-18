import hashlib
import importlib
import time
import traceback
import logging

from django.contrib.auth.hashers import check_password
from django.http import QueryDict
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.request import Request
from rest_framework.views import APIView

import core.utils.str_utils as str_utils
from core.core.code import IkCode
from core.core.exception import IkException
from core.core.http import (IkErrJsonResponse, IkSccJsonResponse,
                            IkSysErrJsonResponse, is_support_session)
from core.core.lang import Boolean2
from core.log.logger import logger
from core.models import User, UsrToken
from core.utils.encrypt import decryptData, generateRsaKeys, getPublicKey
from core.utils.lang_utils import isNullBlank
from iktools import IkConfig

SESSION_KEY_USER_NAME = 'USER_NAME'
_AUTH_MIDDLEWARES = []


class AuthorizationMiddleware:
    """
    Middleware class for handling HTTP request authorization flow.

    This middleware provides complete authorization lifecycle management,
    including pre-authentication processing, handling of successful and
    failed authentication, and authentication removal.
    """

    def __init__(self):
        """
        Initialize the authorization middleware.
        """

    def pre_authenticate(self, request: Request, current_user: User) -> Boolean2:
        """
        Execute pre-processing operations before authentication verification.

        Args:
            request: The HTTP request object
            current_user: The currently authenticated user

        Returns:
            Boolean2: Pre-processing result, True to continue the authentication flow,
                     False to terminate
        """
        pass

    def handle_authentication_success(self, request: Request, current_user: User) -> Boolean2:
        """
        Handle successful authentication cases.

        Args:
            request: The successfully authenticated HTTP request object
            current_user: The currently authenticated user

        Returns:
            Boolean2: Processing result, True for successful handling,
                     False for handling failure
        """
        pass

    def handle_authentication_failure(self, request: Request, current_user: User) -> Boolean2:
        """
        Handle failed authentication cases.

        Args:
            request: The HTTP request object that failed authentication
            current_user: The currently authenticated user

        Returns:
            Boolean2: Processing result, True for successful handling,
                     False for handling failure
        """
        pass

    def remove_authentication(self, request: Request, current_user: User) -> Boolean2:
        """
        Removes authentication information from the request (logout operation).

        Args:
            request: The HTTP request object requiring authentication removal
            current_user: The currently authenticated user

        Returns:
            Boolean2: True if authentication was successfully removed, False otherwise
        """
        """
        Remove authentication information from the request (e.g., logout operation).
        
        Args:
            request: The HTTP request object requiring authentication removal
            
        Returns:
            Boolean2: Operation result, True for successful removal,
                     False for removal failure
        """
        pass


def add_auth_middleware(middleware):
    """
    Add a middleware to the AUTH_MIDDLEWARES list.

    Args:
        middleware: An instance of AuthorizationMiddleware or a class name string
    """
    if isinstance(middleware, str):
        _AUTH_MIDDLEWARES.append(middleware)
    elif isinstance(middleware, AuthorizationMiddleware):
        _AUTH_MIDDLEWARES.append(middleware)
    else:
        raise ValueError("Middleware must be an instance of AuthorizationMiddleware or a class name string.")


def get_auth_middlewares():
    """
    Get a copy of the AUTH_MIDDLEWARES list.

    Returns:
        list: A copy of AUTH_MIDDLEWARES
    """
    return _AUTH_MIDDLEWARES.copy()


def clear_auth_middlewares():
    """
    Clear the AUTH_MIDDLEWARES list.
    """
    _AUTH_MIDDLEWARES.clear()


def getUser(request) -> User:
    try:
        return request.user
    except:
        return None


def hasLogin(request) -> bool:
    return getUser(request) is not None


def getRequestToken(request) -> str:
    token = request._request.GET.get('token', None)
    if token is None:
        prms = QueryDict(request.body)
        token = prms.get('token', None)
        if token is None:
            token = request.headers.get('Token', None)
    return token


def getSessionKey(request) -> str:
    if is_support_session(request):
        # access to django directly. e.g. http://localhost:8000 (build react)
        sessionID = request.session.session_key
        if str_utils.isEmpty(sessionID):
            appName = request.POST.get('appName', None)
        return sessionID
    else:
        # use tooken instead. e.g. access api via react: http://localhost:3000
        token = getRequestToken(request)
        return token


def md5(user):
    ctime = str(time.time())
    m = hashlib.md5(bytes(str(user), encoding="utf-8"))
    m.update(bytes(ctime, encoding="utf-8"))
    return m.hexdigest()


class BasicValidationResult():
    def __init__(self, username: str, success: bool, message: str, user_rc: User = None) -> None:
        self.username = username
        self.success = success
        self.message = message
        self.user_rc = user_rc

    def __repr__(self):
        return f"BasicValidationResult(username={self.username}, success={self.success}, message={self.message})"


def basic_validation(username: str, password: str, is_encrypted: bool = True) -> BasicValidationResult:
    input_username = username
    input_password = password
    try:
        if username is None or username == '':
            return BasicValidationResult(username=input_username, success=False, message='Username cannot be empty.')

        if is_encrypted:
            try:
                username = decryptData(username)
            except:
                logging.error(f"Username decryption failed. username=[{username}]")
                return BasicValidationResult(username=input_username, success=False, message='Username decryption failed.')
            if password is not None and password != '':
                try:
                    password = decryptData(password)
                except:
                    logging.error(f"Password decryption failed. password=[{password}]")
                    return BasicValidationResult(username=username, success=False, message='Password decryption failed.')

        # validate user
        user_rc = User.objects.filter(usr_nm=username).first()
        if user_rc is None:
            return BasicValidationResult(username=username, success=False, message='User does not exist.')
        if not user_rc.active:
            return BasicValidationResult(username=username, success=False, message='This user has been disabled.')
        
        # validate password
        db_password = user_rc.psw
        if not ((password is None or password == '') and (db_password is None or db_password == '')):
            password_encryption_method = IkConfig.getSystem('password_encryption_method').lower()
            if password_encryption_method == 'md5':
                encrypted_password = hashlib.md5(password.encode("utf8")).hexdigest()
                password_matches = (encrypted_password == db_password)
            elif password_encryption_method == 'pbkdf2':
                password_matches = check_password(password, db_password)
            else:
                # default PBKDF2
                password_matches = check_password(password, db_password)
            if not password_matches:
                return BasicValidationResult(username=username, success=False, message='Password is incorrect.')

        return BasicValidationResult(username=username, success=True, message='Validated', user_rc=user_rc)
    except Exception as e:
        logging.exception(f"author_user exception. username=[{input_username}], password=[{input_password}]")
        return BasicValidationResult(username=username, success=False, message='System error.')


def cleanSession(request) -> None:
    request.session.flush()


def _getSessionUser(request):
    token = None
    try:
        token = getSessionKey(request)
    except:
        pass
    if token is None:
        logger.debug('Token is empty. Url=%s' % request.get_full_path())
        raise exceptions.AuthenticationFailed(IkErrJsonResponse(code=IkCode.E10001, message='Please login first.').toJson())
    tokenRc = UsrToken.objects.filter(token=token).first()
    if tokenRc is None:
        logger.debug('Token [%s] is not found.' % token)
        raise exceptions.AuthenticationFailed(IkErrJsonResponse(code=IkCode.E10001, message='Please login first.').toJson())

    usrRc = None
    if is_support_session(request):
        username = request.session.get(SESSION_KEY_USER_NAME, None)
        if username is None:
            logger.debug('Token is empty. Url=%s' % request.get_full_path())
            raise exceptions.AuthenticationFailed(IkErrJsonResponse(code=IkCode.E10001, message='Please login first.').toJson())
        usrRc = User.objects.filter(usr_nm=username).first()
        if usrRc is None:
            logger.debug('Token is empty. Url=%s, user=%s' % (request.get_full_path(), username))
            raise exceptions.AuthenticationFailed(IkErrJsonResponse(code=IkCode.E10001, message='Please login first.').toJson())
    else:
        usrRc = tokenRc.usr
    return (usrRc, tokenRc)


def getSessionID(request) -> str:
    sessionID = None
    try:
        sessionID = request.session.session_key
        useSession = is_support_session(request)
        appName = request.POST.get('appName', None)
        if useSession and sessionID is None:
            request.session.create()
            sessionID = request.session.session_key
    except:
        pass
    return sessionID


class AuthView(APIView):
    def get(self, request):
        '''
            used for home page to validate the session
        '''
        try:
            usrRc, tokenRc = _getSessionUser(request)
            # YL.ikyo, 2022-08-23 for react check login.
            return IkSccJsonResponse(code=IkCode.I1, message='Login already.', data={'user': usrRc.usr_nm, 'token': tokenRc.token})
        except Exception as e:
            print(str(e))
            if isinstance(e, exceptions.AuthenticationFailed):
                logger.error(str(e))
            else:
                logger.error(e, exc_info=True)
            # public_key = RSA_PUBLIC_KEY
            public_key = getPublicKey()
            if public_key is None:
                generateRsaKeys()
                public_key = getPublicKey()
            return IkErrJsonResponse(code=IkCode.E10001, message='Please login first.', data={'RSA_PUBLIC_KEY': public_key})

    def post(self, request):
        is_auth_success = False
        usrRc = None
        try:
            sessionID = getSessionID(request)
            useSession = is_support_session(request)

            _username = request._request.POST.get("username", "")
            _password = request._request.POST.get("password", "")

            validate_result = basic_validation(_username, _password, True)
            if not validate_result.success:
                return Boolean2.FALSE(data=validate_result.message)
            username = validate_result.username
            usrRc = validate_result.user_rc

            try:
                for amdd in _AUTH_MIDDLEWARES:
                    try:
                        middleware_instance = __create_authorization_middleware_instance(amdd) if isinstance(amdd, str) else amdd
                        middleware_instance: AuthorizationMiddleware  # for vs code
                        amdd_result = middleware_instance.pre_authenticate(request, usrRc)
                        if amdd_result is not None and not amdd_result.value:
                            logger.error("User [%s], [%s], pre_authenticate failed: %s", username, str(middleware_instance), amdd_result.dataStr)
                            return amdd_result.toIkJsonResponse1()
                        else:
                            logger.debug("User [%s], [%s], pre_authenticate complete: %s", username, str(
                                middleware_instance), (amdd_result.dataStr if amdd_result is not None else ''))
                    except Exception as e:
                        logger.error("User [%s], [%s], pre_authenticate exception: %s", username, str(middleware_instance), str(e), exc_info=True)
                        return Boolean2.FALSE("Auth middleware exception.")

                tokenStr = md5(usrRc) if sessionID is None else sessionID
                # check the token is in use or not
                oldRc = UsrToken.objects.filter(token=tokenStr).first()
                if oldRc is not None:
                    oldRc.delete()
                UsrToken.objects.update_or_create(usr_id=usrRc.id, defaults={"token": tokenStr})

                if useSession:
                    request.session[SESSION_KEY_USER_NAME] = username

                for amdd in _AUTH_MIDDLEWARES:
                    try:
                        middleware_instance = __create_authorization_middleware_instance(amdd) if isinstance(amdd, str) else amdd
                        middleware_instance: AuthorizationMiddleware  # for vs code
                        amdd_result = middleware_instance.handle_authentication_success(request, usrRc)
                        if amdd_result is not None and not amdd_result.value:
                            logger.error("[%s], handle_authentication_success failed: %s", str(middleware_instance), amdd_result.dataStr)
                        else:
                            logger.debug("[%s], handle_authentication_success complete: %s", str(middleware_instance), (amdd_result.dataStr if amdd_result is not None else ''))
                    except Exception as e:
                        logger.error("[%s], handle_authentication_success exception: %s", str(middleware_instance), str(e), exc_info=True)

                is_auth_success = True
                return IkSccJsonResponse(message='success', data={'token': tokenStr})
            except User.DoesNotExist:
                return IkErrJsonResponse(message='User or password is incorrect.')
        except IkException as pe:
            traceback.print_exc()
            return IkErrJsonResponse(message=str(pe))
        except Exception as e:
            traceback.print_exc()
            return IkSysErrJsonResponse(message=str(e))
        finally:
            if not is_auth_success:
                for amdd in _AUTH_MIDDLEWARES:
                    try:
                        middleware_instance = __create_authorization_middleware_instance(amdd) if isinstance(amdd, str) else amdd
                        middleware_instance: AuthorizationMiddleware  # for vs code
                        amdd_result = middleware_instance.handle_authentication_failure(request, usrRc)
                        if amdd_result is not None and not amdd_result.value:
                            logger.error("[%s], handle_authentication_failure failed: %s", str(middleware_instance), amdd_result.dataStr)
                        else:
                            logger.debug("[%s], handle_authentication_failure complete: %s", str(middleware_instance), (amdd_result.dataStr if amdd_result is not None else ''))
                    except Exception as e:
                        logger.error("[%s], handle_authentication_failure exception: %s", str(middleware_instance), str(e), exc_info=True)

    def delete(self, request):
        try:
            isUseSession = is_support_session(request)
            token = getRequestToken(request)
            if isUseSession and request.session.has_key(SESSION_KEY_USER_NAME):
                cleanSession(request)
                return IkSccJsonResponse(message='logout')
            if isNullBlank(token):
                return IkErrJsonResponse(message='Token is required.')
            tokenRc = UsrToken.objects.filter(token=token).first()
            if tokenRc is None:
                if not isUseSession:
                    return IkErrJsonResponse(message='Token is incorrect.')
                return IkSccJsonResponse(message='logout')
            else:
                tokenRc.delete()

                for amdd in _AUTH_MIDDLEWARES:
                    try:
                        middleware_instance = __create_authorization_middleware_instance() if isinstance(amdd, str) else amdd
                        middleware_instance: AuthorizationMiddleware  # for vs code
                        amdd_result = middleware_instance.remove_authentication(request, UsrToken.usr)
                        if amdd_result is not None and not amdd_result.value:
                            logger.error("[%s], remove_authentication failed: %s", str(middleware_instance), amdd_result.dataStr)
                        else:
                            logger.debug("[%s], remove_authentication complete: %s", str(middleware_instance), (amdd_result.dataStr if amdd_result is not None else ''))
                    except Exception as e:
                        logger.error("[%s], remove_authentication exception: %s", str(middleware_instance), str(e), exc_info=True)

                return IkSccJsonResponse(message='logout')
        except IkException as pe:
            traceback.print_exc()
            return IkErrJsonResponse(message=str(pe))
        except Exception as e:
            traceback.print_exc()
            return IkSysErrJsonResponse(message=str(e))


class Authentication(BaseAuthentication):
    def authenticate(self, request):
        usrRc, tokenRc = _getSessionUser(request)
        return (usrRc, tokenRc)

    def authenticate_header(self, request):
        path = requestUrl = request.get_full_path()  # /api/ ....
        usrId = None if request.user is None else request.user.id
        menuId = None  # TODO:

# Access rights control


class UserPermission(object):
    def has_permission(self, request, view):
        # print('UserPermission check: ' + request.user.usr_nm)
        return request.user is not None


def __create_authorization_middleware_instance(class_full_name) -> AuthorizationMiddleware:
    # Split the module and class name
    module_name, class_name = class_full_name.rsplit('.', 1)
    # Import the module
    module = importlib.import_module(module_name)
    # Get the class
    middleware_class = getattr(module, class_name)
    # Instantiate the class
    middleware_instance = middleware_class()
    return middleware_instance
