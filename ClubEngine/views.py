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
        profile = request_res.get('profile', None)
        location = request_res.get('location', "")
        register_time = str(int(time.time() * 1000))  # 修改为毫秒级时间戳

        if name is None:
            message = {"code": 201, "msg": "缺少名称信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        state, msg = registerMembership().execute(userid, name, profile, location,
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


@csrf_exempt
def send_invitation(request):
    """
    发送邀请
    前端传入字段:
    inviteeId: 被邀请人ID
    inviterId: 邀请人ID
    matchTime: 比赛时间戳
    msg: 邀请消息
    place: 地点
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        inviteeId = request_res.get('inviteeId', None)
        inviterId = request_res.get('inviterId', None)
        matchTime = request_res.get('matchTime', None)
        msg = request_res.get('msg', "")
        place = request_res.get('place', None)
        
        if not all([inviteeId, inviterId, matchTime, place]):
            message = {"code": 201, "msg": "缺少必填信息..."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        # TODO: 在这里实现邀请逻辑
        # 例如：创建邀请记录，发送通知等
        success,message = createInvitation().execute(inviterId, inviteeId, matchTime, msg,
                                                  place)
        
        if success == 1:
            message = {"response": 1, "code": 200, "succeed": True, "msg": "邀请创建成功: "+str(message)}
        elif success == 2:
            message = {"response": 2, "code": 300, "succeed": False, "msg": "邀请已存在"}
        else:
            _logger.error("数据库异常: "+str(message))
            message = {"response": 0, "code": 400, "succeed": False, "msg": "数据库操作失误: "+str(message)}

    except Exception as e:
        message = {"response": 0, "code": 500, "succeed": False, "msg": f"您的请求提交不正确或提交格式错误，请检查！[{str(e)}]"}
    
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_invitation(request):
    """
    获取邀请列表
    前端传入字段:
    access_token: 访问令牌
    inviterId: 邀请人ID (可选)
    inviteeId: 被邀请人ID (可选)
    status: 邀请状态 (可选): 0-待处理，1-已接受，2-已拒绝，3-已过期
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        # 获取可选参数
        inviterId = request_res.get('inviterId', None)
        inviteeId = request_res.get('inviteeId', None)
        status = request_res.get('status', None)
        
        # 至少需要提供一个ID参数
        if not inviterId and not inviteeId:
            message = {"code": 201, "succeed": False, "msg": "至少需要提供inviterId或inviteeId参数"}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
            
        # 如果status是字符串，转换为整数
        if status is not None:
            try:
                status = int(status)
            except ValueError:
                message = {"code": 201, "succeed": False, "msg": "status参数必须是数字"}
                return HttpResponse(json.dumps(message, ensure_ascii=False))
        
        # 获取邀请列表
        invitations = getInvitationByStatus().execute(
            inviterId=inviterId,
            inviteeId=inviteeId,
            status=status
        )
        
        message = {"response": invitations, "code": 200, "succeed": True, "msg": "获取邀请列表成功"}
        
    except Exception as e:
        message = {"response": [], "code": 300, "succeed": False, "msg": f"获取邀请列表失败：{str(e)}"}
        
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def update_invitation(request):
    """
    更新邀请状态
    前端传入字段:
    access_token: 访问令牌
    inv_id: 邀请ID
    inviterId: 邀请者ID
    inviteeId: 被邀请者ID
    action: 操作类型 (accept-接受, reject-拒绝)
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        # 获取必需参数
        inv_id = request_res.get('inv_id', None)
        inviterId = request_res.get('inviterId', None)
        inviteeId = request_res.get('inviteeId', None)
        action = request_res.get('action', None)
        
        # 验证必需参数
        if not all([inv_id, inviterId, inviteeId, action]):
            message = {"code": 201, "succeed": False, "msg": "缺少必填信息 (inv_id, inviterId, inviteeId, action)"}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
            
        # 验证action参数
        if action not in ['accept', 'reject']:
            message = {"code": 201, "succeed": False, "msg": "action参数必须是 'accept' 或 'reject'"}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        
        # 调用updateInvitation执行更新操作
        state, msg = updateInvitation.execute(
            inv_id=inv_id,
            inviterId=inviterId,
            inviteeId=inviteeId,
            action=action,
            access_token=access_token
        )
        
        if state == 1:
            message = {"response": 1, "code": 200, "succeed": True, "msg": msg}
        else:
            message = {"response": 0, "code": 400, "succeed": False, "msg": msg}
        
    except Exception as e:
        _logger.error(f"更新邀请状态接口异常: {str(e)}")
        message = {"response": 0, "code": 500, "succeed": False, "msg": f"更新邀请状态失败：{str(e)}"}
        
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def get_friends(request):
    """
    获取用户好友列表
    前端传入字段:
    access_token: 访问令牌
    userId: 用户ID
    friendshipCreateTime: 好友关系创建时间过滤条件 (可选)，只返回大于等于此时间的好友
    """
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))

        # 获取必需参数
        userId = request_res.get('userId', None)
        
        # 获取可选参数
        friendshipCreateTime = request_res.get('friendshipCreateTime', None)
        
        # 验证必需参数
        if not userId:
            message = {"code": 201, "succeed": False, "msg": "缺少必填信息: userId"}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        
        # 调用getFriends执行查询操作
        friends_list = getFriends.execute(userId=userId, friendshipCreateTime=friendshipCreateTime)
        
        message = {"response": friends_list, "code": 200, "succeed": True, "msg": "获取好友列表成功"}
        
    except Exception as e:
        _logger.error(f"获取好友列表接口异常: {str(e)}")
        message = {"response": [], "code": 500, "succeed": False, "msg": f"获取好友列表失败：{str(e)}"}
        
    return HttpResponse(json.dumps(message, ensure_ascii=False))


@csrf_exempt
def rate_competition(request):
    """用户评分接口"""
    message = {}
    try:
        request_res = json.loads(request.body)
        access_token = request_res.get('access_token', None)
        if not validate_accessToken(access_token):
            message = {"code": 100, "succeed": False, "msg": "Invalidate access token."}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        
        rater_uid = request_res.get('rater_uid', None)
        rated_uid = request_res.get('rated_uid', None)
        ratings = request_res.get('ratings', {})
        
        # 验证必填参数
        if not rater_uid or not rated_uid or not ratings:
            message = {"code": 201, "succeed": False, "msg": "缺少必填信息: rater_uid, rated_uid, ratings"}
            return HttpResponse(json.dumps(message, ensure_ascii=False))
        
        # 验证评分数据完整性
        required_fields = ['tech_one', 'tech_two', 'tech_three', 'tech_four', 'tech_five',
                          'person_one', 'person_two', 'person_three', 'person_four', 'person_five']
        
        for field in required_fields:
            if field not in ratings:
                message = {"code": 202, "succeed": False, "msg": f"评分数据缺少字段: {field}"}
                return HttpResponse(json.dumps(message, ensure_ascii=False))
            
            # 验证评分范围 (假设评分范围是0-10)
            try:
                score = float(ratings[field])
                if score < 0.0 or score > 5.0:
                    message = {"code": 203, "succeed": False, "msg": f"评分{field}超出范围(0-5): {score}"}
                    return HttpResponse(json.dumps(message, ensure_ascii=False))
            except (ValueError, TypeError):
                message = {"code": 204, "succeed": False, "msg": f"评分{field}格式错误: {ratings[field]}"}
                return HttpResponse(json.dumps(message, ensure_ascii=False))
        
        # 执行评分逻辑
        state, msg = RateCompetition().execute(rater_uid=rater_uid, rated_uid=rated_uid, ratings=ratings)
        
        if state == 1:
            message = {"code": 200, "succeed": True, "msg": msg}
        else:
            message = {"code": 300, "succeed": False, "msg": msg}
            
    except Exception as e:
        _logger.error(f"评分接口异常: {e}")
        message = {"code": 500, "succeed": False, "msg": f"服务器内部错误: {str(e)}"}
    
    return HttpResponse(json.dumps(message, ensure_ascii=False))
