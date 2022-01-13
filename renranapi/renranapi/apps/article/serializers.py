from django.utils import timezone as datetime
from rest_framework import serializers

from .models import ArticleCollection, Article, ArticleImage, ArticleSpecial


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

    def create(self, validated_data):
        collection_id = int(self.context["view"].kwargs.get("collection"))
        instance = Article.objects.create(
            title=datetime.now().strftime("%Y-%m-%d"),
            collection_id=collection_id,
            user=self.context['request'].user
        )
        if not validated_data.get('insert'):
            instance.orders = 0 - instance.id
            instance.save()
        return instance


class ArticleImageModelSerializer(serializers.ModelSerializer):
    """文章图片序列化器"""

    class Meta:
        model = ArticleImage
        fields = ["id", "article", "image"]

    def create(self, validated_data):
        instance = ArticleImage.objects.create(
            image=validated_data.get('image'),
            orders=0,
            user=self.context['request'].user
        )
        instance.group = str(instance.image).split('/')[0]
        instance.save()
        return instance


class SpecialModelSerializer(serializers.ModelSerializer):
    """专题序列化器"""
    post_status = serializers.BooleanField(read_only=True, default=False, label="文章对于专题的发布状态")

    class Meta:
        model = ArticleSpecial
        fields = ["id", "name", "image", "notice", "article_count", "follow_count", "post_status"]
