from django.urls import path, re_path

from . import views

urlpatterns = [
    path('collection', views.CollectionAPIView.as_view()),
    re_path("^collection/(?P<pk>\d+)/$", views.CollectionAPIView.as_view()),
    re_path("^collection/(?P<collection>\d+)/articles/$", views.ArticleAPIView.as_view()),
    re_path("^(?P<pk>\d+)/$", views.ArticleAPIView.as_view()),
    re_path("^(?P<pk>\d+)/interval/$", views.ArticleInfoAPIView.as_view()),
    re_path("^(?P<pk>\d+)/info/$", views.ArticleInfoAPIView.as_view()),
    path("image/", views.ArticleImageAPIView.as_view()),
    path("special/", views.SpecialAPIView.as_view()),
    path("post/", views.ArticlePostAPIView.as_view()),
]
