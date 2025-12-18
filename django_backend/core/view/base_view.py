import logging
from functools import wraps
from rest_framework.views import APIView
from ..core.http import IkErrJsonResponse
from ..core.exception import IkException


logger = logging.getLogger(__name__)


class BaseAPIView(APIView):

    @classmethod
    def as_view(cls, **initkwargs):
        original_view = super().as_view(**initkwargs)

        @wraps(original_view)
        def wrapped_view(request, *args, **kwargs):
            # handle the view class's __init__ method exception
            try:
                return original_view(request, *args, **kwargs)
            except Exception as exc:
                logger.exception("Error in %s: %s", cls.__name__, exc)
                if isinstance(exc, IkException):
                    return IkErrJsonResponse(message=str(exc))
                return IkErrJsonResponse(message="Internal error: {}".format(str(exc)))

        # Copy the original view’s csrf_exempt attribute onto the wrapped view.
        if hasattr(original_view, 'csrf_exempt'):
            wrapped_view.csrf_exempt = original_view.csrf_exempt

        return wrapped_view
