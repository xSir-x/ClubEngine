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
        need_fav = request_res.get('is_fav', True)
        state, message = addFavActivity.execute(need_fav=need_fav, act_id=act_id, uid=uid)
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
        response = getAllType.execute(loc_code=loc_code)
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
        response = getActivitiesByType.execute(type=type, loc_code=loc_code, lang=lang, uid=uid, pageId=pageId,
                                               pageSize=pageSize)
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
        lang = request_res.get('lang')
        response = getRecommandActivities.execute(loc_code=loc_code, lang=lang)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_single_act_det(request):
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
        lang = request_res.get('lang')
        response = getSingleActivityDetail().execute(act_id=act_id, type=type, lang=lang)
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
        lang = request_res.get('lang', "zh")
        response = getMyActivitiesBytype().execute(uid=uid, type=type, lang=lang)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
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
        access_token = int(request_res.get('access_token', 0))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        uid = request_res.get('uid')
        order_id = request_res.get('order_id')
        lang = request_res.get('lang', "zh")
        response = getMySingleActivity().execute(uid=uid, order_id=order_id, lang=lang)
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
        access_token = int(request_res.get('access_token', "11"))
        if not validate_accessToken(access_token):
            message = {"data": {}, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        need_fav = request_res.get('need_fav', None)
        assert need_fav != None, Exception("need_fav 字段没有传入，请检查...")
        uid = request_res.get('uid', None)
        assert uid != None, Exception("uid 字段没有传入，请检查...")
        coop_id = request_res.get('coop_id', None)
        assert coop_id != None, Exception("coop_id 字段没有传入，请检查...")
        response = addCoopFav().execute(need_fav=need_fav, uid=uid, coop_id=coop_id)
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
        assert loc_code != None, Exception("loc_code 字段没有传入，请检查...")
        response = getClubCoopListType().execute(loc_code=loc_code)
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
        type = request_res.get('type', None)
        assert type != None, Exception("type 字段没有传入，请检查...")
        loc_code = request_res.get('loc_code', None)
        assert loc_code != None, Exception("loc_code 字段没有传入，请检查...")
        lang = request_res.get('lang', None)
        assert lang != None, Exception("lang 字段没有传入，请检查...")
        pageId = request_res.get('pageId', None)
        assert pageId != None, Exception("pageId 字段没有传入，请检查...")
        pageSize = request_res.get('pageSize', None)
        assert pageSize != None, Exception("pageSize 字段没有传入，请检查...")
        response = getClubCoopListByType().execute(type=type, loc_code=loc_code, lang=lang, pageId=pageId,
                                                   pageSize=pageSize)
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
        lang = request_res.get('lang')
        response = getOneCoopDetail().execute(coop_id=coop_id, lang=lang)
        message = {"data": response, "state": 200, "succeed": True, "msg": message}

    except Exception as e:
        message = {"data": {}, "state": 300, "succeed": False, "msg": "您的请求提交不正确或提交格式错误，请检查！[%s]" % e}
    return HttpResponse(json.dumps(message, ensure_ascii=False))




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
