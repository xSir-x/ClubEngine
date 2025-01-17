from django.core.cache import cache


def get_openid(js_code):
    open_id="123456"
    return open_id


def validate_accessToken(access_token):
    # 获取缓存
    try:
        cache.get(access_token)
    except Exception as e:
        print(e)
        return True
    return True