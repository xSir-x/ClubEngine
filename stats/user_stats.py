import os
import sys
import django
import requests
from django.conf import settings

# 添加项目路径到 sys.path
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClubEngine.settings')
django.setup()

# 导入 UserInforTable 模型
from dbModel.models import UserInforTable

def send_user_stats_notification():
    """
    统计 UserInforTable 用户数量并推送微信通知
    """
    try:
        # 统计用户数量
        total_users = UserInforTable.objects.count()
        
        # 构建消息内容
        message = f"""
        网搭TennisBudy 用户统计报告
        
        总用户数: {total_users}
        
        报告生成时间: {django.utils.timezone.now()}
        """
        print(message)
        
        # 微信机器人 Webhook URL
        webhook_url = 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=693axxx6-7aoc-4bc4-97a0-0ec2sifa5aaa'
        
        # 构建推送数据
        data = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
        
        # 发送推送
        response = requests.post(webhook_url, json=data)
        response.raise_for_status()  # 如果状态码不是 200，会抛出异常
        
        print("用户统计微信通知发送成功")
        
    except Exception as e:
        print(f"发送微信通知失败: {str(e)}")

if __name__ == '__main__':
    send_user_stats_notification()