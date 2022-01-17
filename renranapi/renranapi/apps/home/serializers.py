from rest_framework import serializers

from article.models import Article
from article.serializers import UserModelSerializer
from .models import Banner, Nav


class BannerModelSerializer(serializers.ModelSerializer):
    """轮播图序列化器"""

    class Meta:
        model = Banner
        fields = ('image', 'link', 'is_http')


class NavModelSerializer(serializers.ModelSerializer):
    """导航序列化器"""

    # 序列化器嵌套使用,必须是外键字段才可以使用序列化器嵌套
    # son = SonNavModelSerializer(many=True)
    class Meta:
        model = Nav
        fields = ["name", "icon", "link", "is_http", "son_list"]


class ArticleModelSerializer(serializers.ModelSerializer):
    user = UserModelSerializer()

    class Meta:
        model = Article
        fields = ["id", "title", "html_content", "user", "pub_date", "read_count", "like_count", "collect_count",
                  "comment_count", "reward_count", ]
