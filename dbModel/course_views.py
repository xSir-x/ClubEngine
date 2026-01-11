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
        
        # 查询报名学员列表（已支付且已报名/已完成的）
        enrollments = CourseEnrollmentTable.objects.filter(
            course_id=course_id,
            enrollment_status__in=[1, 3],  # 1-已报名, 3-已完成
            payment_status=2  # 已支付
        ).values('user_id', 'user_name', 'enrollment_id', 'enroll_time', 'enrollment_status')
        
        # 构建学员列表
        enrolled_students = []
        for enrollment in enrollments:
            enrolled_students.append({
                'userId': enrollment['user_id'],
                'userName': enrollment['user_name'],
                'enrollmentId': enrollment['enrollment_id'],
                'enrollTime': enrollment['enroll_time']
            })
        
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
            'currentStudents': len(enrolled_students),
            'originalPrice': float(course.original_price),
            'currentPrice': float(course.current_price),
            'status': course.status,
            'createTime': course.create_time,
            'updateTime': course.update_time,
            'enrolledStudents': enrolled_students  # 新增：已报名学员列表
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
            enrollment_status__in=[1]  # 已报名
        ).first()
        
        if existing:
            # 如果已存在未支付的报名，返回报名信息
            if existing.payment_status == 1:
                return JsonResponse({
                    'code': 200,
                    'message': '您已有待支付的报名记录',
                    'data': {
                        'enrollmentId': existing.enrollment_id,
                        'courseId': course_id,
                        'amount': float(course.current_price),
                        'paymentStatus': 1  # 待支付
                    }
                })
            else:
                return JsonResponse({'code': 400, 'message': '您已报名此课程'})
        
        # 检查人数限制
        current_enrollments = CourseEnrollmentTable.objects.filter(
            course_id=course_id,
            enrollment_status=1,  # 只统计已支付的
            payment_status=2  # 已支付
        ).count()
        
        if current_enrollments >= course.max_students:
            return JsonResponse({'code': 400, 'message': '课程报名人数已满'})
        
        # 创建报名记录（待支付状态）
        enrollment_id = f"ENROLL-{course_id}-{user_id}-{uuid.uuid4().hex[:8]}"
        current_time = str(int(time.time()))
        
        CourseEnrollmentTable.objects.create(
            enrollment_id=enrollment_id,
            course_id=course_id,
            user_id=user_id,
            user_name=user_name,
            paid_amount=course.current_price,
            payment_status=1,  # 1-待支付
            enrollment_status=4,  # 4-待确认（支付后变为1-已报名）
            enroll_time=current_time
        )
        
        logger.info(f'学员创建报名记录: {enrollment_id}, 用户: {user_name}, 课程: {course.title}, 待支付')
        
        return JsonResponse({
            'code': 200,
            'message': '报名记录创建成功，请继续支付',
            'data': {
                'enrollmentId': enrollment_id,
                'courseId': course_id,
                'courseTitle': course.title,
                'courseDate': course.course_date,
                'courseTime': course.course_time,
                'location': course.location,
                'amount': float(course.current_price),
                'paymentStatus': 1  # 待支付
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': 'JSON格式错误'})
    
    except Exception as e:
        logger.error(f'报名课程失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def course_payment_callback(request):
    """
    课程支付回调处理
    在微信支付成功后更新课程报名状态
    POST /api/courses/payment/callback
    
    注意：此接口只负责更新课程报名状态，不创建订单
    订单已经由 genOrder 接口创建，由微信回调 notifyOrder 接口更新支付状态
    
    请求参数:
    {
        "access_token": "xxx",
        "order_id": "订单ID",
        "course_id": "课程ID",
        "user_id": "用户ID"
    }
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        data = json.loads(request.body)
        
        # 验证access_token
        access_token = data.get('access_token', None)
        if not validate_accessToken(access_token):
            return JsonResponse({'code': 100, 'message': 'Invalidate access token.'})
        
        order_id = data.get('order_id')
        course_id = data.get('course_id')
        user_id = data.get('user_id')
        
        if not all([order_id, course_id, user_id]):
            return JsonResponse({'code': 400, 'message': '参数不完整'})
        
        # 使用事务确保数据一致性
        with transaction.atomic():
            # 1. 验证订单是否存在且已支付
            from dbModel.models import UserOrderTable
            
            try:
                order = UserOrderTable.objects.get(order_id=order_id)
            except UserOrderTable.DoesNotExist:
                return JsonResponse({'code': 404, 'message': '订单不存在'})
            
            # 验证订单状态
            if order.order_status != 2:  # 2-支付成功
                return JsonResponse({
                    'code': 400, 
                    'message': f'订单未支付或支付失败，当前状态: {order.order_status}'
                })
            
            # 验证订单是否属于该用户和课程
            if order.uid != user_id or order.act_id != course_id:
                return JsonResponse({'code': 403, 'message': '订单信息不匹配'})
            
            # 2. 更新报名记录
            enrollment = CourseEnrollmentTable.objects.filter(
                course_id=course_id,
                user_id=user_id,
                payment_status=1  # 待支付
            ).first()
            
            if not enrollment:
                return JsonResponse({'code': 404, 'message': '未找到待支付的报名记录'})
            
            # 更新支付状态
            enrollment.payment_status = 2  # 已支付
            enrollment.enrollment_status = 1  # 已报名
            enrollment.order_id = order_id
            enrollment.save()
            
            # 3. 更新课程报名人数
            course = CoachCourseTable.objects.get(course_id=course_id, is_deleted=False)
            paid_enrollments = CourseEnrollmentTable.objects.filter(
                course_id=course_id,
                payment_status=2,
                enrollment_status=1
            ).count()
            course.current_students = paid_enrollments
            course.save()
            
            logger.info(f'课程支付确认成功: 订单={order_id}, 课程={course_id}, 用户={user_id}, 微信支付ID={order.paymentid}')
        
        return JsonResponse({
            'code': 200,
            'message': '支付成功，报名确认完成',
            'data': {
                'enrollmentId': enrollment.enrollment_id,
                'courseId': course_id,
                'orderId': order_id,
                'paymentId': order.paymentid,
                'currentStudents': paid_enrollments
            }
        })
    
    except CoachCourseTable.DoesNotExist:
        return JsonResponse({'code': 404, 'message': '课程不存在'})
    
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': 'JSON格式错误'})
    
    except Exception as e:
        logger.error(f'课程支付回调处理失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def get_user_courses(request):
    """
    用户查询自己的课程
    GET /api/courses/my?userId=xxx&status=1&page=1&pageSize=20
    
    参数:
    - userId: 用户ID (必填)
    - status: 报名状态筛选 (可选) 1-已报名 2-已取消 3-已完成
    - paymentStatus: 支付状态筛选 (可选) 1-未支付 2-已支付 3-已退款
    - page: 页码 (可选，默认1)
    - pageSize: 每页数量 (可选，默认20)
    
    返回:
    {
        "code": 200,
        "message": "查询成功",
        "data": {
            "total": 10,
            "page": 1,
            "pageSize": 20,
            "enrollments": [
                {
                    "enrollmentId": "报名ID",
                    "courseId": "课程ID",
                    "courseTitle": "课程标题",
                    "coachName": "教练姓名",
                    "coverImage": "封面图片",
                    "courseDate": "2026-01-10",
                    "courseTime": "10:00",
                    "duration": 90,
                    "location": "上课地点",
                    "paidAmount": 150.00,
                    "paymentStatus": 2,
                    "enrollmentStatus": 1,
                    "enrollTime": "报名时间",
                    "orderId": "订单ID"
                }
            ]
        }
    }
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
        
        # 获取参数
        user_id = request.GET.get('userId')
        enrollment_status = request.GET.get('status')
        payment_status = request.GET.get('paymentStatus')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        
        if not user_id:
            return JsonResponse({'code': 400, 'message': '用户ID不能为空'})
        
        # 构建查询条件
        filters = {'user_id': user_id}
        
        if enrollment_status:
            filters['enrollment_status'] = int(enrollment_status)
        
        if payment_status:
            filters['payment_status'] = int(payment_status)
        
        # 查询报名记录
        enrollments = CourseEnrollmentTable.objects.filter(**filters).order_by('-enroll_time')
        
        # 分页
        total = enrollments.count()
        start = (page - 1) * page_size
        end = start + page_size
        enrollments_page = enrollments[start:end]
        
        # 构建返回数据
        enrollments_list = []
        for enrollment in enrollments_page:
            # 获取课程详情
            try:
                course = CoachCourseTable.objects.get(
                    course_id=enrollment.course_id,
                    is_deleted=False
                )
                
                enrollments_list.append({
                    'enrollmentId': enrollment.enrollment_id,
                    'courseId': enrollment.course_id,
                    'courseTitle': course.title,
                    'coachId': course.coach_id,
                    'coachName': course.coach_name,
                    'coverImage': course.cover_image,
                    'level': course.level,
                    'category': course.category,
                    'courseDate': course.course_date,
                    'courseTime': course.course_time,
                    'duration': course.duration,
                    'location': course.location,
                    'paidAmount': float(enrollment.paid_amount),
                    'paymentStatus': enrollment.payment_status,
                    'paymentStatusText': {1: '未支付', 2: '已支付', 3: '已退款'}.get(enrollment.payment_status, '未知'),
                    'enrollmentStatus': enrollment.enrollment_status,
                    'enrollmentStatusText': {1: '已报名', 2: '已取消', 3: '已完成'}.get(enrollment.enrollment_status, '未知'),
                    'enrollTime': enrollment.enroll_time,
                    'cancelTime': enrollment.cancel_time,
                    'orderId': enrollment.order_id,
                    'courseStatus': course.status,
                    'courseStatusText': {1: '待开课', 2: '进行中', 3: '已结束', 4: '已取消'}.get(course.status, '未知')
                })
            except CoachCourseTable.DoesNotExist:
                logger.warning(f'课程不存在或已删除: {enrollment.course_id}')
                # 课程已被删除，仍然返回基本报名信息
                enrollments_list.append({
                    'enrollmentId': enrollment.enrollment_id,
                    'courseId': enrollment.course_id,
                    'courseTitle': '课程已删除',
                    'coachId': '',
                    'coachName': '',
                    'coverImage': '',
                    'level': '',
                    'category': '',
                    'courseDate': '',
                    'courseTime': '',
                    'duration': 0,
                    'location': '',
                    'paidAmount': float(enrollment.paid_amount),
                    'paymentStatus': enrollment.payment_status,
                    'paymentStatusText': {1: '未支付', 2: '已支付', 3: '已退款'}.get(enrollment.payment_status, '未知'),
                    'enrollmentStatus': enrollment.enrollment_status,
                    'enrollmentStatusText': {1: '已报名', 2: '已取消', 3: '已完成'}.get(enrollment.enrollment_status, '未知'),
                    'enrollTime': enrollment.enroll_time,
                    'cancelTime': enrollment.cancel_time,
                    'orderId': enrollment.order_id,
                    'courseStatus': 4,
                    'courseStatusText': '已取消'
                })
        
        return JsonResponse({
            'code': 200,
            'message': '查询成功',
            'data': {
                'total': total,
                'page': page,
                'pageSize': page_size,
                'enrollments': enrollments_list
            }
        })
    
    except Exception as e:
        logger.error(f'查询用户课程失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def cancel_course_enrollment(request):
    """
    取消课程报名并退款
    POST /api/courses/cancel
    请求参数:
    {
        "access_token": "xxx",
        "enrollment_id": "报名ID",
        "cancel_reason": "取消原因"
    }
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        data = json.loads(request.body)
        
        # 验证token
        access_token = data.get('access_token', None)
        if not validate_accessToken(access_token):
            return JsonResponse({'code': 100, 'message': 'Invalidate access token.'})
        
        enrollment_id = data.get('enrollment_id')
        cancel_reason = data.get('cancel_reason', '用户取消报名')
        
        if not enrollment_id:
            return JsonResponse({'code': 400, 'message': '报名ID不能为空'})
        
        # 查询报名记录
        try:
            enrollment = CourseEnrollmentTable.objects.get(enrollment_id=enrollment_id)
        except CourseEnrollmentTable.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '报名记录不存在'})
        
        # 检查支付状态
        if enrollment.payment_status != 2:
            return JsonResponse({'code': 400, 'message': '未支付或已退款，无法取消'})
        
        if not enrollment.order_id:
            return JsonResponse({'code': 400, 'message': '缺少订单信息'})
        
        # 检查课程状态和时间（可选：添加退款规则）
        course = CoachCourseTable.objects.filter(course_id=enrollment.course_id).first()
        if course:
            # 可以添加退款规则，比如开课前24小时才能退款
            from datetime import datetime, timedelta
            course_datetime = datetime.strptime(f"{course.course_date} {course.course_time}", "%Y-%m-%d %H:%M")
            if course_datetime - datetime.now() < timedelta(hours=8):
                return JsonResponse({'code': 400, 'message': '开课前8小时内不可退款'})
            
        
        # 调用退款接口
        from wxpay.views import WXMinPay
        from django.http import HttpRequest
        
        # refund_request = HttpRequest()
        # refund_request.body = json.dumps({
        #     'order_id': enrollment.order_id,
        #     'refund_reason': cancel_reason
        # }).encode('utf-8')

        class MockRequest:
            def __init__(self, body_data):
                self.body = json.dumps(body_data).encode('utf-8')

        mock_request = MockRequest({
            'order_id': enrollment.order_id,
            'refund_reason': cancel_reason
        })

        refund_result = WXMinPay.refund(mock_request)
        
        # refund_result = WXMinPay.refund(refund_request)
        
        if refund_result.get('succeed'):
            logger.info(f'课程退款成功: enrollment_id={enrollment_id}')
            return JsonResponse(refund_result)
        else:
            logger.error(f'课程退款失败: {refund_result.get("msg")}')
            return JsonResponse(refund_result)
            
    except Exception as e:
        logger.error(f'取消课程报名失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def batch_verify_enrollments(request):
    """
    教练批量核销课程学员
    POST /api/courses/batch_verify
    
    请求参数:
    {
        "access_token": "xxx",
        "coach_id": "教练ID",
        "course_id": "课程ID",
        "enrollment_ids": ["报名ID1", "报名ID2", "报名ID3"]
    }
    
    返回:
    {
        "code": 200,
        "message": "核销成功",
        "data": {
            "success_count": 3,
            "failed_count": 0,
            "success_list": [
                {
                    "enrollmentId": "报名ID1",
                    "userId": "用户ID",
                    "userName": "用户名",
                    "status": "已完成"
                }
            ],
            "failed_list": []
        }
    }
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        data = json.loads(request.body)
        
        # 验证access_token
        access_token = data.get('access_token', None)
        if not validate_accessToken(access_token):
            return JsonResponse({'code': 100, 'message': 'Invalidate access token.'})
        
        coach_id = data.get('coach_id')
        course_id = data.get('course_id')
        enrollment_ids = data.get('enrollment_ids', [])
        
        # 参数验证
        if not coach_id:
            return JsonResponse({'code': 400, 'message': '教练ID不能为空'})
        
        if not course_id:
            return JsonResponse({'code': 400, 'message': '课程ID不能为空'})
        
        if not enrollment_ids or len(enrollment_ids) == 0:
            return JsonResponse({'code': 400, 'message': '报名ID列表不能为空'})
        
        # 1. 验证教练权限：检查该课程是否属于该教练
        try:
            course = CoachCourseTable.objects.get(course_id=course_id, is_deleted=False)
        except CoachCourseTable.DoesNotExist:
            return JsonResponse({'code': 404, 'message': '课程不存在'})
        
        # 权限检查：防止其他人员随意核销课程
        if course.coach_id != coach_id:
            logger.warning(f'权限验证失败: 教练{coach_id}尝试核销不属于自己的课程{course_id}，实际教练为{course.coach_id}')
            return JsonResponse({
                'code': 403, 
                'message': '权限不足，只有该课程的教练才能核销学员'
            })
        
        # 2. 批量核销学员
        success_list = []
        failed_list = []
        
        with transaction.atomic():
            for enrollment_id in enrollment_ids:
                try:
                    # 查询报名记录
                    enrollment = CourseEnrollmentTable.objects.get(
                        enrollment_id=enrollment_id,
                        course_id=course_id
                    )
                    
                    # 检查支付状态
                    if enrollment.payment_status != 2:
                        failed_list.append({
                            'enrollmentId': enrollment_id,
                            'reason': '未支付或已退款，无法核销'
                        })
                        continue
                    
                    # 检查报名状态
                    if enrollment.enrollment_status == 3:
                        # 已经是已完成状态
                        success_list.append({
                            'enrollmentId': enrollment_id,
                            'userId': enrollment.user_id,
                            'userName': enrollment.user_name,
                            'status': '已完成',
                            'message': '该学员已核销过'
                        })
                        continue
                    
                    if enrollment.enrollment_status != 1:
                        failed_list.append({
                            'enrollmentId': enrollment_id,
                            'reason': f'报名状态异常: {enrollment.enrollment_status}'
                        })
                        continue
                    
                    # 更新为已完成状态
                    enrollment.enrollment_status = 3  # 3-已完成
                    enrollment.save()
                    
                    success_list.append({
                        'enrollmentId': enrollment_id,
                        'userId': enrollment.user_id,
                        'userName': enrollment.user_name,
                        'status': '已完成'
                    })
                    
                    logger.info(f'核销成功: 课程={course_id}, 教练={coach_id}, 学员={enrollment.user_name}({enrollment.user_id})')
                    
                except CourseEnrollmentTable.DoesNotExist:
                    failed_list.append({
                        'enrollmentId': enrollment_id,
                        'reason': '报名记录不存在或课程不匹配'
                    })
                    logger.warning(f'核销失败: 报名记录不存在 enrollment_id={enrollment_id}')
                    
                except Exception as e:
                    failed_list.append({
                        'enrollmentId': enrollment_id,
                        'reason': str(e)
                    })
                    logger.error(f'核销失败: enrollment_id={enrollment_id}, 错误={str(e)}')
        
        # 返回结果
        success_count = len(success_list)
        failed_count = len(failed_list)
        
        return JsonResponse({
            'code': 200,
            'message': f'核销完成: 成功{success_count}个，失败{failed_count}个',
            'data': {
                'success_count': success_count,
                'failed_count': failed_count,
                'success_list': success_list,
                'failed_list': failed_list
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': 'JSON格式错误'})
    
    except Exception as e:
        logger.error(f'批量核销失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})
