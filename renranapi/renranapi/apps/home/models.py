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


class Nav(BaseModel):
    """导航栏"""
    POSITION = (
        (1, "头部导航"),
        (2, "脚部导航"),
    )
    pid = models.ForeignKey("Nav", related_name="son", null=True, blank=True, on_delete=models.DO_NOTHING,
                            verbose_name="父亲导航")
    name = models.CharField(max_length=150, verbose_name='导航名称')
    icon = models.CharField(max_length=150, verbose_name="icon图标", help_text="这里填写的是样式名称.")
    link = models.CharField(null=True, blank=True, max_length=150, verbose_name='导航地址')
    position = models.IntegerField(choices=POSITION, default=1, verbose_name="导航位置")
    is_http = models.BooleanField(verbose_name="是否站外地址", default=False,
                                  help_text="站内地址格式：/users/<br>站外地址格式：http://www.baidu.com")

    class Meta:
        db_table = 'rr_nav'
        verbose_name = '导航菜单'
        verbose_name_plural = verbose_name  # 复数

    def __str__(self):
        return self.name

    @property
    def son_list(self):
        """子导航"""
        ret = self.son.filter(is_show=True, is_deleted=False).order_by("orders", "id")
        data = []
        for nav in ret:
            data.append({
                "name": nav.name,
                "icon": nav.icon,
                "link": nav.link,
                "is_http": nav.is_http,
            })
        return data
