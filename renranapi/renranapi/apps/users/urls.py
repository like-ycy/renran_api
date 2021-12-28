from django.urls import path, re_path

from . import views

urlpatterns = [
    path('login/', views.LoginAPIView.as_view(), name='login'),
    re_path('^mobile/(?P<mobile>1[3-9]\d{9})/$', views.MobileAPIView.as_view(), name='mobile'),
    path('register/', views.UserAPIView.as_view(), name='register'),
    re_path('^sms/(?P<mobile>1[3-9]\d{9})/$', views.SMSAPIView.as_view(), name='sms'),
]
