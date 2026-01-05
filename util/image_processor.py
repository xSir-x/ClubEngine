# -*- coding: utf-8 -*-
"""
图片处理工具类
"""
import os
import io
from PIL import Image
from util.log import logHander

logger = logHander(__name__)


class ImageProcessor:
    """图片处理工具类"""
    
    def __init__(self):
        self.max_size = 5 * 1024 * 1024  # 5MB
        self.quality = 85
        self.allowed_formats = ['JPEG', 'PNG', 'GIF', 'WEBP']
    
    def validate_image(self, image_file):
        """
        验证图片文件
        :param image_file: Django上传的文件对象
        :return: (是否有效, 错误信息)
        """
        try:
            # 验证文件大小
            if image_file.size > self.max_size:
                return False, f"图片大小超过限制({self.max_size / 1024 / 1024}MB)"
            
            # 验证文件类型
            img = Image.open(image_file)
            if img.format not in self.allowed_formats:
                return False, f"不支持的图片格式: {img.format}"
            
            # 验证图片内容
            img.verify()
            
            return True, "验证通过"
            
        except Exception as e:
            logger.error(f"图片验证失败: {str(e)}")
            return False, f"无效的图片文件: {str(e)}"
    
    def compress_image(self, image, quality=None):
        """
        压缩图片
        :param image: PIL Image对象
        :param quality: 图片质量(1-100)
        :return: 压缩后的图片数据
        """
        if quality is None:
            quality = self.quality
        
        output = io.BytesIO()
        
        # 转换为RGB模式（如果是RGBA）
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # 保存为JPEG格式并压缩
        image.save(output, format='JPEG', quality=quality, optimize=True)
        
        return output.getvalue()
    
    def resize_image(self, image, max_width=1920, max_height=1080):
        """
        调整图片尺寸
        :param image: PIL Image对象
        :param max_width: 最大宽度
        :param max_height: 最大高度
        :return: 调整后的图片
        """
        width, height = image.size
        
        # 如果图片尺寸在限制内，不做处理
        if width <= max_width and height <= max_height:
            return image
        
        # 计算缩放比例
        ratio = min(max_width / width, max_height / height)
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        # 使用高质量的重采样算法
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def create_thumbnail(self, image, size=(200, 200)):
        """
        创建缩略图
        :param image: PIL Image对象
        :param size: 缩略图尺寸
        :return: 缩略图数据
        """
        image.thumbnail(size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        
        return output.getvalue()
    
    def process(self, image_file, image_type='general'):
        """
        处理图片（综合处理）
        :param image_file: Django上传的文件对象
        :param image_type: 图片类型
        :return: 处理后的图片数据
        """
        try:
            # 打开图片
            image_file.seek(0)  # 重置文件指针
            image = Image.open(image_file)
            
            # 根据类型设置不同的处理参数
            if image_type == 'avatar':
                # 头像：正方形，较小尺寸
                image = self.make_square(image)
                image = self.resize_image(image, 500, 500)
            elif image_type == 'activity':
                # 活动图片：保持原比例，限制大小
                image = self.resize_image(image, 1920, 1080)
            elif image_type == 'merchant':
                # 商户图片：保持原比例
                image = self.resize_image(image, 1200, 800)
            else:
                # 通用图片
                image = self.resize_image(image)
            
            # 压缩图片
            compressed_data = self.compress_image(image)
            
            logger.info(f"图片处理完成，类型: {image_type}, 大小: {len(compressed_data)} bytes")
            
            return compressed_data
            
        except Exception as e:
            logger.error(f"图片处理失败: {str(e)}")
            raise
    
    def make_square(self, image):
        """
        将图片裁剪为正方形
        :param image: PIL Image对象
        :return: 正方形图片
        """
        width, height = image.size
        
        if width == height:
            return image
        
        # 以较小的边为基准
        min_side = min(width, height)
        
        # 计算裁剪区域
        left = (width - min_side) // 2
        top = (height - min_side) // 2
        right = left + min_side
        bottom = top + min_side
        
        return image.crop((left, top, right, bottom))
    
    def add_watermark(self, image, watermark_text, position='bottom-right'):
        """
        添加水印
        :param image: PIL Image对象
        :param watermark_text: 水印文字
        :param position: 水印位置
        :return: 添加水印后的图片
        """
        from PIL import ImageDraw, ImageFont
        
        draw = ImageDraw.Draw(image)
        
        # 使用默认字体
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        # 计算水印位置
        width, height = image.size
        text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        if position == 'bottom-right':
            x = width - text_width - 10
            y = height - text_height - 10
        elif position == 'bottom-left':
            x = 10
            y = height - text_height - 10
        elif position == 'top-right':
            x = width - text_width - 10
            y = 10
        else:  # top-left
            x = 10
            y = 10
        
        # 绘制水印
        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 128))
        
        return image
