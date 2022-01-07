from rest_framework.generics import ListAPIView, CreateAPIView
from rest_framework.permissions import IsAuthenticated

from .models import ArticleCollection
from .serializers import CollectionModelSerializer


class CollectionAPIView(ListAPIView, CreateAPIView):
    """文集列表"""
    permission_classes = (IsAuthenticated,)
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
