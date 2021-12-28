import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework_jwt.views import ObtainJSONWebToken

from renranapi.utils.tencentcloudapi import TencentCloudAPI, TencentCloudSDKException

logger = logging.getLogger('django')


class LoginAPIView(ObtainJSONWebToken):
    """
    用户登录视图
    """

    def post(self, request, *args, **kwargs):
        """
        校验用户操作验证码成功以后的ticket临时票据
        """
        if settings.IS_TEST:
            return super().post(request, *args, **kwargs)
        try:
            api = TencentCloudAPI()
            result = api.captcha(
                request.data.get("ticket"),
                request.data.get("randstr"),
                request._request.META.get("REMOTE_ADDR"),
            )
            if result:
                return super().post(request, *args, **kwargs)
            else:
                raise TencentCloudSDKException
        except TencentCloudSDKException as err:
            return Response({"errmsg": "验证码校验失败"}, status=status.HTTP_400_BAD_REQUEST)
