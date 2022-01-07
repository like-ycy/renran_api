from rest_framework import serializers

from .models import ArticleCollection


class CollectionModelSerializer(serializers.ModelSerializer):
    """文集序列化器"""

    class Meta:
        model = ArticleCollection
        fields = ('id', 'name')
