import random

from alipay import AliPay
from django.utils import timezone as datetime
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from article.models import Article
from renranapi.utils.tablestore1 import *
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


class AlipayResultAPIView(APIView):
    """支付结果的处理"""

    def get1(self, request):
        """同步回调结果的处理"""
        data = request.query_params.dict()  # 把查询字符串转换成字典
        signature = data.pop("sign")

        alipay = self.get_alipay()

        # 验证支付的同步通知结果
        success = alipay.verify(data, signature)
        if True:
            # 完成支付结果的处理
            # 根据订单号提取订单信息
            out_trade_no = data.get("out_trade_no")
            try:
                reward = Reward.objects.get(out_trade_no=out_trade_no, status=False)
            except Reward.DoesNotExist:
                return Response({"detail": "当前打赏记录不存在或者已完成！"}, status=status.HTTP_400_BAD_REQUEST)

            # 根据订单的付款状态进行修改
            self.change_reward(data, reward)

            # 返回结果
            return Response({"detail": "支付处理成功！", "article_id": reward.article.id})

        return Response({"detial": "支付结果参数有误！"}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """提供给客户端查询订单支付结果"""
        out_trade_no = request.query_params.get("out_trade_no")
        try:
            reward = Reward.objects.get(out_trade_no=out_trade_no)
        except Reward.DoesNotExist:
            return Response({"detail": "当前打赏记录不存在！"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"status": reward.status})

    def post(self, request):
        """异步回调结果的处理"""
        data = request.data
        signature = data.pop("sign")

        alipay = self.get_alipay()

        # 验证支付的异步通知结果
        success = alipay.verify(data, signature)
        if success and data["trade_status"] in ("TRADE_SUCCESS", "TRADE_FINISHED"):
            # 完成支付结果的处理
            # 根据订单号提取订单信息
            out_trade_no = data.get("out_trade_no")
            try:
                reward = Reward.objects.get(out_trade_no=out_trade_no)
                if reward.status:
                    return Response("success", content_type="text/plain")
            except Reward.DoesNotExist:
                return Response("success", content_type="text/plain")

            self.change_reward(data, reward)

            # 返回结果
            return Response("success", content_type="text/plain")

        return Response("fail", status=status.HTTP_400_BAD_REQUEST, content_type="text/plain")

    def change_reward(self, data, reward):
        # 根据订单的付款状态进行修改
        reward.status = True
        reward.trade_no = data.get("trade_no")
        reward.save()

        # 增加文章作者的资金
        reward.article.user.money += reward.money
        reward.article.user.save()

        # 增加文章的赞赏人数
        reward.article.reward_count += 1
        reward.article.save()

        # 记录用户的赞赏行为
        primary_key = {"id": settings.LOG_TABLE_ID, "user_id": reward.user.id, "message_id": reward.article.id}
        attribute_columns = {
            "is_reward": 1,
            "timestamp": datetime.now().timestamp(),
        }
        OTS().update_row("user_message_log_table", primary_key, attribute_columns)

    def get_alipay(self):
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

        return alipay
