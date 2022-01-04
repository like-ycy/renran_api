from django.contrib import admin

from .models import Banner


class BannerModelAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "link", "image", "is_show", "start_time", "end_time"]
    list_editable = ["is_show", "start_time", "end_time"]


admin.site.register(Banner, BannerModelAdmin)
