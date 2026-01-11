from django.core.cache import cache
import requests
import uuid
from wxpay.settings import APPID, APP_SECRET
from django_redis import get_redis_connection
import json
from django.utils.timezone import is_aware, make_aware
from django.utils import timezone
from datetime import datetime

redis_conn = get_redis_connection()


def get_openid(js_code):
    """
    获取open_id
    :param js_code:
    :return:
    """
    appid = APPID
    secret = 'b583d5d85d03874c0db4922f49b06827'  # "小程序secret"
    grant_type = "authorization_code"  # 这个固定
    url = "https://api.weixin.qq.com/sns/jscode2session?appid=" + appid + "&secret=" + secret + "&js_code=" + js_code + "&grant_type=" + grant_type
    user_info = requests.get(url).json()
    open_id = user_info['openid']  # 用户openid
    session_key = user_info['session_key']  # 用户的session_key
    return open_id


def validate_accessToken(access_token):
    # 获取缓存
    try:
        res = retrieve_from_redis(access_token)
        if not res:
            print(">> Retrieve access token Failed....")
            return False
    except Exception as e:
        print(">> Retrieve access token Exception: %s...." % e)
        return False
    return True


def get_uid_from_token(access_token):
    """
    从 access_token 中提取用户 openid (uid)
    access_token 格式: openid[0] + timestamp + openid[1:]
    通过去除中间的时间戳来还原 openid
    """
    if not access_token or len(access_token) < 14:
        return None
    
    try:
        # access_token 由 openid[0] + 13位时间戳 + openid[1:] 组成
        # 提取第一个字符
        first_char = access_token[0]
        # 跳过13位时间戳，提取剩余部分
        remaining = access_token[14:]
        # 还原 openid
        openid = first_char + remaining
        return openid
    except Exception as e:
        print(f">> Extract uid from token failed: {e}")
        return None


def store_in_redis(key, value, ex=60 * 60):
    """使用Redis进行数据存储"""
    # redis_conn = get_redis_connection()
    redis_conn.set(key, value, ex)


def retrieve_from_redis(key):
    """要从Redis中检索数据"""
    # redis_conn = get_redis_connection()
    return redis_conn.get(key)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            if timezone.is_naive(obj):
                obj = timezone.make_aware(obj, timezone.utc)
            return obj.strftime('%Y-%m-%dT%H:%M:%S%z')  # ISO 8601 format
        return super().default(obj)


import time
from datetime import datetime

