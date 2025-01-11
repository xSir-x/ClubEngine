# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.views.generic import View

from wxpay.lib.wechatpayv3.wechatpayv3 import WeChatPay, WeChatPayType
from wxpay.settings import *

# 使用WeChatPay类的构造函数创建一个名为wxpay的实例。
wxpay = WeChatPay(
    # 微信支付类型为NATIVE。
    wechatpay_type=WeChatPayType.NATIVE,
    mchid=MCHID,  # 商户号。
    private_key=PRIVATE_KEY,  # 商户私钥。
    cert_serial_no=CERT_SERIAL_NO,  # 证书序列号
    apiv3_key=APIV3_KEY,  # APIv3密钥
    appid=APPID,  # 应用ID
    notify_url=NOTIFY_URL,  # 回调通知地址。
    cert_dir=CERT_DIR,  # 证书目录。
    partner_mode=PARTNER_MODE,  # 合作模式
    proxy=PROXY,  # 代理
    timeout=TIMEOUT  # 超时时间
)

# 微信支付平台公钥模式初始化，2024年09月之后申请的账号参考使用此模式。
# 平台证书模式向公钥模式切换期间也请使用此方式初始化。
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


class WXMinPay(object):
    def post(self, request):
        """
        支付请求
        """
        request_res = json.loads(request.body)
        out_trade_no = request_res.get("out_trade_no", None)
        amount = int(request_res.get('amount', 0))
        description = request_res.get("description", 'Y-Club WXminPay')
        payer = {'openid': request_res.get("openid", None)}

        # 以小程序下单为例，下单成功后，将prepay_id和其他必须的参数组合传递给小程序的wx.requestPayment接口唤起支付
        # out_trade_no = ''.join(sample(ascii_letters + digits, 8))
        # description = 'Y-Club WXminPay'
        # amount = 1
        # payer = {'openid': 'demo-openid'}

        code, message = wxpay.pay(
            description=description,    # 商品描述
            out_trade_no=out_trade_no,  # 订单号
            amount={'total': amount},   # 订单金额
            pay_type=WeChatPayType.MINIPROG,    # 支付方式：小程序
            payer=payer # 支付者信息
        )
        result = json.loads(message)
        if code in range(200, 300):
            prepay_id = result.get('prepay_id')
            timestamp = str(int(time.time()))   # 当前时间戳
            noncestr = str(uuid.uuid4()).replace('-', '')   # 生成一个随机字符串
            package = 'prepay_id=' + prepay_id  # 拼接prepay_id参数
            sign = wxpay.sign(data=[APPID, timestamp, noncestr, package])
            signtype = 'RSA'    # 签名方式

            response = {'code': 200, 'result': {
                'appId': APPID,             # 微信公众号ID
                'timeStamp': timestamp,     # 当前时间戳
                'nonceStr': noncestr,       # 随机字符串
                'package': 'prepay_id=%s' % prepay_id,      # 拼接的prepay_id参数
                'signType': signtype,       # 签名方式
                'paySign': sign             # 签名
            }}
            return HttpResponse(json.dumps(response, ensure_ascii=False))
        else:
            response = {'code': -1, 'result': {'reason': result.get('code')}}
            return HttpResponse(json.dumps(response, ensure_ascii=False))

    def get(self, request):
        """
        调用 wxpay.callback 函数处理请求头和请求数据
        """
        request = json.loads(request.body)
        result = wxpay.callback(request.headers, request.data)
        # 如果处理结果存在且事件类型为 'TRANSACTION.SUCCESS'
        if result and result.get('event_type') == 'TRANSACTION.SUCCESS':
            # 从处理结果中获取资源信息
            resp = result.get('resource')
            # 在这里可以写我们的业务处理，必须要返回一个SUCCESS的回复，否则微信会视为没有调用成功，从而一直调用当前请求。

            response = {'code': 'SUCCESS', 'message': '成功'}
            return HttpResponse(json.dumps(response, ensure_ascii=False))

