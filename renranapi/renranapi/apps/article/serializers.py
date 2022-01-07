from rest_framework import serializers

from .models import ArticleCollection


class CollectionModelSerializer(serializers.ModelSerializer):
    """文集序列化器"""

    class Meta:
        model = ArticleCollection
        fields = ('id', 'name')

    def validate(self, attrs):
        """数据校验"""
        # 校验文集名称是否重复
        name = attrs.get('name')
        user = self.context['request'].user
        try:
            ArticleCollection.objects.get(name=name, user=user, is_deleted=False)
            raise serializers.ValidationError('文集名称已存在')
        except ArticleCollection.DoesNotExist:
            return attrs

    def create(self, validated_data):
        """创建文集"""
        name = validated_data.get('name')
        user = self.context['request'].user
        try:
            instance = ArticleCollection.objects.create(name=name, user=user)
            return instance
        except:
            raise serializers.ValidationError('创建文集失败')
