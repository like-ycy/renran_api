from django.urls import path

from . import views

urlpatterns = [
    path('banner', views.BannerListAPIView.as_view(), name='banner'),
    path("nav/header/", views.HeaderNavListAPIView.as_view()),
    path("nav/footer/", views.FooterNavListAPIView.as_view()),
]
