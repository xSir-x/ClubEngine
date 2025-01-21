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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        act_id = request_res.get('act_id', None)
        assert act_id is not None, Exception("act_id 字段没有传入，请检查...")
        uid = request_res.get('uid', None)
        assert uid is not None, Exception("uid 字段没有传入，请检查...")
        need_fav = request_res.get('need_fav', True)
        assert need_fav is not None, Exception("need_fav 字段没有传入，请检查...")
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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        loc_code = request_res.get('loc_code', None)
        assert loc_code is not None, Exception("loc_code 字段没有传入，请检查...")
        response = getAllType.execute(loc_code=loc_code)
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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        type = request_res.get('type', None)
        assert type is not None, Exception("type 字段没有传入，请检查...")
        loc_code = request_res.get('loc_code', None)
        assert loc_code is not None, Exception("loc_code 字段没有传入，请检查...")
        lang = request_res.get('lang', None)
        assert lang is not None, Exception("lang 字段没有传入，请检查...")
        pageId = request_res.get('pageId', None)
        assert pageId is not None, Exception("pageId 字段没有传入，请检查...")
        pageSize = request_res.get('pageSize', None)
        assert pageSize is not None, Exception("pageSize 字段没有传入，请检查...")
        response, size = getActivitiesByType.execute(type=type, loc_code=loc_code, lang=lang, pageId=pageId,
                                                     pageSize=pageSize)
        message = {"response": response, "total": size, "code": 200, "succeed": True, "msg": message}

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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        loc_code = request_res.get('loc_code', None)
        assert loc_code is not None, Exception("loc_code 字段没有传入，请检查...")
        lang = request_res.get('lang', None)
        assert lang is not None, Exception("lang 字段没有传入，请检查...")
        response = getRecommandActivities.execute(loc_code=loc_code, lang=lang)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        act_id = request_res.get('act_id', None)
        assert act_id is not None, Exception("act_id 字段没有传入，请检查...")
        type = request_res.get('type', None)
        assert type is not None, Exception("type 字段没有传入，请检查...")
        lang = request_res.get('lang', "zh")
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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        uid = request_res.get('uid')
        assert uid is not None, Exception("act_id 字段没有传入，请检查...")
        type = request_res.get('type')
        assert type is not None, Exception("type 字段没有传入，请检查...")
        lang = request_res.get('lang', "zh")
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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        uid = request_res.get('uid')
        assert uid is not None, Exception("uid 字段没有传入，请检查...")
        order_id = request_res.get('order_id')
        assert order_id is not None, Exception("order_id 字段没有传入，请检查...")
        lang = request_res.get('lang', "zh")
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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        need_fav = request_res.get('need_fav', None)
        assert need_fav is not None, Exception("need_fav 字段没有传入，请检查...")
        uid = request_res.get('uid', None)
        assert uid is not None, Exception("uid 字段没有传入，请检查...")
        coop_id = request_res.get('coop_id', None)
        assert coop_id is not None, Exception("coop_id 字段没有传入，请检查...")
        response = addCoopFav().execute(need_fav=need_fav, uid=uid, coop_id=coop_id)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        loc_code = request_res.get('loc_code')
        assert loc_code is not None, Exception("loc_code 字段没有传入，请检查...")
        response = getClubCoopListType().execute(loc_code=loc_code)
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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        type = request_res.get('type', None)
        assert type is not None, Exception("type 字段没有传入，请检查...")
        loc_code = request_res.get('loc_code', None)
        assert loc_code is not None, Exception("loc_code 字段没有传入，请检查...")
        lang = request_res.get('lang', "zh")
        pageId = request_res.get('pageId', None)
        assert pageId is not None, Exception("pageId 字段没有传入，请检查...")
        pageSize = request_res.get('pageSize', None)
        assert pageSize is not None, Exception("pageSize 字段没有传入，请检查...")
        response = getClubCoopListByType().execute(type=type, loc_code=loc_code, lang=lang, pageId=pageId,
                                                   pageSize=pageSize)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        coop_id = request_res.get('coop_id')
        assert coop_id is not None, Exception("coop_id 字段没有传入，请检查...")
        lang = request_res.get('lang')
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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
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
            response = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
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
                store_in_redis(access_token, access_token)
        except Exception as e:
            raise Exception("Redis缓存操作失败...:%s" % e)

        # 设置缓存
        # try:
        #     cached_result = cache.get(access_token)
        #     if cached_result:
        #         cache.delete(access_token)
        # except Exception as e:
        #     message = {"response": {}, "succeed": False, "msg": "access_token 清空失败：%s！" % e}
        #     return HttpResponse(json.dumps(message, ensure_ascii=False))

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
        print(e)
        message = {"response": {}, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！"}

    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def auth_register(request):
    """用户注册:  0: 注册失败，1: 注册成功, 2: 用户已存在"""
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        userid = request_res.get('uid', None)
        name = request_res.get('name', None)
        level = request_res.get('level', None)
        wechat = request_res.get('wechat', None)
        if not wechat:
            message = {"response": 0, "code": 300, "msg": "微信号是必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        profile = request_res.get('profile', None)
        email = request_res.get('email', None)
        if not email:
            message = {"response": 0, "code": 300, "msg": "email是必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        phone_no = request_res.get('phone_no', None)
        location = request_res.get('location', "")
        register_time = timezone.now()

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
            message = {"response": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        uid = request_res.get('uid', None)
        response = getMemberInfo().execute(uid=uid)
        message = {"response": response, "code": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"response": {}, "code": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))
