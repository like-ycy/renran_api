from django.db import models

from article.models import Article
from renranapi.utils.models import BaseModel
from users.models import User


class Reward(BaseModel):
    REWARD_TYPE = (
        (1, "支付宝"),
        (2, "余额"),
    )
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="用户")
    money = models.DecimalField(decimal_places=2, max_digits=6, verbose_name="打赏金额")
    article = models.ForeignKey(Article, on_delete=models.DO_NOTHING, verbose_name="文章")
    status = models.BooleanField(default=False, verbose_name="打赏状态")
    reward_type = models.IntegerField(default=1, verbose_name="打赏类型")
    message = models.TextField(null=True, blank=True, verbose_name="打赏留言")
    trade_no = models.CharField(max_length=255, null=True, blank=True, verbose_name="流水号")
    out_trade_no = models.CharField(max_length=255, null=True, blank=True, verbose_name="订单号")

    class Meta:
        db_table = "rr_user_reward"
        verbose_name = "打赏记录"
        verbose_name_plural = verbose_name

    def __str__(self):
        author = self.article.user.nickname if self.article.user.nickname else self.article.user.username
        reward_user = self.user.nickname if self.user.nickname else self.user.username
        return reward_user + "打赏了" + author + "的文章《" + self.article.title + "》" + self.money + "元"
