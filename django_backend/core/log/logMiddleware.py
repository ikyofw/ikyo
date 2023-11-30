import logging
import threading

try:
    from django.utils.deprecation import MiddlewareMixin  # Django 1.10.x
except ImportError:
    MiddlewareMixin = object  # Django 1.4.x - Django 1.9.x

local = threading.local()
SESSION_KEY_USER_NAME = 'USER_NAME'


class RequestLogFilter(logging.Filter):
    """
    Log filter, saves the request information of the current request thread to the log's record context. 
    The record carries the information needed by the formatter.
    """

    def filter(self, record):
        record.path = getattr(local, 'path', "none")
        record.username = getattr(local, 'username', "none")
        return True


class RequestLogMiddleware(MiddlewareMixin):
    """
    Getting the required information from request
    """

    def process_request(self, request):
        # Unified additional log content.
        local.path = request.path
        local.username = request.session.get(SESSION_KEY_USER_NAME, "system")
