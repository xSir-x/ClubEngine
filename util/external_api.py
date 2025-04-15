from django.core.cache import cache
import requests
from django.http import JsonResponse

def get_openid(js_code):
    url = "https://api.weixin.qq.com/sns/jscode2session"
    headers = {
        "Authorization": "Bearer YOUR_ACCESS_TOKEN",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果响应状态码不是200，则引发HTTPError
        data = response.json()  # 假设响应是JSON格式
        return JsonResponse(data, safe=False)
    except requests.exceptions.HTTPError as http_err:
        return JsonResponse({"error": str(http_err)}, status=response.status_code)
    except Exception as err:
        return JsonResponse({"error": str(err)}, status=500)



def validate_accessToken(access_token):
    # 获取缓存
    try:
        cache.get(access_token)
    except Exception as e:
        print(e)
        return False
    return True



