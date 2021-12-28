from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from renranapi.apps.users.models import User


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
