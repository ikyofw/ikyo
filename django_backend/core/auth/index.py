import hashlib
import time
import traceback
import importlib

from django.http import QueryDict
from django.contrib.auth.hashers import check_password

import core.utils.strUtils as strUtils
from core.core.code import IkCode
from core.core.exception import IkException
from core.core.http import IkErrJsonResponse, IkSccJsonResponse, IkSysErrJsonResponse, isSupportSession
from core.core.lang import Boolean2
from core.log.logger import logger
from core.utils.encrypt import decryptData, generateRsaKeys, getPublicKey
from core.utils.langUtils import isNullBlank
from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication
from rest_framework.views import APIView
from rest_framework.request import Request
from iktools import IkConfig
from core.models import User, UsrToken


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
    if isSupportSession(request):
        # access to django directly. e.g. http://localhost:8000 (build react)
        sessionID = request.session.session_key
        if strUtils.isEmpty(sessionID):
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
    if isSupportSession(request):
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
        useSession = isSupportSession(request)
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
        try:
            sessionID = getSessionID(request)
            useSession = isSupportSession(request)
            # YL.ikyo, 2022-10-21 login username & password RSA decryption - start
            _username = request._request.POST.get("username", "")
            _password = request._request.POST.get("password", "")
            username = decryptData(_username)
            password = decryptData(_password)
            # YL.ikyo, 2022-10-21 - end

            try:
                usrRc = User.objects.filter(usr_nm=username).first()
                if usrRc is None:
                    return Boolean2(False, 'User is not found.').toIkJsonResponse1()
                if not usrRc.active:
                    return Boolean2(False, 'This user has been disabled.').toIkJsonResponse1()

                password_matches = False
                password_encryption_method = IkConfig.getSystem('password_encryption_method').lower()
                if password_encryption_method == 'md5':
                    encrypted_password = hashlib.md5(password.encode("utf8")).hexdigest()
                    password_matches = encrypted_password == usrRc.psw
                elif password_encryption_method == 'pbkdf2':
                    password_matches = check_password(password, usrRc.psw)
                else:
                    password_matches = check_password(password, usrRc.psw)  # The default encryption method is PBKDF2.
                if not password_matches:
                    return Boolean2(False, 'Password is incorrect.').toIkJsonResponse1()
                
                for amdd in _AUTH_MIDDLEWARES:
                    try:
                        middleware_instance = __create_authorization_middleware_instance() if isinstance(amdd, str) else amdd
                        middleware_instance : AuthorizationMiddleware # for vs code
                        amdd_result = middleware_instance.pre_authenticate(request, usrRc)
                        if amdd_result is not None and not amdd_result.value:
                            logger.error("User [%s], [%s], pre_authenticate failed: %s", username, str(middleware_instance), amdd_result.dataStr)
                            return amdd_result.toIkJsonResponse1()
                        else:
                            logger.debug("User [%s], [%s], pre_authenticate complete: %s", username, str(middleware_instance), (amdd_result.dataStr if amdd_result is not None else ''))
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
                        middleware_instance = __create_authorization_middleware_instance() if isinstance(amdd, str) else amdd
                        middleware_instance : AuthorizationMiddleware # for vs code
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
                        middleware_instance = __create_authorization_middleware_instance() if isinstance(amdd, str) else amdd
                        middleware_instance : AuthorizationMiddleware # for vs code
                        amdd_result = middleware_instance.handle_authentication_failure(request, usrRc)
                        if amdd_result is not None and not amdd_result.value:
                            logger.error("[%s], handle_authentication_failure failed: %s", str(middleware_instance), amdd_result.dataStr)
                        else:
                            logger.debug("[%s], handle_authentication_failure complete: %s", str(middleware_instance), (amdd_result.dataStr if amdd_result is not None else ''))
                    except Exception as e:
                        logger.error("[%s], handle_authentication_failure exception: %s", str(middleware_instance), str(e), exc_info=True)

    def delete(self, request):
        try:
            isUseSession = isSupportSession(request)
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
                        middleware_instance : AuthorizationMiddleware # for vs code
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