# -*- coding: utf-8 -*-


from django.shortcuts import render
from django.views.decorators import csrf
# from dbModel.models import orders
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User
import time
import hashlib
import json
from util.external_api import get_openid, validate_accessToken
from django.core.cache import cache


def validate_accessToken(access_token):
    """
    访问权限验证
    """

    return True

@csrf_exempt
def add_fav_act(request):
    """
    收藏活动
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        act_id = request_res.get('act_id', '')
        uid = request_res.get('uid', '')
        state, message = addFavActivity.execuate(act_id=act_id, uid=uid)
        message = {"status": state, "state": 200, "succeed": False, "msg": message}

    except Exception as e:
        message = {"status": 0, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_all_type(request):
    """
    获取所有活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        loc_code = request_res.get('loc_code', "")
        response = getAllType.execuate(loc_code=loc_code)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))

@csrf_exempt
def get_acts_bytype(request):
    """
    根据类型获取活动列表
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        type = request_res.get('type')
        loc_code = request_res.get('loc_code')
        lang = request_res.get('lang')
        uid = request_res.get('uid')
        pageId = request_res.get('pageId')
        pageSize = request_res.get('pageSize')
        response = getActivitiesByType.execuate(type=type, loc_code=loc_code, lang=lang, uid=uid, pageId=pageId, pageSize=pageSize)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_recomm_acts(request):
    """
    获取活动推荐列表
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        loc_code = request_res.get('loc_code')
        response = getRecommandActivities.execuate(loc_code=loc_code)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_recomm_acts(request):
    """
    获取活动推荐列表
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        loc_code = request_res.get('loc_code')
        response = getRecommandActivities.execuate(loc_code=loc_code)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_act_det(request):
    """
    获取单个活动细节
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        act_id = request_res.get('act_id')
        type = request_res.get('type')
        response = getSingleActivityDetail().execuate(act_id=act_id, type=type)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_my_acts_bytype(request):
    """
    获取我的活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        uid = request_res.get('uid')
        type = request_res.get('type')
        response = getMyActivitiesBytype().execuate(uid=uid, type=type)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_my_act(request):
    """
    获取我的活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        uid = request_res.get('uid')
        order_id = request_res.get('order_id')
        response = getMySingleActivity().execuate(uid=uid, order_id=order_id)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))




@csrf_exempt
def add_coopfav(request):
    """
    获取我的活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        uid = request_res.get('uid')
        coop_id = request_res.get('coop_id')
        response = addCoopFav().execuate(uid=uid, coop_id=coop_id)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_cooplist_type(request):
    """
    获取我的活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        loc_code = request_res.get('loc_code')
        response = getClubCoopListType().execuate(loc_code=loc_code)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_coopdet_bytype(request):
    """
    获取我的活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        loc_code = request_res.get('loc_code')
        response = getClubCoopListByType().execuate(loc_code=loc_code)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_coopdet(request):
    """
    获取我的活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        coop_id = request_res.get('coop_id')
        response = getOneCoopDetail().execuate(coop_id=coop_id)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))





# 接收POST请求数据
@csrf_exempt
# def add(request):
#
#     try:
#
#         data = eval(bytes.decode(request.body))
#         print(data["orderId"])
#         orderId = data["orderId"]
#         orderTime = data["orderTime"]
#         skuId = data["skuId"]
#         userId = data["userId"]
#         status = data["status"]
#         price = data["price"]
#         pay = data["pay"]
#         if orders.objects.filter(orderId=orderId):
#             orders.objects.filter(orderId=orderId).update(orderTime=orderTime, skuId=skuId, userId=userId, status=status, price=price, pay=pay)
#             message = {"data": {}, "succeed": True, "msg": "已存在orderId={}的订单，订单数据修改成功！，当前订单数：{}".format(orderId, len(orders.objects.all()))}
#         else:
#             neworder = orders(orderId=orderId, orderTime=orderTime, skuId=skuId, userId=userId, status=status, price=price, pay=pay)
#             neworder.save()
#             message = {"data": {}, "succeed": True, "msg": "新增订单数据成功，当前订单数：{}".format(len(orders.objects.all()))}
#     except Exception as e:
#         message = {"data": {}, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！"}
#
#     return HttpResponse(json.dumps(message, ensure_ascii=False))
#
#
# def user_orders(request):
#
#     try:
#         userId = request.GET['userId']
#         orderlist = orders.objects.filter(userId=userId)
#         user_order = []
#         for data in orderlist:
#             user_order.append({"orderId": data.orderId,
#                                "orderTime": data.orderTime,
#                                "skuId": data.skuId,
#                                "userId": data.userId,
#                                "status": data.status,
#                                "price": data.price,
#                                "pay": data.pay})
#
#         message = {"data": {"user_orders": user_order}, "succeed": True, "msg": "已成功查询到用户订单数量：{}".format(len(user_order))}
#     except Exception as e:
#         message = {"data": {}, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！"}
#
#     return HttpResponse(json.dumps(message, ensure_ascii=False))
#
#
# def pay_rate(request):
#
#     try:
#         skuId = request.GET['skuId']
#         orderlist = orders.objects.filter(skuId=skuId)
#         order_num = len(orderlist)
#         pay_num = 0
#         for data in orderlist:
#             if data.status == 1:
#                 pay_num += 1
#         if order_num == 0:
#             message = {"data": {}, "succeed": False, "msg": "未查询到该skuId"}
#         else:
#             payrate = float(pay_num)/float(order_num)
#             message = {"data": {"skuId": skuId, "order_num": order_num, "pay_num": pay_num, "pay_rate": payrate}, "succeed": True, "msg": "已成功查询到skuId={}的订单共有{}个，其中已付款{}个，实际付款率为{}（付款数/订单总数）".format(skuId, order_num, pay_num, payrate)}
#     except Exception as e:
#         message = {"data": {}, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！"}
#
#     return HttpResponse(json.dumps(message, ensure_ascii=False))


# def get_top(request):
#
#     try:
#         starttime = int(request.GET['starttime'])
#         endtime = int(request.GET['endtime'])
#         print(starttime, endtime)
#         orderlist = []
#         for data in orders.objects.all():
#             if data.orderTime >= starttime and data.orderTime <= endtime:
#                 orderlist.append(data)
#
#         sku_done = {}
#         for order in orderlist:
#             if order.status == 1:
#                 try:
#                     sku_done[str(order.skuId)] += 1
#                 except Exception as e:
#                     sku_done[str(order.skuId)] = 1
#
#         print(sku_done)
#
#         topsku = []
#
#         for obj in sorted(sku_done.items(), key=lambda kv: (kv[1], kv[0])):
#             topsku.append(obj[0])
#         print(topsku)
#
#         message = {"data": {"top10_skuId": topsku[:10]}, "succeed": True, "msg": "已成功获取并分析从{}到{}的共{}个订单，共{}个成交的skuId，已按正序已列出成交额top10的skuId.".format(starttime, endtime, len(orderlist), len(topsku))}
#
#     except Exception as e:
#         message = {"data": {}, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！"}
#
#     return HttpResponse(json.dumps(message, ensure_ascii=False))


def auth_user(request):
    try:
        js_code = int(request.GET['js_code'])
        #请求腾讯api得到openid
        openid = get_openid(js_code)
        #下发本次登陆token，后续请求验证
        timestamp_milliseconds = str(int(time.time() * 1000))
        byte_str = (openid[0]+timestamp_milliseconds+openid[1:])
        access_token = byte_str
        print('access_token:', access_token)
        #缓存access_token
        # 设置缓存
        try:
            cache.delete(access_token)
        except Exception as e:
            print(e)

        cache.set(access_token, 1, timeout=5)  # timeout 以秒为单位
        message = {"data": {"access_token": access_token,"uid":openid}, "succeed": True, "msg": "本次下发用户token为: "+access_token}

    except Exception as e:
        print(e)
        message = {"data": {}, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！"}

    return HttpResponse(json.dumps(message, ensure_ascii=False))

#示例函数--测试access_token有效
def test_access(request):
    try:
        access_token = int(request.GET['access_token'])
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "invalidate access token"}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        #继续写业务逻辑
        print("validate access token")

    except Exception as e:
        print(e)
        message = {"data": {}, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！"}

    return HttpResponse(json.dumps(message, ensure_ascii=False))
