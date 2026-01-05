# -*- coding: utf-8 -*-
"""
华为云OBS操作工具类
"""
import os
import uuid
from datetime import datetime
from obs import ObsClient
from django.conf import settings
from util.log import logHander

logger = logHander(__name__)


class OBSHelper:
    """华为云OBS操作辅助类"""
    
    def __init__(self):
        """初始化OBS客户端"""
        self.access_key_id = getattr(settings, 'OBS_ACCESS_KEY_ID', '')
        self.secret_access_key = getattr(settings, 'OBS_SECRET_ACCESS_KEY', '')
        self.server = getattr(settings, 'OBS_SERVER', 'https://obs.cn-north-4.myhuaweicloud.com')
        self.bucket_name = getattr(settings, 'OBS_BUCKET_NAME', 'clubengine-images')
        
        # 创建OBS客户端
        self.obs_client = ObsClient(
            access_key_id=self.access_key_id,
            secret_access_key=self.secret_access_key,
            server=self.server
        )
    
    def generate_object_key(self, filename, image_type='general'):
        """
        生成对象存储的key（路径）
        :param filename: 原始文件名
        :param image_type: 图片类型 (avatar, activity, merchant, general)
        :return: 对象key
        """
        # 获取文件扩展名
        ext = os.path.splitext(filename)[1].lower()
        if not ext:
            ext = '.jpg'
        
        # 生成唯一文件名
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        # 生成目录结构：类型/年/月/日/文件名
        now = datetime.now()
        object_key = f"{image_type}/{now.year}/{now.month:02d}/{now.day:02d}/{unique_filename}"
        
        return object_key
    
    def upload_file(self, file_path, object_key, content_type='image/jpeg'):
        """
        上传文件到OBS
        :param file_path: 本地文件路径
        :param object_key: OBS对象key
        :param content_type: 文件类型
        :return: 上传结果
        """
        try:
            resp = self.obs_client.putFile(
                bucketName=self.bucket_name,
                objectKey=object_key,
                file_path=file_path,
                metadata={'Content-Type': content_type}
            )
            
            if resp.status < 300:
                # 生成访问URL
                url = f"{self.server}/{self.bucket_name}/{object_key}"
                
                logger.info(f"文件上传成功: {object_key}")
                return {
                    'success': True,
                    'url': url,
                    'object_key': object_key,
                    'message': '上传成功'
                }
            else:
                logger.error(f"文件上传失败: {resp.errorCode} - {resp.errorMessage}")
                return {
                    'success': False,
                    'message': f'上传失败: {resp.errorMessage}'
                }
        except Exception as e:
            logger.error(f"上传文件异常: {str(e)}")
            return {
                'success': False,
                'message': f'上传异常: {str(e)}'
            }
    
    def upload_image(self, image_data, image_type='general', filename='image.jpg'):
        """
        上传图片数据到OBS
        :param image_data: 图片二进制数据或文件路径
        :param image_type: 图片类型
        :param filename: 文件名
        :return: 上传结果
        """
        try:
            # 生成对象key
            object_key = self.generate_object_key(filename, image_type)
            
            # 判断是文件路径还是二进制数据
            if isinstance(image_data, str) and os.path.exists(image_data):
                # 文件路径
                result = self.upload_file(image_data, object_key)
            else:
                # 二进制数据
                resp = self.obs_client.putContent(
                    bucketName=self.bucket_name,
                    objectKey=object_key,
                    content=image_data
                )
                
                if resp.status < 300:
                    url = f"{self.server}/{self.bucket_name}/{object_key}"
                    result = {
                        'success': True,
                        'url': url,
                        'object_key': object_key,
                        'cdn_url': self.get_cdn_url(object_key),
                        'message': '上传成功'
                    }
                else:
                    result = {
                        'success': False,
                        'message': f'上传失败: {resp.errorMessage}'
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"上传图片异常: {str(e)}")
            return {
                'success': False,
                'message': f'上传异常: {str(e)}'
            }
    
    def delete_file(self, object_key):
        """
        删除OBS上的文件
        :param object_key: 对象key
        :return: 删除结果
        """
        try:
            resp = self.obs_client.deleteObject(
                bucketName=self.bucket_name,
                objectKey=object_key
            )
            
            if resp.status < 300:
                logger.info(f"文件删除成功: {object_key}")
                return {'success': True, 'message': '删除成功'}
            else:
                logger.error(f"文件删除失败: {resp.errorMessage}")
                return {'success': False, 'message': resp.errorMessage}
                
        except Exception as e:
            logger.error(f"删除文件异常: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def get_signed_url(self, object_key, expires=3600):
        """
        生成临时访问URL（私有桶使用）
        :param object_key: 对象key
        :param expires: 过期时间（秒）
        :return: 临时URL
        """
        try:
            resp = self.obs_client.createSignedUrl(
                method='GET',
                bucketName=self.bucket_name,
                objectKey=object_key,
                expires=expires
            )
            
            if resp.status < 300:
                return {
                    'success': True,
                    'url': resp.signedUrl,
                    'expires': expires
                }
            else:
                return {
                    'success': False,
                    'message': resp.errorMessage
                }
                
        except Exception as e:
            logger.error(f"生成临时URL异常: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def get_cdn_url(self, object_key):
        """
        获取CDN加速URL
        :param object_key: 对象key
        :return: CDN URL
        """
        cdn_domain = getattr(settings, 'OBS_CDN_DOMAIN', '')
        if cdn_domain:
            return f"{cdn_domain}/{object_key}"
        else:
            return f"{self.server}/{self.bucket_name}/{object_key}"
    
    def list_objects(self, prefix='', max_keys=100):
        """
        列出存储桶中的对象
        :param prefix: 前缀过滤
        :param max_keys: 最大返回数量
        :return: 对象列表
        """
        try:
            resp = self.obs_client.listObjects(
                bucketName=self.bucket_name,
                prefix=prefix,
                max_keys=max_keys
            )
            
            if resp.status < 300:
                objects = []
                for content in resp.body.contents:
                    objects.append({
                        'key': content.key,
                        'size': content.size,
                        'last_modified': content.lastModified
                    })
                return {'success': True, 'objects': objects}
            else:
                return {'success': False, 'message': resp.errorMessage}
                
        except Exception as e:
            logger.error(f"列出对象异常: {str(e)}")
            return {'success': False, 'message': str(e)}
    
    def __del__(self):
        """关闭OBS客户端连接"""
        if hasattr(self, 'obs_client') and self.obs_client:
            self.obs_client.close()
