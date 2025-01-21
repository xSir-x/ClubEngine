# -*- coding: utf-8 -*-
import datetime
import random
from django.views.generic import View
import time
from django.utils import timezone
from wxpay.wechatpayv3 import WeChatPay, WeChatPayType
from wxpay.settings import *
from dbModel.models import *

# 微信支付平台公钥模式初始化，2024年09月之后申请的账号参考使用此模式。
# 平台证书模式向公钥模式切换期间也请使用此方式初始化。
print("PUBLIC_KEY_ID:", PUBLIC_KEY_ID)
wxpay = WeChatPay(
    wechatpay_type=WeChatPayType.NATIVE,
    mchid=MCHID,
    private_key=PRIVATE_KEY,
    cert_serial_no=CERT_SERIAL_NO,
    apiv3_key=APIV3_KEY,
    appid=APPID,
    notify_url=NOTIFY_URL,
    logger=LOGGER,
    partner_mode=PARTNER_MODE,
    proxy=PROXY,
    timeout=TIMEOUT,
    public_key=PUBLIC_KEY,
    public_key_id=PUBLIC_KEY_ID)

import requests


class ExchangeRate():
    @classmethod
    def HK_to_RMB(cls):
        # 使用 ExchangeRate-API 的免费 API 服务
        api_url = "https://api.exchangerate-api.com/v4/latest/HKD"
        # 发送请求
        response = requests.get(api_url)
        # 检查请求是否成功
        if response.status_code == 200:
            # 解析 JSON 响应
            data = response.json()
            cny_rate = float(data["rates"]["CNY"])
            print(f"HKD to CNY exchange rate: {cny_rate}")
            return cny_rate
        else:
            raise Exception("Failed to retrieve exchange rate data.")


class WXMinPay(object):
    @classmethod
    def pay_miniprog(cls, request):
        """
        支付请求：
        :param request:
        :return:
        """
        request_res = json.loads(request.body)
        order_id = request_res.get("order_id", None)
        amount = int(float(request_res.get('amount', 0)) * 100)
        description = request_res.get("description", 'Y-Club WXminPay')
        payer = {'openid': request_res.get("openid", None)}
        act_id = request_res.get("act_id", None)

        # 金额验证
        act_info_obj = ActivityInfoTable.objects.filter(act_id=act_id)
        if act_info_obj.exists():
            _amount = int(float(act_info_obj.values("price")[0]["price"]) * 100)
            if amount != _amount:
                response = {'code': 300,
                            'succeed': False,
                            'msg': '金额与用户当前等级不一致，无法支付...'}
                return response
        else:
            response = {'code': 300,
                        'succeed': False,
                        'msg': '订单对应的活动不存在...'}
            return response

        # 以小程序下单为例，下单成功后，将prepay_id和其他必须的参数组合传递给小程序的wx.requestPayment接口唤起支付
        # out_trade_no = ''.join(sample(ascii_letters + digits, 8))
        # description = 'Y-Club WXminPay'
        # amount = 1
        # payer = {'openid': 'demo-openid'}

        code, message = wxpay.pay(
            description=description,  # 商品描述
            out_trade_no=order_id,  # 订单号
            amount={'total': amount},  # 订单金额
            pay_type=WeChatPayType.MINIPROG,  # 支付方式：小程序
            payer=payer,  # 支付者信息
        )
        result = json.loads(message)
        if code in range(200, 300):
            prepay_id = result.get('prepay_id')
            timestamp = time.time()  # 当前时间戳
            noncestr = str(uuid.uuid4()).replace('-', '')  # 生成一个随机字符串
            package = 'prepay_id=' + prepay_id  # 拼接prepay_id参数
            sign = wxpay.sign(data=[APPID, timestamp, noncestr, package])
            signtype = 'RSA'  # 签名方式

            response = {'code': 200,
                        'succeed': True,
                        'msg': "支付请求发起成功...",
                        'response': {
                            'appId': APPID,  # 微信公众号ID
                            'timeStamp': timestamp,  # 当前时间戳
                            'nonceStr': noncestr,  # 随机字符串
                            'package': 'prepay_id=%s' % prepay_id,  # 拼接的prepay_id参数
                            'signType': signtype,  # 签名方式
                            'paySign': sign  # 签名
                        }
                        }

            return response
        else:
            order_status = 3
            pay_time = time.time()
            UserOrderTable.objects.filter(order_id=order_id).update(order_status=order_status,
                                                                    pay_time=pay_time)

            response = {'code': 300, 'succeed': False, 'msg': "支付请求发起失败: %s" % result["message"]}
            return response

    @classmethod
    def notify(cls, request):
        """
        支付结果回调处理：调用 wxpay.callback 函数处理请求头和请求数据
        :param request:
        :return:
        """
        result = wxpay.callback(request.headers, request.data)
        # 如果处理结果存在且事件类型为 'TRANSACTION.SUCCESS'
        if result and result.get('event_type') == 'TRANSACTION.SUCCESS':
            # 从处理结果中获取资源信息
            resp = result.get('resource')
            appid = resp.get('appid')
            mchid = resp.get('mchid')
            order_id = resp.get('out_trade_no')
            transaction_id = resp.get('transaction_id')
            trade_type = resp.get('trade_type')
            trade_state = resp.get('trade_state')
            trade_state_desc = resp.get('trade_state_desc')
            bank_type = resp.get('bank_type')
            attach = resp.get('attach')
            success_time = resp.get('success_time')
            payer = resp.get('payer')
            amount = resp.get('amount').get('total')
            # 在这里可以写我们的业务处理，必须要返回一个SUCCESS的回复，否则微信会视为没有调用成功，从而一直调用当前请求。

            order_status = 2
            pay_time = time.time()
            paymentid = transaction_id

            UserOrderTable.objects.filter(order_id=order_id).update(order_status=order_status,
                                                                    pay_time=pay_time,
                                                                    paymentid=paymentid)
            response = {'code': 200, 'succeed': True, 'message': '支付回调成功...'}
            return response
        else:
            response = {'code': 300, 'succeed': False, 'message': '支付回调失败...'}
            return response

    @classmethod
    def gen_order(cls, request):
        """
        生成订单ID，更新DB：order_id, uid, act_id, coop_id, order_time, exp_time, order_status
        :param request:
        :return:
        """
        try:
            request_res = json.loads(request.body)
            uid = request_res.get("uid", None)
            act_id = request_res.get("act_id", None)
            coop_id = request_res.get("coop_id", None)

            res_obj = UserOrderTable.objects.filter(uid=uid, act_id=act_id, coop_id=coop_id)
            if res_obj.exists():
                res_det = res_obj.values("order_time", "exp_time")
                delta_min = 0
                exp_time = 0  # 订单过期时间10分钟
                for det_item in res_det:
                    order_time = det_item["order_time"]
                    exp_time = det_item["exp_time"]
                    delta_min = (int(time.time()) - int(order_time)) / 60
                if delta_min < exp_time:
                    response = {'code': 200, 'succeed': True, 'msg': '订单已经存在...'}
                    return response
                else:
                    UserOrderTable.objects.filter(uid=uid, act_id=act_id, coop_id=coop_id).delete()

            # order_time = timezone.now()
            order_time = str(int(time.time()))
            t_time = time.localtime(float(order_time))
            exp_time = 10  # 默认过期时间10min:   timezone.now()
            order_status = 1  # 订单状态：1-未支付 2-支付成功 3-支付失败
            date = datetime.datetime.now().strftime("%Y-%m-%d")
            order_id = f'{str(int(time.time()))}-{random.randint(1000, 9999)}'

            UserOrderTable.objects.create(order_id=order_id,
                                          uid=uid,
                                          act_id=act_id,
                                          coop_id=coop_id,
                                          pay_time=order_time,
                                          order_time=order_time,
                                          exp_time=exp_time,
                                          paymentid="",
                                          order_status=order_status)
            response = {'code': 200, 'succeed': True, 'msg': '订单创建成功...'}
            return response
        except Exception as e:
            response = {'code': 300, 'succeed': False, 'msg': '订单创建失败: %s' % e}
            return response

    @classmethod
    def search_order(cls, request):
        """
        查询订单
        :param request:
        :return:
        """
        try:
            # request_res = json.loads(request.body)
            # order_id = request_res.get("order_id", None)
            # code, message = wxpay.query(
            #     transaction_id=order_id
            # )
            # print('code: %s, message: %s' % (code, message))
            request_res = json.loads(request.body)
            order_id = request_res.get("order_id", None)
            my_act_obj = UserOrderTable.objects.filter(order_id=order_id)
            order_infos = []
            if my_act_obj.exists():
                order_infos = my_act_obj.values()
            response = {'code': 200, 'succeed': True, 'msg': '订单查询成功', 'response': order_infos}
            return response
        except Exception as e:
            response = {'code': 300, 'succeed': False, 'msg': '订单查询失败: %s.' % e}
            return response


if __name__ == '__main__':
    pass
