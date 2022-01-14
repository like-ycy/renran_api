import random

from alipay import AliPay
from django.conf import settings
from django.utils import timezone as datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from article.models import Article
from .models import Reward


class AlipayAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """发起支付，生成记录，返回支付链接"""
        # 获取参数
        money = request.data.get('money')
        article_id = request.data.get('article_id')
        user = request.user
        # 判断参数是否合法
        if not article_id:
            return Response({'detail': '参数错误'}, status=status.HTTP_400_BAD_REQUEST)
        # 判断文章是否存在
        try:
            article = Article.objects.get(is_deleted=False, is_show=True, is_public=True, id=article_id)
        except Article.DoesNotExist:
            return Response({'detail': '文章不存在'}, status=status.HTTP_400_BAD_REQUEST)

        # 生成订单号
        out_trade_no = datetime.now().strftime("%Y%m%d%H%M%S") + ("%06d" % user.id) + (
                "%06d" % random.randint(1, 999999))

        reward = Reward.objects.create(
            money=float(money),
            user=user,
            article=article,
            reward_type=1,
            message=request.data.get('message'),
            out_trade_no=out_trade_no,
        )

        # 读取秘钥文件的内容
        app_private_key_string = open(settings.ALIPAY.get("app_private_key_path")).read()
        alipay_public_key_string = open(settings.ALIPAY.get("alipay_public_key_path")).read()
        # 根据支付宝sdk生成支付链接
        alipay = AliPay(
            appid=settings.ALIPAY.get("appid"),  # appid
            app_notify_url=settings.ALIPAY.get("app_notify_url"),  # 默认回调url
            app_private_key_string=app_private_key_string,
            alipay_public_key_string=alipay_public_key_string,
            sign_type=settings.ALIPAY.get("sign_type"),
            debug=settings.ALIPAY.get("debug")
        )

        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=out_trade_no,  # 订单号
            total_amount=float(money),  # 订单金额
            subject="打赏文章《%s》" % article.title,  # 订单标题
            return_url=settings.ALIPAY.get("return_url"),  # 订单的同步回调地址[js跳转]
            notify_url=settings.ALIPAY.get("notify_url")  # 订单的异步回调地址[由支付宝主动发起请求到api服务端的地址]
        )

        url = settings.ALIPAY.get("gateway_url") + order_string

        return Response({"url": url, "out_trade_no": out_trade_no})
