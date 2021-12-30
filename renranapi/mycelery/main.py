import os

import django
from celery import Celery

# 创建对象
app = Celery("renran")

# 把celery和django组合
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'renranapi.settings.dev')

# 对django框架执行初始化
django.setup()

# 加载配置
app.config_from_object("mycelery.config")

# 注册任务
app.autodiscover_tasks(["mycelery.email", "mycelery.article"])

# 运行celery
# 注意,务必在服务端项目根目录下运行
# 在本地开发中,直接在终端下面直接运行,需要保持终端没有关闭
# celery -A mycelery.main worker --loglevel=info
# 在实际工作中, 肯定是守护进程的模式来启动,到时候supervisor
