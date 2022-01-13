from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """用户模型类"""
    nickname = models.CharField(max_length=20, null=True, verbose_name="用户昵称")
    mobile = models.CharField(max_length=15, unique=True, verbose_name="手机号", default='')
    avatar = models.ImageField(upload_to="avatar", null=True, verbose_name="头像")
    wechat = models.CharField(max_length=100, null=True, unique=True, verbose_name="微信账号")
    alipay = models.CharField(max_length=100, null=True, unique=True, verbose_name="支付宝账号")
    qq_number = models.CharField(max_length=11, null=True, unique=True, verbose_name="QQ号")
    money = models.DecimalField(decimal_places=2, max_digits=8, default=0, verbose_name="用户资金")

    class Meta:
        # 自定义表名
        db_table = "rr_users"
        verbose_name = "用户信息"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.nickname if self.nickname else self.username
