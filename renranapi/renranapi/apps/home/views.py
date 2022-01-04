from django.conf import settings
from django.utils import timezone as datetime
from rest_framework.generics import ListAPIView

from .models import Banner
from .serializers import BannerModelSerializer


class BannerListAPIView(ListAPIView):
    """轮播图视图"""
    serializer_class = BannerModelSerializer

    # 使用queryset会有一个时间bug，时间为项目启动时间，所以改为使用get_queryset
    def get_queryset(self):
        return Banner.objects.filter(is_show=True, is_deleted=False, start_time__lte=datetime.now(),
                                     end_time__gte=datetime.now()).order_by('orders', 'id')[
               :settings.HOME_BANNER_LENGTH]
