from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, DestroyAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ArticleCollection, Article
from .serializers import CollectionModelSerializer, ArticleModelSerializer


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
