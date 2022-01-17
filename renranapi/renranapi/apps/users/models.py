from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone as datetime

from renranapi.utils.tablestore1 import *


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

    def get_user_log(self, user_id=None, limit=50):
        """获取指定用户最近3个月的行为记录"""
        if user_id is None:
            user_id = self.id
        start_key = {"id": settings.LOG_TABLE_ID, "user_id": user_id, "message_id": INF_MIN}
        end_key = {"id": settings.LOG_TABLE_ID, "user_id": user_id, "message_id": INF_MAX}
        columns_to_get = ["is_read", "is_comment", "is_reward", "is_like"]
        timestamp = datetime.now().timestamp() - 3 * 30 * 24 * 60 * 60
        cond = SingleColumnCondition("timestamp", timestamp, ComparatorType.GREATER_EQUAL)
        ret = OTS().get_list("user_message_log_table", start_key, end_key, limit=limit, columns_to_get=columns_to_get,
                             cond=cond)
        log_list = []
        if ret["status"]:
            """查询成功"""
            log_list.extend(ret["data"])
            while ret["token"] and len(log_list) < limit:
                ret = OTS().get_list("user_message_log_table", start_key, end_key, limit=limit,
                                     columns_to_get=columns_to_get, cond=cond)
                if ret["status"]:
                    log_list.extend(ret["data"])
        return log_list

    def get_log_list(self, log_list):

        start_key = {"id": settings.LOG_TABLE_ID, "user_id": INF_MIN, "message_id": INF_MIN}
        end_key = {"id": settings.LOG_TABLE_ID, "user_id": INF_MAX, "message_id": INF_MAX}
        columns_to_get = ["is_read", "is_comment", "is_reward", "is_like"]
        timestamp = datetime.now().timestamp() - 15 * 24 * 60 * 60
        limit = 50
        # 与用户2有相同浏览历史的用户列表
        user_list = set()
        # 保存用户2看过的文章列表
        message_list = []
        for log_item in log_list:
            message_list.append(log_item["message_id"])
            cond = CompositeColumnCondition(LogicalOperator.AND)
            cond.add_sub_condition(SingleColumnCondition("timestamp", timestamp, ComparatorType.GREATER_EQUAL))
            cond.add_sub_condition(SingleColumnCondition("message_id", log_item["message_id"], ComparatorType.EQUAL))
            ret = OTS().get_list("user_message_log_table", start_key, end_key, limit=limit,
                                 columns_to_get=columns_to_get, cond=cond)
            if ret["status"]:
                for data in ret["data"]:
                    user_list.add(data["user_id"])

        return list(user_list), message_list
