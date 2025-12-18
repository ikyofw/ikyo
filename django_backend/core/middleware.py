import logging
from django.shortcuts import redirect

logger = logging.getLogger(__name__)


class Catch404Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if response.status_code == 403:
            logger.warning(
                "404 Forbidden: path=%s, method=%s, referer=%s",
                request.path,
                request.method,
                request.META.get("HTTP_REFERER", ""),
            )
            if request.path != "/error-page/":
                return redirect("/error-page/")
        if response.status_code == 404:
            logger.warning(
                "404 Not Found: path=%s, method=%s, referer=%s",
                request.path,
                request.method,
                request.META.get("HTTP_REFERER", ""),
            )
            if request.path != "/error-page/":
                return redirect("/error-page/")

        return response
