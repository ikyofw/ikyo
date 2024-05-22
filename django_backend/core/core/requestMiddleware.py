import threading
from django.utils.deprecation import MiddlewareMixin  # Django 1.10.x
from .http import isSupportSession
from core.models import User

_thread_locals = threading.local()

def getCurrentRequest():
    return getattr(_thread_locals, 'request', None)


def getCurrentUser() -> User:
    '''
        return core.models.User, None if not found
    '''
    request = getCurrentRequest()
    return request.user if request else request


class IkRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        return None

    def process_response(self, request, response):
        response.set_cookie('__SYS_SUPPORT_SESSION__', 'session' if isSupportSession(request) else 'token')
        return response

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request
        response = self.get_response(request)
        return response