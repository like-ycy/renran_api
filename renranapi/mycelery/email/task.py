import logging

from django.conf import settings
from django.core.mail import send_mail

from mycelery.main import app

log = logging.getLogger("django")


@app.task(name="send_email")
def send_email(recipient_list, url):
    """异步发送找回密码的邮件"""
    try:
        send_mail(subject='找回密码', message='', from_email=settings.EMAIL_FROM, recipient_list=recipient_list,
                  html_message='<a href="%s" target="_blank">重置密码</a>' % url)
    except:
        log.error("发送邮件失败！")
