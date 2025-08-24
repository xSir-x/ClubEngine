# -*- coding: utf-8 -*-
import datetime
import random
import base64
import requests
import time
from wxpay.wechatpayv3 import WeChatPay, WeChatPayType
from wxpay.settings import *
from dbModel.models import *

from util.log import logHander

_logger = logHander(__name__)

# 微信支付平台公钥模式初始化，2024年09月之后申请的账号参考使用此模式。
# 平台证书模式向公钥模式切换期间也请使用此方式初始化。
_logger.info("PUBLIC_KEY_ID: %s" % PUBLIC_KEY_ID)
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
            _logger.info(f"HKD to CNY exchange rate: {cny_rate}")
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

        if order_id is None or payer is None or act_id is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return message
        _logger.info("payOrder:: pay amount: %s, act_id: %s, order_id: %s " % (amount, act_id, order_id))

        # 订单验证
        res_obj = UserOrderTable.objects.filter(order_id=order_id)
        if res_obj.exists():
            res_det = res_obj.values("order_time", "exp_time")
            delta_min = 0
            exp_time = 0  # 订单过期时间10分钟
            for det_item in res_det:
                order_time = det_item["order_time"]
                exp_time = det_item["exp_time"]
                delta_min = (int(time.time() * 1000) - int(order_time)) / 60000  # 修改为毫秒计算
            if False and delta_min >= exp_time:  # 订单过期删除
                _logger.info("payOrder:: 订单已过期...")
                response = {'code': 300,
                            'succeed': False,
                            'msg': '订单已过期...'}
                return response
        else:
            _logger.info("payOrder:: 订单不存在...")
            response = {'code': 300,
                        'succeed': False,
                        'msg': '订单不存在...'}
            return response
        _logger.info("payOrder:: 订单验证成功")

        # 金额验证
        act_info_obj = ActivityInfoTable.objects.filter(act_id=act_id)
        if act_info_obj.exists():
            _amount = int(float(act_info_obj.values("price")[0]["price"]) * 100)
            if amount != _amount:
                _logger.info("payOrder:: 金额与用户当前等级不一致，无法支付...")
                response = {'code': 300,
                            'succeed': False,
                            'msg': '金额与用户当前等级不一致，无法支付...'}
                return response
        else:
            _logger.info("payOrder:: 订单对应的活动不存在...")
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
        _logger.info("payOrder:: wx pay code: %s, message: %s" % (code, message ))
        if code in range(200, 300):
            prepay_id = result.get('prepay_id')
            timestamp = str(int(time.time()))  # 当前时间戳: time.time()
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
            pay_time = str(int(time.time() * 1000))  # 修改为毫秒级时间戳
            try:
                UserOrderTable.objects.filter(order_id=order_id).update(order_status=order_status,
                                                                        pay_time=pay_time)
            except Exception as e:
                _logger.info("payOrder:: 支付请求发起失败，order_status入库失败: %s" % e)
            _logger.info("payOrder:: 支付请求发起request失败...")
            response = {'code': 300, 'succeed': False, 'msg': "支付请求发起失败: %s" % result["message"]}
            return response

    @classmethod
    def notify(cls, request):
        """
        支付结果回调处理：调用 wxpay.callback 函数处理请求头和请求数据
        :param request:
        :return:
        """
        try:
            _logger.info("payOrder -> notify:: 支付回调...")
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
                pay_time = str(int(time.time() * 1000))  # 修改为毫秒级时间戳
                paymentid = transaction_id

                UserOrderTable.objects.filter(order_id=order_id).update(order_status=order_status,
                                                                        pay_time=pay_time,
                                                                        paymentid=paymentid)
                _logger.info("payOrder -> notify:: 支付回调成功，order_id: %s, order_status: %s, paymentid: %s 信息入库成功..." %
                             (order_id, order_status, paymentid))
                response = {'code': 200,
                            'succeed': True,
                            'response': {"order_id": order_id,
                                         "paymentid": paymentid,
                                         "trade_state": trade_state,
                                         "trade_state_desc": trade_state_desc,
                                         "bank_type": bank_type,
                                         "amount": amount,
                                         "success_time": success_time},
                            'message': '支付回调成功...'}
                return response
            else:
                _logger.info("支付回调失败...")
                response = {'code': 300, 'succeed': False, 'message': '支付回调失败...'}
                return response
        except Exception as e:
            _logger.error("支付回调异常: %s..." % e)
            raise Exception("**支付回调失败: %s" % e)

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

            if uid is None or act_id is None or coop_id is None:
                message = {"code": 201, "msg": "缺少必填信息..."}
                return message

            res_obj = UserOrderTable.objects.filter(uid=uid, act_id=act_id, coop_id=coop_id)
            if res_obj.exists():
                res_det = res_obj.values("order_id", "order_time", "exp_time", "order_status")
                for det_item in res_det:
                    order_id = det_item["order_id"]
                    order_time = det_item["order_time"]
                    exp_time = det_item["exp_time"]
                    order_status = det_item["order_status"]  # 修正变量名

                    delta_min = (int(time.time() * 1000) - int(order_time)) / 60000  # 修改为毫秒计算
                    if delta_min < exp_time + 3:  # 缓冲时间3分钟
                        if order_status == 2:
                            _logger.info("Order gen:: 订单[%s]已经存在，且已经支付..." % order_id)
                        else:
                            _logger.info("Order gen:: 订单已经存在，且未支付...")
                            message = {'code': 200, 'succeed': True, 'response': {"order_id": order_id},
                                       'msg': '订单已经存在，且未支付...'}
                            return message
                    else:
                        UserOrderTable.objects.filter(uid=uid, act_id=act_id, coop_id=coop_id).delete()

            _logger.info("Order gen:: 不存在未支付订单，重新创建订单...")
            # order_time = timezone.now()
            order_time = str(int(time.time() * 1000))  # 修改为毫秒级时间戳
            # t_time = time.localtime(float(order_time))
            exp_time = 30  # 默认过期时间30分钟
            order_status = 1  # 订单状态：1-未支付 2-支付成功 3-支付失败
            random_bytes = os.urandom(16)
            random_string = base64.urlsafe_b64encode(random_bytes).decode('utf-8')[:16]  # 取前16个字符以匹配长度需求
            order_id = f'{str(int(time.time() * 1000))}-{random.randint(1000, 9999)}-{random_string}'  # 修改为毫秒级时间戳
            UserOrderTable.objects.create(order_id=order_id,
                                          uid=uid,
                                          act_id=act_id,
                                          coop_id=coop_id,
                                          pay_time=order_time,
                                          order_time=order_time,
                                          exp_time=exp_time,
                                          paymentid="",
                                          order_status=order_status)
            _logger.info("Order gen:: 订单创建成功, order_id: %s" % order_id)
            message = {'code': 200, 'succeed': True, 'response': {"order_id": order_id}, 'msg': '订单创建成功...'}
            return message
        except Exception as e:
            message = {'code': 300, 'succeed': False, 'msg': '订单创建失败: %s' % e}
            return message

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
