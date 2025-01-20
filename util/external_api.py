from django.core.cache import cache
import requests
import uuid
from wxpay.settings import APPID, APP_SECRET
from django_redis import get_redis_connection

def get_openid(js_code):
    """
    获取open_id
    :param js_code:
    :return:
    """
    appid = APPID
    secret = 'b583d5d85d03874c0db4922f49b06827' #"小程序secret"
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
            return True
        # cache.get(access_token)
    except Exception as e:
        return False
    return True


def store_in_redis(key, value, ex=30):
    """使用Redis进行数据存储"""
    redis_conn = get_redis_connection()
    redis_conn.set(key, value, ex)


def retrieve_from_redis(key):
    """要从Redis中检索数据"""
    redis_conn = get_redis_connection()
    return redis_conn.get(key)