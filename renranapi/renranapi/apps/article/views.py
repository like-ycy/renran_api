from django.utils import timezone as datetime
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView, UpdateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from renranapi.utils.tablestore1 import *
from users.models import User
from .models import ArticleCollection, Article, ArticleImage, ArticleSpecial
from .models import ArticlePostSpecial
from .serializers import CollectionModelSerializer, ArticleModelSerializer, ArticleImageModelSerializer
from .serializers import SpecialModelSerializer, ArticleRetrieveModelSerializer


class CollectionAPIView(ListAPIView, CreateAPIView, DestroyAPIView, UpdateAPIView):
    """文集列表"""
    permission_classes = [IsAuthenticated]
    serializer_class = CollectionModelSerializer

    def get_queryset(self):
        # 获取当前用户的文集
        collection_list = ArticleCollection.objects.filter(user=self.request.user, is_deleted=False,
                                                           is_show=True).order_by('orders', 'id')
        if len(collection_list) < 1:
            """针对新用户默认创建2个文集提供给用户[当然也可以在用户注册的时候给用户默认添加2个文集]"""
            collection_list1 = ArticleCollection.objects.create(user=self.request.user, name='我的日记', )
            collection_list2 = ArticleCollection.objects.create(user=self.request.user, name='我的随笔', )
            collection_list = [collection_list1, collection_list2]
        return collection_list

    def perform_destroy(self, instance):
        """逻辑删除"""
        instance.is_deleted = True
        instance.save()


class ArticleAPIView(ListAPIView, CreateAPIView):
    """文章视图"""
    permission_classes = [IsAuthenticated]
    serializer_class = ArticleModelSerializer

    def get_queryset(self):
        collection_id = self.kwargs.get('collection')
        return Article.objects.filter(is_deleted=False, is_show=True, user=self.request.user,
                                      collection_id=collection_id).order_by("orders", "id")

    def patch(self, request, pk):
        """修改文章发布状态"""
        try:
            article = Article.objects.get(pk=pk, is_deleted=False, is_show=True, user=self.request.user)
        except Article.DoesNotExist:
            return Response({"detail": "当前文章不存在！"}, status=status.HTTP_400_BAD_REQUEST)
        """
        1. 隐私文章 is_public=False, pub_date=None
        2. 发布文章 is_public=True, pub_date=None
        3. 定时文章 is_public=False, pub_date=时间
        """
        if article.pub_date:
            """取消定时发布文章"""
            article.pub_date = None
        elif article.is_public:
            """把文章设置为隐私文章"""
            article.is_public = False
            # 取消推送Feed流
            article.cancel_push_feed()
        else:
            """发布文章"""
            article.is_public = True
            # 推送feed流给粉丝
            article.push_feed()
        article.save()
        return Response({"detail": "发布状态切换成功!"}, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """修改文章所在文集"""
        try:
            article = Article.objects.get(pk=pk, is_deleted=False, is_show=True, user=self.request.user)
        except Article.DoesNotExist:
            return Response({"detail": "当前文章不存在！"}, status=status.HTTP_400_BAD_REQUEST)
        collection_id = int(request.data.get('collection'))
        article.collection_id = collection_id
        article.save()
        return Response({"detail": "移动文章成功!"}, status=status.HTTP_200_OK)


class ArticleInfoAPIView(APIView):
    """文章信息视图"""
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        """修改文章发布时间"""
        try:
            article = Article.objects.get(pk=pk, is_deleted=False, is_show=True, user=self.request.user)
        except Article.DoesNotExist:
            return Response({"detail": "当前文章不存在！"}, status=status.HTTP_400_BAD_REQUEST)

        # 判断文章是否已经发布
        if article.is_public:
            return Response({"detial": "已经发布的文章不能设置定时发布!"})

        # 判断发布时间是否为未来时间
        now_time = datetime.now().timestamp()
        pub_time_str = request.data.get('pub_date')  # 字符串
        # 将字符串转换为时间戳
        put_time = datetime.datetime.strptime(pub_time_str, "%Y-%m-%d %H:%M:%S").timestamp()

        if put_time <= now_time:
            return Response({"detail": "定时发布的文章必须是未来的时间点!"}, status=status.HTTP_400_BAD_REQUEST)

        article.pub_date = pub_time_str
        article.save()

        return Response({"detail": "定时发布文章设置成功!"})

    def put(self, request, pk):
        """文章内容修改保存"""
        try:
            article = Article.objects.get(pk=pk, is_deleted=False, is_show=True, user=self.request.user)
        except Article.DoesNotExist:
            return Response({"detail": "当前文章不存在！"}, status=status.HTTP_400_BAD_REQUEST)

        article.title = request.data.get('title', '')
        article.content = request.data.get('content', '')
        article.html_content = request.data.get('html_content', '')
        article.save()

        return Response({"detail": "编辑文章保存成功!"})


class ArticleImageAPIView(CreateAPIView):
    """文章图片上传视图"""
    permission_classes = [IsAuthenticated]
    serializer_class = ArticleImageModelSerializer
    queryset = ArticleImage.objects.all()


class SpecialAPIView(ListAPIView):
    """专题视图"""
    permission_classes = [IsAuthenticated]
    serializer_class = SpecialModelSerializer

    def get_queryset(self):
        article_id = self.request.query_params.get('article_id')
        special_list = ArticleSpecial.objects.filter(is_show=True, is_deleted=False,
                                                     mymanager__user=self.request.user).order_by("orders", "id")

        for special in special_list:
            special.post_status = special.check_post_stauts(article_id)
        return special_list


class ArticlePostAPIView(APIView):
    """文章投稿"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """文章投稿到专题"""
        # 文章id和专题id
        article_id = request.data.get('article_id')
        special_id = request.data.get('special_id')

        try:
            article = Article.objects.get(pk=article_id, is_deleted=False, is_show=True, user=self.request.user)
        except Article.DoesNotExist:
            return Response({"detail": "当前文章不存在!"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            special = ArticleSpecial.objects.get(pk=special_id, is_deleted=False, is_show=True)
        except ArticleSpecial.DoesNotExist:
            return Response({"detail": "当前专题不存在!"}, status=status.HTTP_400_BAD_REQUEST)

        # 判断文章是否已经投稿或者在审核中了
        try:
            ArticlePostSpecial.objects.get(article=article, special=special, status__in=[0, 1, 2])
            return Response({"detail": "当前文章已经在投稿中或已被收录，请不要频繁点击投稿!"}, status=status.HTTP_400_BAD_REQUEST)
        except:
            pass

        # 新增投稿记录
        postlog = ArticlePostSpecial.objects.create(
            article=article,
            special=special,
            status=0,
            post_time=datetime.now()
        )

        # 判断当前用户是否是专题的管理员，如果是，则直接默认通过
        try:
            postlog.special.mymanager.get(user=request.user)
            postlog.status = 2
            postlog.save()
        except:
            pass

        return Response({"detail": "文章投稿成功!"}, status=status.HTTP_200_OK)


class ArticleRetrieveAPIView(RetrieveAPIView):
    """文章详情"""
    queryset = Article.objects.filter(is_deleted=False, is_show=True, is_public=True)
    serializer_class = ArticleRetrieveModelSerializer


class FocusAPIView(APIView):
    def get(self, request):
        if not isinstance(request.user, User):
            return Response({"status": -2, "detail": "当前用户尚未登录！无法查询关注关系"})

        try:
            author_id = int(request.query_params.get("author_id"))
            User.objects.get(pk=author_id)
        except User.DoesNotExist:
            return Response({"detail": "参数有误，当前作者不存在！"}, status=status.HTTP_400_BAD_REQUEST)

        if author_id == request.user.id:
            return Response({"status": -1, "detail": "当前用户是作者!"})

        ret = OTS().get_row("user_relation_table", {"id": settings.RELATION_TABLE_ID, "user_id": author_id,
                                                    "follow_user_id": request.user.id})
        return Response({"status": int(ret[0])})

    def put(self, request):
        """切换关注关系"""
        if not isinstance(request.user, User):
            return Response({"detail": "用户尚未用户，无法操作"}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            author_id = int(request.data.get("author_id"))
            User.objects.get(pk=author_id)
        except User.DoesNotExist:
            return Response({"detail": "参数有误，当前作者不存在！"}, status=status.HTTP_400_BAD_REQUEST)

        if author_id == request.user.id:
            return Response({"detail": "当前用户是作者!"}, status=status.HTTP_400_BAD_REQUEST)

        # 获取当前用户与作者的关注状态
        focus_status = bool(int(request.data.get("status")))

        client = OTS()
        primary_key = {"id": settings.RELATION_TABLE_ID, "user_id": author_id, "follow_user_id": request.user.id}
        if focus_status:
            message = "取消关注"
            ret = client.delete_row("user_relation_table", primary_key)
        else:
            message = "关注"
            ret = client.put_row("user_relation_table", primary_key)

        if not ret[0]:
            return Response({"detail": "%s失败！" % message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"status": not focus_status, "detail": "%s成功！" % message})


class UserArticleAPIView(ViewSet):
    permission_classes = [IsAuthenticated]
    """用户和文章之间的交互行为记录api"""
    client = OTS()

    def check_params(self):
        user = self.request.user
        pk = int(self.kwargs.get("pk"))
        try:
            article = Article.objects.get(pk=pk, is_deleted=False, is_show=True, is_public=True)
        except Article.DoesNotExist:
            return Response({"detail": "当前文章不存在!"}, status=status.HTTP_400_BAD_REQUEST)

        # 如果用户是作者，则不需要记录
        if article.user.id == user.id:
            return Response({"detail": "当前是作者。"}, status=status.HTTP_400_BAD_REQUEST)

        primary_key = {"id": settings.LOG_TABLE_ID, "user_id": user.id, "message_id": pk}
        ret = self.client.get_row("user_message_log_table", primary_key)

        return user, primary_key, ret

    @action(methods=["get"], detail=True)
    def read(self, request, pk):
        response = self.check_params()
        if isinstance(response, Response):
            return response
        user, primary_key, ret = response
        if ret[0] and len(ret[1]) < 1:
            attribute_columns = {
                "is_read": 1,
                "is_comment": 0,
                "is_reward": 0,
                "is_like": 0,
                "timestamp": datetime.now().timestamp(),
            }
            self.client.put_row("user_message_log_table", primary_key, attribute_columns)

        return Response({"detail": "ok"})

    @action(methods=["get"], detail=True)
    def status(self, request, pk):
        """添加评论，点赞等行为"""
        response = self.check_params()
        if isinstance(response, Response):
            return response
        user, primary_key, ret = response
        status_type = request.query_params.get("type")
        if status_type not in ("is_comment", "is_like"):
            return Response({"detail": "参数有误，无法添加行为记录"}, status=status.HTTP_400_BAD_REQUEST)
        if ret[0] and len(ret[1]) > 0:
            attribute_columns = {
                status_type: 1,
                "timestamp": datetime.now().timestamp(),
            }
            self.client.update_row("user_message_log_table", primary_key, attribute_columns)
        else:
            return Response({"detail": "当前用户没有阅读文章的记录，无法添加行为记录"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "ok"})
