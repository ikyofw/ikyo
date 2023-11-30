from core.core.http import IkSccJsonResponse
from rest_framework.views import APIView

from .index import Authentication, UserPermission


class AuthTest(APIView):
    authentication_classes = [Authentication, ]
    permission_classes = [UserPermission,]

    def get(self, request, *args, **kwargs):
        print(request.user, request.auth)
        return IkSccJsonResponse('Get Dog')

    def post(self, requst, *args, **kwargs):
        return IkSccJsonResponse('Post Dog')

    def delete(self, request, *args, **kwargs):
        return IkSccJsonResponse('Delete Dog')

    def put(self, request, *args, **kwargs):
        return IkSccJsonResponse('Put Dog')
