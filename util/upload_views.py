# -*- coding: utf-8 -*-
"""
图片上传API视图
"""
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.views import View
from util.obs_helper import OBSHelper
from util.image_processor import ImageProcessor
from util.log import logHander
from dbModel.models import UserInforTable

logger = logHander(__name__)


@csrf_exempt
def upload_image(request):
    """
    图片上传接口
    POST /api/upload/image
    参数:
        - image: 图片文件
        - type: 图片类型 (avatar, activity, merchant, general)
    返回:
        {
            "code": 200,
            "message": "上传成功",
            "data": {
                "url": "https://...",
                "cdn_url": "https://...",
                "thumbnail_url": "https://..."
            }
        }
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    # 获取参数
    image_file = request.FILES.get('image')
    image_type = request.POST.get('type', 'general')
    
    if not image_file:
        return JsonResponse({'code': 400, 'message': '未找到图片文件'})
    
    # 验证图片类型
    allowed_types = ['avatar', 'activity', 'merchant', 'general']
    if image_type not in allowed_types:
        return JsonResponse({'code': 400, 'message': f'不支持的图片类型: {image_type}'})
    
    try:
        # 1. 验证图片
        processor = ImageProcessor()
        is_valid, error_msg = processor.validate_image(image_file)
        
        if not is_valid:
            return JsonResponse({'code': 400, 'message': error_msg})
        
        # 2. 处理图片
        image_file.seek(0)  # 重置文件指针
        processed_data = processor.process(image_file, image_type)
        
        # 3. 上传到OBS
        obs_helper = OBSHelper()
        result = obs_helper.upload_image(
            processed_data, 
            image_type, 
            image_file.name
        )
        
        if result['success']:
            # 4. 返回结果
            return JsonResponse({
                'code': 200,
                'message': '上传成功',
                'data': {
                    'url': result['url'],
                    'cdn_url': result.get('cdn_url', result['url']),
                    'object_key': result['object_key']
                }
            })
        else:
            return JsonResponse({
                'code': 500, 
                'message': result.get('message', '上传失败')
            })
    
    except Exception as e:
        logger.error(f'上传图片异常: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def upload_avatar(request):
    """
    用户头像上传接口
    POST /api/upload/avatar
    参数:
        - image: 图片文件
        - uid: 用户ID
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    image_file = request.FILES.get('image')
    uid = request.POST.get('uid')
    
    if not image_file:
        return JsonResponse({'code': 400, 'message': '未找到图片文件'})
    
    if not uid:
        return JsonResponse({'code': 400, 'message': '缺少用户ID'})
    
    try:
        # 1. 验证用户是否存在
        user = UserInforTable.objects.filter(uid=uid).first()
        if not user:
            return JsonResponse({'code': 404, 'message': '用户不存在'})
        
        # 2. 处理和上传图片
        processor = ImageProcessor()
        is_valid, error_msg = processor.validate_image(image_file)
        
        if not is_valid:
            return JsonResponse({'code': 400, 'message': error_msg})
        
        image_file.seek(0)
        processed_data = processor.process(image_file, 'avatar')
        
        obs_helper = OBSHelper()
        result = obs_helper.upload_image(processed_data, 'avatar', image_file.name)
        
        if result['success']:
            # 3. 更新用户头像URL
            UserInforTable.objects.filter(uid=uid).update(
                pic=result.get('cdn_url', result['url'])
            )
            
            logger.info(f'用户 {uid} 更新头像成功')
            
            return JsonResponse({
                'code': 200,
                'message': '头像上传成功',
                'data': {
                    'url': result['url'],
                    'cdn_url': result.get('cdn_url', result['url'])
                }
            })
        else:
            return JsonResponse({'code': 500, 'message': result.get('message', '上传失败')})
    
    except Exception as e:
        logger.error(f'上传头像异常: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def delete_image(request):
    """
    删除图片接口
    POST /api/delete/image
    参数:
        - object_key: OBS对象key
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    import json
    data = json.loads(request.body)
    object_key = data.get('object_key')
    
    if not object_key:
        return JsonResponse({'code': 400, 'message': '缺少object_key参数'})
    
    try:
        obs_helper = OBSHelper()
        result = obs_helper.delete_file(object_key)
        
        if result['success']:
            return JsonResponse({
                'code': 200,
                'message': '删除成功'
            })
        else:
            return JsonResponse({
                'code': 500,
                'message': result.get('message', '删除失败')
            })
    
    except Exception as e:
        logger.error(f'删除图片异常: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


class ImageUploadView(View):
    """图片上传类视图"""
    
    def post(self, request):
        """处理POST请求"""
        return upload_image(request)
