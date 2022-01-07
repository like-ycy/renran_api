from django.contrib import admin

from .models import ArticleCollection


class ArticleCollectionAdmin(admin.ModelAdmin):
    """"文集管理"""
    list_display = ["id", "name"]


admin.site.register(ArticleCollection, ArticleCollectionAdmin)
