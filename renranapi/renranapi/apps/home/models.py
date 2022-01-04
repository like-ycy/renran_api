from models import BaseModel, models


class Banner(BaseModel):
    """轮播图模型"""
    name = models.CharField(max_length=150, verbose_name='轮播图标题')
    info = models.TextField(null=True, blank=True, verbose_name='备注信息')
    link = models.CharField(null=True, blank=True, max_length=150, verbose_name='轮播图广告地址')
    image = models.ImageField(upload_to='banner', verbose_name='轮播图', null=True, blank=True)
    start_time = models.DateTimeField(verbose_name="上架时间", default=None, null=True, blank=True)
    end_time = models.DateTimeField(verbose_name="下架时间", default=None, null=True, blank=True)
    is_http = models.BooleanField(verbose_name="是否站外地址", default=False,
                                  help_text="站内地址格式：/users/<br>站外地址格式：http://www.baidu.com")

    class Meta:
        db_table = 'rr_banner'
        verbose_name = '轮播图'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name
