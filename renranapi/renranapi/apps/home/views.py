from django.utils import timezone as datetime
from rest_framework.generics import ListAPIView

from article.models import Article
from renranapi.utils.tablestore1 import *
from users.models import User
from .models import Banner, Nav
from .paginations import HomeArticlePageNumberPagination
from .serializers import ArticleModelSerializer
from .serializers import BannerModelSerializer, NavModelSerializer


class BannerListAPIView(ListAPIView):
    """轮播图视图"""
    serializer_class = BannerModelSerializer

    # 使用queryset会有一个时间bug，时间为项目启动时间，所以改为使用get_queryset
    def get_queryset(self):
        return Banner.objects.filter(is_show=True, is_deleted=False, start_time__lte=datetime.now(),
                                     end_time__gte=datetime.now()).order_by('orders', 'id')[
               :settings.HOME_BANNER_LENGTH]


class HeaderNavListAPIView(ListAPIView):
    queryset = Nav.objects.filter(is_show=True, pid=None, is_deleted=False, position=1).order_by("orders", "id")[
               :settings.HEADER_NAV_LENGTH]
    serializer_class = NavModelSerializer


class FooterNavListAPIView(ListAPIView):
    queryset = Nav.objects.filter(is_show=True, pid=None, is_deleted=False, position=2).order_by("orders", "id")[
               :settings.FOOTER_NAV_LENGTH]
    serializer_class = NavModelSerializer


class ArticleListAPIView(ListAPIView):
    serializer_class = ArticleModelSerializer
    pagination_class = HomeArticlePageNumberPagination

    def get_queryset(self):
        user = self.request.user
        queryset = []
        if isinstance(self.request.user, User):
            """登录"""
            start_key = {"id": settings.MESSAGE_TABLE_ID, "user_id": user.id, "sequence_id": INF_MIN,
                         "message_id": INF_MIN}
            end_key = {"id": settings.MESSAGE_TABLE_ID, "user_id": user.id, "sequence_id": INF_MAX,
                       "message_id": INF_MAX}
            cond = CompositeColumnCondition(LogicalOperator.AND)
            cond.add_sub_condition(SingleColumnCondition("is_cancel", False, ComparatorType.EQUAL))
            cond.add_sub_condition(SingleColumnCondition("is_read", False, ComparatorType.EQUAL))
            message_list = []
            primary_list = []
            # 接受客户端执行返回的单页数据量，如果客户端没有指定，则默认采用分页器的单页数据量
            size = int(self.request.query_params.get("size")) or self.pagination_class.page_size
            client = OTS()
            ret = client.get_list("user_message_table", start_key, end_key, limit=size, cond=cond)

            if ret["status"]:
                for item in ret["data"]:
                    message_list.append(item["message_id"])
                    primary_list.append(item)
                while ret["token"]:
                    # print(ret["token"]) # [('id', 1), ('user_id', 2), ('sequence_id', 1596081490522997), ('message_id', 23)]
                    start_key = ret["token"]
                    end_key = {"id": settings.MESSAGE_TABLE_ID, "user_id": user.id, "sequence_id": INF_MAX,
                               "message_id": INF_MAX}
                    ret = client.get_list("user_message_table", start_key, end_key, limit=size, cond=cond)
                    for item in ret["data"]:
                        message_list.append(item["message_id"])
                        primary_list.append(item)

                queryset = Article.objects.filter(is_public=True, is_show=True, is_deleted=False,
                                                  pk__in=message_list).order_by("-id")

                # 记录推送状态到同步库中
                page = self.request.query_params.get("page")
                if page is None:
                    page = 1
                page = int(page)

                update_primary_list = []
                attribute_columns_list = []
                article_list = queryset[(page - 1) * size:page * size]
                for article in article_list:
                    for data in primary_list:
                        if data["user_id"] == user.id and data["message_id"] == article.id:
                            update_primary_list.append(data)
                            attribute_columns_list.append({"is_read": True})

                client.update_list("user_message_table", update_primary_list, attribute_columns_list)

            if len(queryset) < 1:
                """进行智能推荐"""
                # 1. 获取当前登录用户近3个月的行为记录
                current_user_log_list = user.get_user_log()

                # 2. 把阅读过与当前登录用户一样的文章的所有关联用户查询出来
                user_list, message_list = user.get_log_list(current_user_log_list)

                # 3. 获取每个关联用户近期的行为记录,把所有用户的行为记录合并成一个大数组
                cf_list = {}
                for user_id in user_list:
                    user_log_list = user.get_user_log(user_id)
                    # 遍历每一个相关用户的行为记录，得到每一个文章的推荐度
                    for user_log in user_log_list:
                        cf_num = user_log["is_read"] * settings.CF_READ + user_log["is_like"] * settings.CF_LIKE + \
                                 user_log['is_comment'] * settings.CF_COMMENT + user_log[
                                     "is_reward"] * settings.CF_REWARD
                        if user_log["message_id"] not in message_list:  # 只有当前用户没有阅读过的文章，才统计推荐度
                            if user_log["message_id"] in cf_list:
                                """累加推荐度"""
                                cf_list[user_log["message_id"]] += cf_num
                            else:
                                """新增一个推荐文章"""
                                cf_list[user_log["message_id"]] = cf_num

                # 4.3 字典排序，按推荐度的值从大到小进行排列
                cf_list = sorted(cf_list.items(), key=lambda x: x[1], reverse=True)
                # [(6, 18), (9, 16), (7, 9), (4, 8), (17, 2)]
                # 我们只需要文章ID即可。
                cf_list = [cf_item[0] for cf_item in cf_list]
                queryset = Article.objects.filter(is_public=True, is_show=True, is_deleted=False,
                                                  pk__in=cf_list).order_by("-id")

        if len(queryset) < 1:
            queryset = Article.objects.filter(is_public=True, is_show=True, is_deleted=False).order_by("-reward_count",
                                                                                                       "-comment_count",
                                                                                                       "-like_count",
                                                                                                       "-id")

        return queryset
