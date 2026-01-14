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
            _logger.info("payOrder -> notify:: 收到微信支付回调...")
            
            # Django 标准请求使用 request.body，不是 request.data
            result = wxpay.callback(request.headers, request.body)
            
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
                
                _logger.info("payOrder -> notify:: 微信回调数据解析成功, order_id: %s, transaction_id: %s, amount: %s" % 
                           (order_id, transaction_id, amount))
                
                # 在这里可以写我们的业务处理，必须要返回一个SUCCESS的回复，否则微信会视为没有调用成功，从而一直调用当前请求。
                order_status = 2
                pay_time = str(int(time.time() * 1000))  # 修改为毫秒级时间戳
                paymentid = transaction_id

                UserOrderTable.objects.filter(order_id=order_id).update(
                    order_status=order_status,
                    pay_time=pay_time,
                    paymentid=paymentid
                )

                order= UserOrderTable.objects.get(order_id=order_id)
                course_id = order.act_id
                user_id = order.uid
                # 2. 更新报名记录
                enrollment = CourseEnrollmentTable.objects.filter(
                    course_id=course_id,
                    user_id=user_id,
                    payment_status=1  # 待支付
                ).first()
                
                if not enrollment:
                    response = {'code': 300, 'succeed': False, 'message': '支付回调失败...课程记录不存在'}
                    return response
                
                # 更新支付状态
                enrollment.payment_status = 2  # 已支付
                enrollment.enrollment_status = 1  # 已报名
                enrollment.order_id = order_id
                enrollment.save()
                
                # 3. 更新课程报名人数
                course = CoachCourseTable.objects.get(course_id=course_id, is_deleted=False)
                paid_enrollments = CourseEnrollmentTable.objects.filter(
                    course_id=course_id,
                    payment_status=2,
                    enrollment_status=1
                ).count()
                course.current_students = paid_enrollments
                course.save()


                _logger.info("payOrder -> notify:: 支付回调成功，order_id: %s, order_status: %s, paymentid: %s 信息入库成功..." %
                             (order_id, order_status, paymentid))              
                
                response = {
                    'code': 200,
                    'succeed': True,
                    'response': {
                        "order_id": order_id,
                        "paymentid": paymentid,
                        "trade_state": trade_state,
                        "trade_state_desc": trade_state_desc,
                        "bank_type": bank_type,
                        "amount": amount,
                        "success_time": success_time
                    },
                    'message': '支付回调成功...'
                }
                return response
            else:
                _logger.warning("payOrder -> notify:: 支付回调失败，事件类型不匹配或结果为空")
                response = {'code': 300, 'succeed': False, 'message': '支付回调失败...'}
                return response
                
        except Exception as e:
            _logger.error("payOrder -> notify:: 支付回调异常: %s" % str(e), exc_info=True)
            response = {'code': 300, 'succeed': False, 'message': '支付回调处理失败: %s' % str(e)}
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
            random_string = base64.urlsafe_b64encode(random_bytes).decode('utf-8')[:12]  # 取前16个字符以匹配长度需求
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

    @classmethod
    def refund(cls, request):
        """
        发起退款
        POST /refundOrder
        请求参数:
        {
            "access_token": "xxx",
            "order_id": "订单ID",
            "refund_reason": "退款原因",
            "refund_amount": 150.00  # 可选，不传则全额退款
        }
        """
        try:
            request_res = json.loads(request.body)
            order_id = request_res.get("order_id", None)
            refund_reason = request_res.get("refund_reason", "用户申请退款")
            refund_amount_yuan = request_res.get("refund_amount", None)  # 元
            
            if not order_id:
                return {'code': 400, 'succeed': False, 'msg': '订单ID不能为空'}
            
            # 1. 查询原订单
            try:
                order = UserOrderTable.objects.get(order_id=order_id)
            except UserOrderTable.DoesNotExist:
                return {'code': 404, 'succeed': False, 'msg': '订单不存在'}
            
            # 2. 验证订单状态
            if order.order_status != 2:
                return {'code': 400, 'succeed': False, 'msg': '订单未支付，无法退款'}
            
            if not order.paymentid:
                return {'code': 400, 'succeed': False, 'msg': '订单无支付记录'}
            
            # 3. 查询订单金额（从活动表或课程表）
            total_amount = 0
            course_id = None
            enrollment_id = None
            
            # 优先查询课程报名
            enrollment = CourseEnrollmentTable.objects.filter(
                order_id=order_id
            ).first()
            
            if enrollment:
                total_amount = int(float(enrollment.paid_amount) * 100)  # 转为分
                course_id = enrollment.course_id
                enrollment_id = enrollment.enrollment_id
                
                # 检查是否已退款
                if enrollment.payment_status == 3:
                    return {'code': 400, 'succeed': False, 'msg': '该课程已退款'}
            else:
                # 查询活动信息
                activity = ActivityInfoTable.objects.filter(act_id=order.act_id).first()
                if activity:
                    total_amount = int(float(activity.price) * 100)
            
            if total_amount == 0:
                return {'code': 400, 'succeed': False, 'msg': '无法获取订单金额'}
            
            # 4. 计算退款金额
            if refund_amount_yuan:
                refund_amount = int(float(refund_amount_yuan) * 100)
                if refund_amount > total_amount:
                    return {'code': 400, 'succeed': False, 'msg': '退款金额不能超过订单金额'}
            else:
                refund_amount = total_amount  # 全额退款
            
            # 5. 生成退款单号
            refund_id = f"REFUND-{order_id}-{int(time.time() * 1000)}-{uuid.uuid4().hex[:8]}"
            
            # 6. 检查是否已有退款记录
            existing_refund = RefundOrderTable.objects.filter(
                order_id=order_id,
                refund_status__in=[1, 2]  # 退款中或已成功
            ).first()
            
            if existing_refund:
                return {
                    'code': 400, 
                    'succeed': False, 
                    'msg': f'订单已有退款记录: {existing_refund.refund_id}'
                }
            
            # 7. 调用微信退款API
            _logger.info(f"Refund:: 发起退款, order_id: {order_id}, refund_id: {refund_id}, "
                        f"total: {total_amount}, refund: {refund_amount}")
            
            # 导入退款回调URL
            from wxpay.settings import REFUND_NOTIFY_URL
            
            code, message = wxpay.refund(
                out_refund_no=refund_id,  # 商户退款单号
                out_trade_no=order_id,  # 原商户订单号
                amount={
                    'refund': refund_amount,  # 退款金额（分）
                    'total': total_amount,  # 原订单金额（分）
                    'currency': 'CNY'
                },
                reason=refund_reason,  # 退款原因
                notify_url=REFUND_NOTIFY_URL  # 退款回调地址
            )
            
            result = json.loads(message)
            _logger.info(f"Refund:: 微信退款API响应, code: {code}, message: {message}")
            
            # 8. 创建退款记录
            refund_time = str(int(time.time() * 1000))
            
            if code in range(200, 300):
                # 退款请求成功
                wx_refund_id = result.get('refund_id', '')
                refund_status = 1  # 退款中
                
                RefundOrderTable.objects.create(
                    refund_id=refund_id,
                    order_id=order_id,
                    transaction_id=order.paymentid,
                    user_id=order.uid,
                    total_amount=total_amount,
                    refund_amount=refund_amount,
                    refund_reason=refund_reason,
                    refund_status=refund_status,
                    refund_time=refund_time,
                    wx_refund_id=wx_refund_id,
                    course_id=course_id,
                    enrollment_id=enrollment_id
                )
                
                _logger.info(f"Refund:: 退款记录创建成功, refund_id: {refund_id}")
                
                return {
                    'code': 200,
                    'succeed': True,
                    'msg': '退款申请提交成功，预计1-3个工作日到账',
                    'response': {
                        'refund_id': refund_id,
                        'wx_refund_id': wx_refund_id,
                        'refund_amount': refund_amount / 100,
                        'status': '退款中'
                    }
                }
            else:
                # 退款失败
                error_msg = result.get('message', '退款失败')
                _logger.error(f"Refund:: 退款失败, error: {error_msg}")
                
                # 仍然创建退款记录，状态为失败
                RefundOrderTable.objects.create(
                    refund_id=refund_id,
                    order_id=order_id,
                    transaction_id=order.paymentid,
                    user_id=order.uid,
                    total_amount=total_amount,
                    refund_amount=refund_amount,
                    refund_reason=refund_reason,
                    refund_status=3,  # 退款失败
                    refund_time=refund_time,
                    course_id=course_id,
                    enrollment_id=enrollment_id
                )
                
                return {
                    'code': 400,
                    'succeed': False,
                    'msg': f'退款失败: {error_msg}'
                }
                
        except Exception as e:
            _logger.error(f"Refund:: 退款异常: {str(e)}", exc_info=True)
            return {'code': 500, 'succeed': False, 'msg': f'退款异常: {str(e)}'}
    
    @classmethod
    def refund_notify(cls, request):
        """
        退款结果回调处理
        POST /notifyRefund
        支持的事件类型：
        - REFUND.SUCCESS: 退款成功
        - REFUND.CLOSED: 退款关闭
        - REFUND.ABNORMAL: 退款异常
        """
        try:
            _logger.info("Refund Notify:: 收到微信退款回调...")
            
            # 处理退款通知
            result = wxpay.callback(request.headers, request.body)
            
            if not result:
                _logger.error("Refund Notify:: 回调数据解析失败")
                return {'code': 400, 'succeed': False, 'message': '回调数据解析失败'}
            
            event_type = result.get('event_type', '')
            _logger.info(f"Refund Notify:: 事件类型: {event_type}")
            
            # 支持多种退款事件类型
            if event_type in ['REFUND.SUCCESS', 'REFUND.CLOSED', 'REFUND.ABNORMAL']:
                resp = result.get('resource')
                if not resp:
                    _logger.error("Refund Notify:: 回调资源数据为空")
                    return {'code': 400, 'succeed': False, 'message': '回调资源数据为空'}
                
                refund_id = resp.get('out_refund_no')  # 商户退款单号
                wx_refund_id = resp.get('refund_id')  # 微信退款单号
                refund_status_text = resp.get('refund_status')  # SUCCESS/CLOSED/ABNORMAL
                success_time = resp.get('success_time', '')
                amount = resp.get('amount', {})
                
                _logger.info(f"Refund Notify:: 退款回调数据, refund_id: {refund_id}, "
                           f"wx_refund_id: {wx_refund_id}, status: {refund_status_text}")
                
                # 查询退款记录
                refund_record = RefundOrderTable.objects.filter(refund_id=refund_id).first()
                if not refund_record:
                    _logger.error(f"Refund Notify:: 退款记录不存在: {refund_id}")
                    return {'code': 404, 'succeed': False, 'message': '退款记录不存在'}
                
                # 根据事件类型更新退款状态
                if event_type == 'REFUND.SUCCESS':
                    # 退款成功
                    refund_record.refund_status = 2  # 退款成功
                    refund_record.success_time = str(int(time.time() * 1000))
                    refund_record.wx_refund_id = wx_refund_id
                    refund_record.save()
                    
                    # 更新原订单状态
                    UserOrderTable.objects.filter(order_id=refund_record.order_id).update(
                        refund_status=2  # 全额退款
                    )
                    
                    # 更新课程报名状态
                    if refund_record.enrollment_id:
                        CourseEnrollmentTable.objects.filter(
                            enrollment_id=refund_record.enrollment_id
                        ).update(
                            payment_status=3,  # 已退款
                            enrollment_status=2,  # 已取消
                            cancel_time=str(int(time.time() * 1000))
                        )
                        
                        # 更新课程报名人数
                        if refund_record.course_id:
                            course = CoachCourseTable.objects.filter(
                                course_id=refund_record.course_id
                            ).first()
                            if course:
                                course.current_students = max(0, course.current_students - 1)
                                course.save()
                    
                    _logger.info(f"Refund Notify:: 退款成功，状态更新完成")
                    
                elif event_type == 'REFUND.CLOSED':
                    # 退款关闭
                    refund_record.refund_status = 4  # 退款关闭
                    refund_record.save()
                    _logger.info(f"Refund Notify:: 退款关闭")
                    
                elif event_type == 'REFUND.ABNORMAL':
                    # 退款异常
                    refund_record.refund_status = 3  # 退款失败
                    refund_record.save()
                    _logger.warning(f"Refund Notify:: 退款异常")
                
                return {
                    'code': 200,
                    'succeed': True,
                    'message': '退款回调处理成功'
                }
            else:
                _logger.warning(f"Refund Notify:: 未知的事件类型: {event_type}")
                return {'code': 400, 'succeed': False, 'message': f'未知的事件类型: {event_type}'}
                
        except Exception as e:
            _logger.error(f"Refund Notify:: 退款回调异常: {str(e)}", exc_info=True)
            return {'code': 500, 'succeed': False, 'message': f'退款回调异常: {str(e)}'}
    
    @classmethod
    def query_refund(cls, request):
        """
        查询退款状态
        POST /queryRefund
        请求参数:
        {
            "access_token": "xxx",
            "refund_id": "退款单号"  # 或者 "order_id": "订单号"
        }
        """
        try:
            request_res = json.loads(request.body)
            refund_id = request_res.get("refund_id", None)
            order_id = request_res.get("order_id", None)
            
            if not refund_id and not order_id:
                return {'code': 400, 'succeed': False, 'msg': '退款单号或订单号不能为空'}
            
            # 查询退款记录
            if refund_id:
                refunds = RefundOrderTable.objects.filter(refund_id=refund_id)
            else:
                refunds = RefundOrderTable.objects.filter(order_id=order_id)
            
            if not refunds.exists():
                return {'code': 404, 'succeed': False, 'msg': '未找到退款记录'}
            
            refund_list = []
            for refund in refunds:
                status_text = {
                    1: '退款中',
                    2: '退款成功',
                    3: '退款失败',
                    4: '退款关闭'
                }.get(refund.refund_status, '未知')
                
                refund_list.append({
                    'refund_id': refund.refund_id,
                    'order_id': refund.order_id,
                    'refund_amount': float(refund.refund_amount) / 100,
                    'total_amount': float(refund.total_amount) / 100,
                    'refund_reason': refund.refund_reason,
                    'refund_status': refund.refund_status,
                    'status_text': status_text,
                    'refund_time': refund.refund_time,
                    'success_time': refund.success_time,
                    'wx_refund_id': refund.wx_refund_id
                })
            
            return {
                'code': 200,
                'succeed': True,
                'msg': '查询成功',
                'response': refund_list
            }
            
        except Exception as e:
            _logger.error(f"Query Refund:: 查询退款异常: {str(e)}", exc_info=True)
            return {'code': 500, 'succeed': False, 'msg': f'查询退款异常: {str(e)}'}


if __name__ == '__main__':
    pass
