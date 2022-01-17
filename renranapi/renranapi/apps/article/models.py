from django.utils import timezone as datetime

from renranapi.utils.models import BaseModel, models
from renranapi.utils.tablestore1 import *
from users.models import User


class ArticleCollection(BaseModel):
    """文集，相当于文章的分类"""
    user = models.ForeignKey(User, related_name="mycollections", on_delete=models.DO_NOTHING, verbose_name="用户")
    name = models.CharField(max_length=150, db_index=True, verbose_name="文集名称")

    class Meta:
        db_table = "rr_article_collection"
        verbose_name = "文集"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Article(BaseModel):
    """文章模型类"""
    title = models.CharField(max_length=150, db_index=True, verbose_name="文章")
    content = models.TextField(null=True, blank=True, verbose_name="文章内容")
    html_content = models.TextField(null=True, blank=True, verbose_name="文章内容[html格式]")
    user = models.ForeignKey(User, related_name="myarticles", on_delete=models.DO_NOTHING, verbose_name="作者")
    collection = models.ForeignKey(ArticleCollection, related_name="article_list", on_delete=models.CASCADE,
                                   verbose_name="文集")
    pub_date = models.DateTimeField(null=True, blank=True, default=None, verbose_name="发布时间")
    access_pwd = models.CharField(max_length=15, null=True, blank=True, verbose_name="访问密码")
    read_count = models.IntegerField(default=0, null=True, blank=True, verbose_name="阅读量")
    like_count = models.IntegerField(default=0, null=True, blank=True, verbose_name="点赞量")
    collect_count = models.IntegerField(default=0, null=True, blank=True, verbose_name="收藏量")
    comment_count = models.IntegerField(default=0, null=True, blank=True, verbose_name="评论量")
    reward_count = models.IntegerField(default=0, null=True, blank=True, verbose_name="赞赏量")
    is_public = models.BooleanField(default=False, verbose_name="是否公开")

    class Meta:
        db_table = "rr_article"
        verbose_name = "文章"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.title

    def push_feed(self):
        """推送feed流"""
        # 获取当前作者的粉丝列表
        flowers_list = self.get_author_flowers(self.user.id)
        if len(flowers_list) < 1:
            return False

        # 把推送数据填写到同步库中
        primary_key_list = [{
            "id": settings.MESSAGE_TABLE_ID,
            "user_id": flower,
            "sequence_id": PK_AUTO_INCR,
            "message_id": self.id
        } for flower in flowers_list]

        attribute_columns_list = [{
            "timestamp": datetime.now().timestamp(),  # 推送时间
            "is_read": False,  # 是否阅读
            "is_cancel": False,  # 是否取消推送
        } for flower in flowers_list]

        ret = OTS().add_list("user_message_table", primary_key_list, attribute_columns_list)

    def get_author_flowers(self, author_id):
        """获取当前作者的所有粉丝"""
        start_key = {"id": 1, "user_id": author_id, "follow_user_id": INF_MIN}  # 查询开始的主键列
        end_key = {"id": 1, "user_id": author_id, "follow_user_id": INF_MAX}  # 查询结束的主键列

        # 获取粉丝数据，默认一次最多只能获取90
        ret = OTS().get_list("user_relation_table", start_key, end_key)
        data = []
        if ret["status"]:
            data.extend(ret["data"])
            while ret["token"]:  # 当数据超过90条时，token表示下一次查询的开始主键列
                start_key = ret["token"]
                ret = OTS().get_list("user_relation_table", start_key, end_key)
                data.extend(ret["data"])

        flowers_list = [item["follow_user_id"] for item in data]
        return flowers_list

    def cancel_push_feed(self):
        # 取消推送记录
        # 查询当前文章的所有推送记录
        start_key = {'id': 1, 'user_id': INF_MIN, 'sequence_id': INF_MIN, 'message_id': INF_MIN}
        end_key = {'id': 1, 'user_id': INF_MAX, 'sequence_id': INF_MAX, 'message_id': INF_MAX}
        print(self.id)
        cond = cond = SingleColumnCondition("message_id", self.id, ComparatorType.EQUAL)
        ret = OTS().get_list("user_message_table", start_key, end_key, cond=cond)
        if ret["status"]:
            primary_key_list = ret["data"]
        if len(primary_key_list) < 1:
            return False
        attribute_columns_list = [{"is_cancel": True} for i in primary_key_list]
        OTS().update_list("user_message_table", primary_key_list, attribute_columns_list)

    def get_feed_list(self):
        """获取指定文章的推送记录"""
        start_key = {
            "id": settings.MESSAGE_TABLE_ID,
            "user_id": INF_MIN,
            "sequence_id": INF_MIN,
            "message_id": self.id
        }
        end_key = {
            "id": settings.MESSAGE_TABLE_ID,
            "user_id": INF_MAX,
            "sequence_id": INF_MAX,
            "message_id": self.id
        }
        # 获取文章推送记录，默认一次最多只能获取90
        ret = OTS().get_list("user_message_table", start_key, end_key)
        print(ret)
        data = []
        if ret["status"]:
            data.extend(ret["data"])
            while ret["token"]:  # 当数据超过90条时，token表示下一次查询的开始主键列
                start_key = ret["token"]
                ret = OTS().get_list("user_message_table", start_key, end_key)
                data.extend(ret["data"])

        return data


class ArticleSpecial(BaseModel):
    """专题模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name="专题名称")
    image = models.ImageField(null=True, blank=True, verbose_name="封面图片")
    notice = models.TextField(null=True, blank=True, verbose_name="专题公告")
    article_count = models.IntegerField(default=0, null=True, blank=True, verbose_name="文章总数")
    follow_count = models.IntegerField(default=0, null=True, blank=True, verbose_name="关注数量")
    user = models.ForeignKey(User, related_name="myspecials", on_delete=models.DO_NOTHING, verbose_name="创建人")

    class Meta:
        db_table = "rr_article_special"
        verbose_name = "专题"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name

    def check_post_stauts(self, article_id):
        """判断当前文章对于专题的收录状态"""
        try:
            self.myarticles.get(article_id=int(article_id), status=2)
            return True
        except:
            return False


class ArticlePostSpecial(BaseModel):
    """文章和专题的绑定关系"""
    STATUS_OPTION = (
        (0, "投稿中"),
        (1, "等待审核"),
        (2, "审核通过"),
        (3, "审核不通过"),
    )
    article = models.ForeignKey(Article, on_delete=models.CASCADE, verbose_name="文章")
    special = models.ForeignKey(ArticleSpecial, related_name="myarticles", on_delete=models.CASCADE, verbose_name="专题")
    status = models.SmallIntegerField(choices=STATUS_OPTION, default=0, verbose_name="审核状态")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.DO_NOTHING, verbose_name="审核管理员")
    post_time = models.DateTimeField(default=None, null=True, blank=True, verbose_name="投稿时间")

    class Meta:
        db_table = "rr_article_post_special"
        verbose_name = "专题的文章"
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.article.title


class SpecialManager(BaseModel):
    """专题管理员"""
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="用户")
    special = models.ForeignKey(ArticleSpecial, related_name="mymanager", on_delete=models.CASCADE, verbose_name="专题")

    class Meta:
        db_table = "rr_special_manager"
        verbose_name = "专题管理员"
        verbose_name_plural = verbose_name


class SpecialFocus(BaseModel):
    """专题关注"""
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="用户")
    special = models.ForeignKey(ArticleSpecial, on_delete=models.CASCADE, verbose_name="专题")

    class Meta:
        db_table = "rr_special_focus"
        verbose_name = "专题粉丝"
        verbose_name_plural = verbose_name


class ArticleImage(BaseModel):
    """文章图片素材库"""
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, verbose_name="用户")
    group = models.CharField(max_length=15, null=True, blank=True, verbose_name="组名")
    image = models.ImageField(null=True, blank=True, verbose_name="图片地址")
    sha1_files = models.CharField(max_length=64, null=True, blank=True, verbose_name="文件指纹")

    class Meta:
        db_table = "rr_article_image"
        verbose_name = "文章图片"
        verbose_name_plural = verbose_name
