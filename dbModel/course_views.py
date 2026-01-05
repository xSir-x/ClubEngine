# -*- coding: utf-8 -*-
"""
课程相关视图
"""
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
from dbModel.models import CoachCourseTable, CourseEnrollmentTable
from util.log import logHander
from util.external_api import validate_accessToken
import time
import uuid
import json

logger = logHander(__name__)


@csrf_exempt
def publish_courses(request):
    """
    批量发布课程
    POST /api/courses/publish
    请求体:
    {
        "access_token": "token123",
        "coachId": "oABC123XYZ789",
        "coachName": "张教练",
        "courseInfo": {
            "title": "网球正手技术提升训练",
            "description": "...",
            "coverImage": "forehand.jpeg",
            "level": "intermediate",
            "category": "technique",
            "time": "10:00",
            "duration": 90,
            "location": "深圳湾体育中心1号场",
            "minStudents": 3,
            "maxStudents": 10,
            "originalPrice": 180.00,
            "currentPrice": 150.00
        },
        "dates": ["2026-01-10", "2026-01-11", "2026-01-12"]
    }
    
    返回:
    {
        "code": 200,
        "message": "课程发布成功",
        "data": {
            "success_count": 3,
            "courses": [...]
        }
    }
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        # 解析请求数据
        data = json.loads(request.body)
        
        # 验证access_token
        access_token = data.get('access_token', None)
        if not validate_accessToken(access_token):
            return JsonResponse({'code': 100, 'message': 'Invalidate access token.'})
        
        coach_id = data.get('coachId')
        coach_name = data.get('coachName')
        course_info = data.get('courseInfo', {})
        dates = data.get('dates', [])
        
        # 验证必填字段
        if not coach_id or not coach_name:
            return JsonResponse({'code': 400, 'message': '教练ID和姓名不能为空'})
        
        if not course_info:
            return JsonResponse({'code': 400, 'message': '课程信息不能为空'})
        
        if not dates or len(dates) == 0:
            return JsonResponse({'code': 400, 'message': '课程日期不能为空'})
        
        # 验证课程信息必填字段
        required_fields = ['title', 'description', 'coverImage', 'level', 'category', 
                          'time', 'duration', 'location', 'minStudents', 'maxStudents',
                          'originalPrice', 'currentPrice']
        
        for field in required_fields:
            if field not in course_info:
                return JsonResponse({'code': 400, 'message': f'课程信息缺少必填字段: {field}'})
        
        # 批量创建课程
        courses_created = []
        current_time = str(int(time.time()))
        
        with transaction.atomic():
            for course_date in dates:
                # 生成唯一课程ID
                course_id = f"COURSE-{coach_id}-{course_date}-{uuid.uuid4().hex[:8]}"
                
                # 创建课程记录
                course = CoachCourseTable.objects.create(
                    course_id=course_id,
                    coach_id=coach_id,
                    coach_name=coach_name,
                    title=course_info['title'],
                    description=course_info['description'],
                    cover_image=course_info['coverImage'],
                    level=course_info['level'],
                    category=course_info['category'],
                    course_date=course_date,
                    course_time=course_info['time'],
                    duration=course_info['duration'],
                    location=course_info['location'],
                    min_students=course_info['minStudents'],
                    max_students=course_info['maxStudents'],
                    current_students=0,
                    original_price=course_info['originalPrice'],
                    current_price=course_info['currentPrice'],
                    status=1,
                    is_deleted=False,
                    create_time=current_time
                )
                
                courses_created.append({
                    'course_id': course_id,
                    'title': course_info['title'],
                    'date': course_date,
                    'time': course_info['time'],
                    'location': course_info['location'],
                    'price': float(course_info['currentPrice'])
                })
                
                logger.info(f'课程创建成功: {course_id}, 教练: {coach_name}, 日期: {course_date}')
        
        return JsonResponse({
            'code': 200,
            'message': '课程发布成功',
            'data': {
                'success_count': len(courses_created),
                'courses': courses_created
            }
        })
    
    except json.JSONDecodeError:
        logger.error('JSON解析失败')
        return JsonResponse({'code': 400, 'message': 'JSON格式错误'})
    
    except Exception as e:
        logger.error(f'发布课程失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def get_courses(request):
    """
    获取课程列表
    GET /api/courses/list?coachId=xxx&date=2026-01-10&status=1
    """
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        # 验证access_token (从GET参数或Header中获取)
        access_token = request.GET.get('access_token', None)
        if not access_token:
            # 尝试从请求头获取
            access_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not validate_accessToken(access_token):
            return JsonResponse({'code': 100, 'message': 'Invalidate access token.'})
        
        coach_id = request.GET.get('coachId')
        course_date = request.GET.get('date')
        status = request.GET.get('status')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        
        # 构建查询条件
        filters = {'is_deleted': False}
        
        if coach_id:
            filters['coach_id'] = coach_id
        
        if course_date:
            filters['course_date'] = course_date
        
        if status:
            filters['status'] = int(status)
        
        # 查询课程
        courses = CoachCourseTable.objects.filter(**filters).order_by('-create_time')
        
        # 分页
        total = courses.count()
        start = (page - 1) * page_size
        end = start + page_size
        courses_page = courses[start:end]
        
        # 构建返回数据
        courses_list = []
        for course in courses_page:
            courses_list.append({
                'courseId': course.course_id,
                'coachId': course.coach_id,
                'coachName': course.coach_name,
                'title': course.title,
                'description': course.description,
                'coverImage': course.cover_image,
                'level': course.level,
                'category': course.category,
                'date': course.course_date,
                'time': course.course_time,
                'duration': course.duration,
                'location': course.location,
                'minStudents': course.min_students,
                'maxStudents': course.max_students,
                'currentStudents': course.current_students,
                'originalPrice': float(course.original_price),
                'currentPrice': float(course.current_price),
                'status': course.status,
                'createTime': course.create_time
            })
        
        return JsonResponse({
            'code': 200,
            'message': '查询成功',
            'data': {
                'total': total,
                'page': page,
                'pageSize': page_size,
                'courses': courses_list
            }
        })
    
    except Exception as e:
        logger.error(f'查询课程失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def get_course_detail(request):
    """
    获取课程详情
    GET /api/courses/detail?courseId=xxx
    """
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        # 验证access_token
        access_token = request.GET.get('access_token', None)
        if not access_token:
            access_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not validate_accessToken(access_token):
            return JsonResponse({'code': 100, 'message': 'Invalidate access token.'})
        
        course_id = request.GET.get('courseId')
        
        if not course_id:
            return JsonResponse({'code': 400, 'message': '课程ID不能为空'})
        
        # 查询课程
        try:
            course = CoachCourseTable.objects.get(course_id=course_id, is_deleted=False)
        except CoachCourseTable.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '课程不存在'})
        
        # 查询报名学员数量
        enrollment_count = CourseEnrollmentTable.objects.filter(
            course_id=course_id,
            enrollment_status=1
        ).count()
        
        course_detail = {
            'courseId': course.course_id,
            'coachId': course.coach_id,
            'coachName': course.coach_name,
            'title': course.title,
            'description': course.description,
            'coverImage': course.cover_image,
            'level': course.level,
            'category': course.category,
            'date': course.course_date,
            'time': course.course_time,
            'duration': course.duration,
            'location': course.location,
            'minStudents': course.min_students,
            'maxStudents': course.max_students,
            'currentStudents': enrollment_count,
            'originalPrice': float(course.original_price),
            'currentPrice': float(course.current_price),
            'status': course.status,
            'createTime': course.create_time,
            'updateTime': course.update_time
        }
        
        return JsonResponse({
            'code': 200,
            'message': '查询成功',
            'data': course_detail
        })
    
    except Exception as e:
        logger.error(f'查询课程详情失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def update_course(request):
    """
    更新课程信息
    POST /api/courses/update
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        data = json.loads(request.body)
        
        # 验证access_token
        access_token = data.get('access_token', None)
        if not validate_accessToken(access_token):
            return JsonResponse({'code': 100, 'message': 'Invalidate access token.'})
        
        course_id = data.get('courseId')
        
        if not course_id:
            return JsonResponse({'code': 400, 'message': '课程ID不能为空'})
        
        # 查询课程
        try:
            course = CoachCourseTable.objects.get(course_id=course_id, is_deleted=False)
        except CoachCourseTable.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '课程不存在'})
        
        # 更新允许修改的字段
        update_fields = ['title', 'description', 'coverImage', 'level', 'category',
                        'time', 'duration', 'location', 'minStudents', 'maxStudents',
                        'originalPrice', 'currentPrice', 'status']
        
        field_mapping = {
            'title': 'title',
            'description': 'description',
            'coverImage': 'cover_image',
            'level': 'level',
            'category': 'category',
            'time': 'course_time',
            'duration': 'duration',
            'location': 'location',
            'minStudents': 'min_students',
            'maxStudents': 'max_students',
            'originalPrice': 'original_price',
            'currentPrice': 'current_price',
            'status': 'status'
        }
        
        updated = False
        for field_name, db_field in field_mapping.items():
            if field_name in data:
                setattr(course, db_field, data[field_name])
                updated = True
        
        if updated:
            course.update_time = str(int(time.time()))
            course.save()
            logger.info(f'课程更新成功: {course_id}')
        
        return JsonResponse({
            'code': 200,
            'message': '课程更新成功'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': 'JSON格式错误'})
    
    except Exception as e:
        logger.error(f'更新课程失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def delete_course(request):
    """
    删除课程（软删除）
    POST /api/courses/delete
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        data = json.loads(request.body)
        
        # 验证access_token
        access_token = data.get('access_token', None)
        if not validate_accessToken(access_token):
            return JsonResponse({'code': 100, 'message': 'Invalidate access token.'})
        
        course_id = data.get('courseId')
        
        if not course_id:
            return JsonResponse({'code': 400, 'message': '课程ID不能为空'})
        
        # 查询课程
        try:
            course = CoachCourseTable.objects.get(course_id=course_id, is_deleted=False)
        except CoachCourseTable.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '课程不存在'})
        
        # 检查是否有学员报名
        enrollment_count = CourseEnrollmentTable.objects.filter(
            course_id=course_id,
            enrollment_status=1
        ).count()
        
        if enrollment_count > 0:
            return JsonResponse({
                'code': 400,
                'message': f'课程已有{enrollment_count}名学员报名，无法删除'
            })
        
        # 软删除
        course.is_deleted = True
        course.status = 4  # 已取消
        course.update_time = str(int(time.time()))
        course.save()
        
        logger.info(f'课程删除成功: {course_id}')
        
        return JsonResponse({
            'code': 200,
            'message': '课程删除成功'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': 'JSON格式错误'})
    
    except Exception as e:
        logger.error(f'删除课程失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def enroll_course(request):
    """
    学员报名课程
    POST /api/courses/enroll
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        data = json.loads(request.body)
        
        # 验证access_token
        access_token = data.get('access_token', None)
        if not validate_accessToken(access_token):
            return JsonResponse({'code': 100, 'message': 'Invalidate access token.'})
        
        course_id = data.get('courseId')
        user_id = data.get('userId')
        user_name = data.get('userName')
        
        if not all([course_id, user_id, user_name]):
            return JsonResponse({'code': 400, 'message': '参数不完整'})
        
        # 查询课程
        try:
            course = CoachCourseTable.objects.get(course_id=course_id, is_deleted=False)
        except CoachCourseTable.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '课程不存在'})
        
        # 检查课程状态
        if course.status != 1:
            return JsonResponse({'code': 400, 'message': '课程不可报名'})
        
        # 检查是否已报名
        existing = CourseEnrollmentTable.objects.filter(
            course_id=course_id,
            user_id=user_id,
            enrollment_status=1
        ).exists()
        
        if existing:
            return JsonResponse({'code': 400, 'message': '您已报名此课程'})
        
        # 检查人数限制
        current_enrollments = CourseEnrollmentTable.objects.filter(
            course_id=course_id,
            enrollment_status=1
        ).count()
        
        if current_enrollments >= course.max_students:
            return JsonResponse({'code': 400, 'message': '课程报名人数已满'})
        
        # 创建报名记录
        enrollment_id = f"ENROLL-{course_id}-{user_id}-{uuid.uuid4().hex[:8]}"
        current_time = str(int(time.time()))
        
        CourseEnrollmentTable.objects.create(
            enrollment_id=enrollment_id,
            course_id=course_id,
            user_id=user_id,
            user_name=user_name,
            paid_amount=course.current_price,
            payment_status=1,
            enrollment_status=1,
            enroll_time=current_time
        )
        
        # 更新课程当前学员数
        course.current_students = current_enrollments + 1
        course.save()
        
        logger.info(f'学员报名成功: {enrollment_id}, 用户: {user_name}, 课程: {course.title}')
        
        return JsonResponse({
            'code': 200,
            'message': '报名成功',
            'data': {
                'enrollmentId': enrollment_id,
                'courseId': course_id,
                'amount': float(course.current_price)
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': 'JSON格式错误'})
    
    except Exception as e:
        logger.error(f'报名课程失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})
