from django.db import models


class BaseModel(models.Model):
    """公共抽象模型"""
    orders = models.IntegerField(default=0, null=True, blank=True, verbose_name="排序")
    is_show = models.BooleanField(default=True, verbose_name="是否显示")
    is_deleted = models.BooleanField(default=False, verbose_name="是否删除")  # 逻辑删除
    created_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_time = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        abstract = True
