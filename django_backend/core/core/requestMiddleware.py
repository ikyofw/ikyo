from django.utils.deprecation import MiddlewareMixin  # Django 1.10.x

from .http import isSupportSession


class IkRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        return None

    def process_response(self, request, response):
        response.set_cookie('__SYS_SUPPORT_SESSION__', 'session' if isSupportSession(request) else 'token')
        return response
