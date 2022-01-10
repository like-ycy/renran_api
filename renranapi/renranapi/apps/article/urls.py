from django.urls import path, re_path

from . import views

urlpatterns = [
    path('collection', views.CollectionAPIView.as_view(), name='collection'),
    re_path("^collection/(?P<pk>\d+)/$", views.CollectionAPIView.as_view()),
]
