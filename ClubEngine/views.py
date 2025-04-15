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
from util.external_api import get_openid, validate_accessToken, store_in_redis, retrieve_from_redis
from django.core.cache import cache
from dbModel.views import *
from wxpay.views import *
from django_redis import get_redis_connection
import json
from util.log import logHander

_logger = logHander(__name__)


@csrf_exempt
def add_fav_act(request):
    """
    收藏活动
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        act_id = request_res.get('act_id', None)
        uid = request_res.get('uid', None)
        need_fav = request_res.get('need_fav', True)

        if act_id is None or uid is None or need_fav is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        _logger.info("Request:: 发起活动收藏...")
        state, message = addFavActivity.execute(need_fav=need_fav, act_id=act_id, uid=uid)
        message = {"response": state, "code": 200, "succeed": False, "msg": message}

    except Exception as e:
        message = {"response": 0, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_all_type(request):
    """
    获取所有活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        loc_code = request_res.get('loc_code', None)
        lang = request_res.get('lang', None)

        if loc_code is None or lang is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        _logger.info("Request:: 获取所有活动类型...")
        response = getAllType.execute(loc_code=loc_code, lang=lang)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_acts_bytype(request):
    """
    根据类型获取活动列表
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        type = request_res.get('type', None)
        loc_code = request_res.get('loc_code', None)
        lang = request_res.get('lang', None)
        pageId = request_res.get('pageId', 0)
        pageSize = request_res.get('pageSize', 10)

        if type is None or loc_code is None or lang is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        _logger.info("Request:: 根据类型获取活动列表, type: %s, loc_code: %s, lang: %s" % (type, loc_code, lang))
        page_res, size = getActivitiesByType.execute(type=type, loc_code=loc_code, lang=lang, pageId=pageId,
                                                     pageSize=pageSize)
        message = {"response": page_res, "total": size, "code": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"response": {}, "total": 0, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_recomm_acts(request):
    """
    获取活动推荐列表
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        loc_code = request_res.get('loc_code', None)
        lang = request_res.get('lang', None)

        if loc_code is None or lang is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        response = getRecommandActivities.execute(loc_code=loc_code, lang=lang)
        message = {"response": response, "code": 200, "succeed": True, "msg": "OK!"}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_single_act_det(request):
    """
    获取单个活动细节
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        act_id = request_res.get('act_id', None)
        type = request_res.get('type', None)
        lang = request_res.get('lang', "zh")

        if type is None or act_id is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        response = getSingleActivityDetail().execute(act_id=act_id, type=type, lang=lang)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_my_acts_bytype(request):
    """
    获取我的活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        uid = request_res.get('uid', None)
        type = request_res.get('type', None)
        lang = request_res.get('lang', "zh")

        if type is None or uid is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        response = getMyActivitiesBytype().execute(uid=uid, type=type, lang=lang)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_my_act(request):
    """

    :param request:
    :return:
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        uid = request_res.get('uid', None)
        order_id = request_res.get('order_id', None)
        lang = request_res.get('lang', "zh")

        if uid is None or order_id is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        response = getMySingleActivity().execute(uid=uid, order_id=order_id, lang=lang)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def add_coopfav(request):
    """
    获取我的活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        need_fav = request_res.get('need_fav', None)
        uid = request_res.get('uid', None)
        coop_id = request_res.get('coop_id', None)

        if need_fav is None or uid is None or coop_id is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        state, msg = addCoopFav().execute(need_fav=need_fav, uid=uid, coop_id=coop_id)
        message = {"response": state, "code": 200, "succeed": True, "msg": msg}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_cooplist_type(request):
    """
    获取我的活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        lang = request_res.get('lang', None)
        loc_code = request_res.get('loc_code', None)

        if lang is None or loc_code is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        response = getClubCoopListType().execute(loc_code=loc_code, lang=lang)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_coopdet_bytype(request):
    """
    获取我的活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        type = request_res.get('type', None)
        loc_code = request_res.get('loc_code', None)
        lang = request_res.get('lang', "zh")
        pageId = request_res.get('pageId', 0)
        pageSize = request_res.get('pageSize', 10)

        if type is None or loc_code is None or lang is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        page_res, total_size = getClubCoopListByType(). \
            execute(type=type, loc_code=loc_code, lang=lang, pageId=pageId, pageSize=pageSize)
        message = {"response": page_res, "total": total_size, "code": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_coopdet(request):
    """
    获取我的活动类型
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        coop_id = request_res.get('coop_id')
        lang = request_res.get('lang')

        if coop_id is None or lang is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        response = getOneCoopDetail().execute(coop_id=coop_id, lang=lang)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def modify_membership(request):
    """
    修改会员信息
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        uid = request_res.get('uid', None)
        name = request_res.get('name', None)
        wechat = request_res.get('wechat', None)
        pic = request_res.get('pic', None)
        email = request_res.get('email', None)
        profile = request_res.get('profile', None)
        phone_no = request_res.get('phone_no', None)
        location = request_res.get('location', None)
        state, msg = modifyMembership().execute(uid=uid, name=name, wechat=wechat, pic=pic, email=email,
                                                profile=profile, phone_no=phone_no, location=location)
        message = {"response": state, "code": 200, "succeed": True, "msg": msg}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


# TODO: 订单接口

@csrf_exempt
def minipay(request):
    """小程序支付"""
    response = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"response": {},
                       "code": 300,
                       "succeed": False,
                       "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        response = WXMinPay().pay_miniprog(request=request)

    except Exception as e:
        response = {"response": {},
                    "code": 300,
                    "succeed": False,
                    "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(response, ensure_ascii=False))


@csrf_exempt
def mininotify(request):
    """小程序支付回调"""
    response = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            response = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(response, ensure_ascii=False))

        response = WXMinPay().notify(request=request)
    except Exception as e:
        response = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(response, ensure_ascii=False))


@csrf_exempt
def genorder(request):
    """小程序订单生成"""
    response = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"response": {}, "code": 200, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        response = WXMinPay().gen_order(request=request)
    except Exception as e:
        response = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(response, ensure_ascii=False))


@csrf_exempt
def search_order(request):
    """小程序订单查询"""
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        response = WXMinPay().search_order(request=request)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


# TODO: 用户登录接口
@csrf_exempt
def auth_user(request):
    try:
        request_res = json.loads(request.body)
        js_code = request_res.get("js_code", None)
        if not js_code:
            message = {"response": {}, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，JS_CODE为空，请检查！"}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        # js_code = int(request.GET['js_code'])
        # 请求腾讯api得到openid
        openid = get_openid(js_code)
        # 下发本次登陆token，后续请求验证
        timestamp_milliseconds = str(int(time.time() * 1000))
        byte_str = (openid[0] + timestamp_milliseconds + openid[1:])
        access_token = byte_str
        # 缓存access_token
        try:
            res = retrieve_from_redis(access_token)
            if not res:
                store_in_redis(access_token, 1)
        except Exception as e:
            raise Exception("Redis缓存操作失败...:%s" % e)

        message = {
            "code": 200,
            "result": {"access_token": access_token, "openid": openid},
            "succeed": True,
            "msg": "本次下发用户token为: " + access_token}

    except Exception as e:
        message = {"code": 300,
                   "result": {},
                   "succeed": False,
                   "msg": "您的请求提交不正确或提交格式错误，请检查: %s！" % e}

    return HttpResponse(json.dumps(message, ensure_ascii=False))


# 示例函数--测试access_token有效
def test_access(request):
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"response": {}, "succeed": False, "msg": "invalidate access token"}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        # 继续写业务逻辑
        print("validate access token")

    except Exception as e:
        message = {"response": {}, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查: %s" % e}

    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def auth_register(request):
    """用户注册:  0: 注册失败，1: 注册成功, 2: 用户已存在"""
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        userid = request_res.get('uid', None)
        name = request_res.get('name', None)
        level = request_res.get('level', None)
        wechat = request_res.get('wechat', None)
        profile = request_res.get('profile', None)
        email = request_res.get('email', None)
        phone_no = request_res.get('phone_no', None)
        location = request_res.get('location', "")
        register_time = str(int(time.time()))

        if wechat is None or name is None or email is None:
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        state, msg = registerMembership().execute(userid, name, level, wechat, profile, email, phone_no, location,
                                                  register_time)

        message = {"response": state, "code": 200, "msg": msg}

    except Exception as e:
        message = {"response": 0, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def search_user(request):
    """用户信息查询"""
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        uid = request_res.get('uid', None)
        response = getMemberInfo().execute(uid=uid)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))
