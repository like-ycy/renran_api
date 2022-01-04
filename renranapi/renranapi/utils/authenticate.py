from django.contrib.auth.backends import ModelBackend
from django.db.models import Q
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.utils import jwt_payload_handler as payload_handler

from users.models import User


def get_user_by_account(account):
    """
    根据用户信息获取user模型对象
    :param account: 账号信息，可以是用户名、手机号、邮箱
    :return User对象或者 None
    """
    try:
        user = User.objects.filter(Q(username=account) | Q(mobile=account) | Q(email=account)).first()
    except User.DoesNotExist:
        user = None
    return user


class CustomAuthBackend(ModelBackend):
    """
    自定义用户认证类
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写authenticate方法，实现用户名和手机号或者邮箱都能登录
        :param request: http请求对象
        :param username: 用户名、邮箱、手机号
        :param password: 密码
        :param kwargs: 额外参数
        :return:
        """
        # 根据用户名获取用户对象
        user = get_user_by_account(username)
        # 判断用户对象是否存在，并且密码是否正确
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        else:
            return None


def jwt_payload_handler(user):
    """
    自定义载荷信息
    :params user  用户模型实例对象
    """
    # 先让jwt模块生成自己的载荷信息
    payload = payload_handler(user)
    # 追加自己要返回的内容
    if hasattr(user, 'avatar'):
        payload['avatar'] = user.avatar.url if user.avatar else ""
    if hasattr(user, 'nickname'):
        payload['nickname'] = user.nickname

    return payload


def generate_jwt_token(user):
    """
    生成jwt token
    :param user: 用户对象
    :return: jwt token
    """
    jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
    jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
    payload = jwt_payload_handler(user)
    token = jwt_encode_handler(payload)
    return token
