import os
import sys
import django
from django.core.mail import send_mail
from django.conf import settings

# 添加项目路径到 sys.path
project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_path)

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClubEngine.settings')
django.setup()

# 导入 UserInforTable 模型
from dbModel.models import UserInforTable

def send_user_stats_email():
    """
    统计 UserInforTable 用户数量并发送邮件
    """
    try:
        # 统计用户数量
        total_users = UserInforTable.objects.count()
        
        # 构建邮件内容
        subject = '网搭TennisBuddy 用户统计报告'
        message = f"""
        ClubEngine 用户统计报告
        
        总用户数: {total_users}
        
        报告生成时间: {django.utils.timezone.now()}
        """
        print(message)
        
        # 发送邮件
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['pengyazhang@yeah.net'],  # 替换为你的邮箱
            fail_silently=False,
        )
        
        print("用户统计邮件发送成功")
        
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")

if __name__ == '__main__':
    send_user_stats_email()