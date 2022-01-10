from django.contrib import admin

from .models import ArticleCollection, Article


class ArticleCollectionAdmin(admin.ModelAdmin):
    """"文集管理"""
    list_display = ["id", "name"]


admin.site.register(ArticleCollection, ArticleCollectionAdmin)


class ArticleAdmin(admin.ModelAdmin):
    """文章管理"""
    list_display = ["id", "title", "collection", "user", "is_public", "pub_date"]


admin.site.register(Article, ArticleAdmin)
