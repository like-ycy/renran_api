from rest_framework import serializers

from .models import ArticleCollection, Article


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

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name')
        instance.save()
        return instance


class ArticleModelSerializer(serializers.ModelSerializer):
    """文章序列化器"""
    insert = serializers.BooleanField(write_only=True, required=False, default=True,
                                      help_text="新增文章的排序位置: True表示开头,False表示末尾")

    class Meta:
        model = Article
        fields = ["id", "title", "content", "html_content", "is_public", "pub_date", "insert"]
