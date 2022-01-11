from django.utils import timezone as datetime
from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ArticleCollection, Article, ArticleImage
from .serializers import CollectionModelSerializer, ArticleModelSerializer, ArticleImageModelSerializer


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
