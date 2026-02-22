# -*- coding: utf-8 -*-
"""
公益网球场相关视图
"""
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.db import transaction
from dbModel.models import FreeCourtSlotTable, FreeCourtBookingTable, UserQuotaTable, QuotaHistoryTable
from util.log import logHander
from util.external_api import validate_accessToken
import time
import uuid
import json
from datetime import datetime

logger = logHander(__name__)


def init_user_quota(user_id):
    """
    为新用户初始化配额
    - 每个用户注册后默认获得3次/月的免费抢场配额
    """
    current_month = datetime.now().strftime('%Y-%m')
    current_time = str(int(time.time()))
    
    quota, created = UserQuotaTable.objects.get_or_create(
        user_id=user_id,
        defaults={
            'total_quota': 3,
            'used_quota': 0,
            'available_quota': 3,
            'current_month': current_month,
            'last_reset_time': current_time,
            'bonus_quota': 0,
            'create_time': current_time,
            'update_time': current_time
        }
    )
    
    if created:
        # 记录初始化历史
        QuotaHistoryTable.objects.create(
            user_id=user_id,
            change_type='init',
            change_amount=3,
            reason='用户注册初始化配额',
            before_quota=0,
            after_quota=3,
            change_time=current_time
        )
        logger.info(f'用户{user_id}配额初始化成功')
    
    return quota


def check_and_reset_monthly_quota(user_id):
    """
    检查并重置月度配额
    - 每月1号自动重置为基础配额
    - 分享奖励配额会累积到下月
    """
    current_month = datetime.now().strftime('%Y-%m')
    current_time = str(int(time.time()))
    
    quota = UserQuotaTable.objects.filter(user_id=user_id).first()
    if not quota:
        return init_user_quota(user_id)
    
    # 检查是否需要重置
    if quota.current_month != current_month:
        old_quota = quota.available_quota
        
        # 重置逻辑：基础配额5 + 累积的分享奖励配额
        new_total = 5 + quota.bonus_quota
        
        quota.current_month = current_month
        quota.total_quota = new_total
        quota.used_quota = 0
        quota.available_quota = new_total
        quota.last_reset_time = current_time
        quota.update_time = current_time
        quota.save()
        
        # 记录重置历史
        QuotaHistoryTable.objects.create(
            user_id=user_id,
            change_type='reset',
            change_amount=new_total,
            reason=f'月度重置到{current_month}',
            before_quota=old_quota,
            after_quota=new_total,
            change_time=current_time
        )
        
        logger.info(f'用户{user_id}配额已重置: {current_month}, 新配额: {new_total}')
    
    return quota


def consume_quota(user_id, booking_id, amount=1):
    """
    消耗用户配额（抢场时调用）
    - 原子性操作，确保数据一致性
    - 记录配额变动历史
    """
    current_time = str(int(time.time()))
    
    with transaction.atomic():
        # 先检查月度重置
        quota = check_and_reset_monthly_quota(user_id)
        
        # 检查配额是否足够
        if quota.available_quota < amount:
            raise ValueError('配额不足')
        
        # 扣减配额
        old_quota = quota.available_quota
        quota.used_quota += amount
        quota.available_quota -= amount
        quota.update_time = current_time
        quota.save()
        
        # 记录变动历史
        QuotaHistoryTable.objects.create(
            user_id=user_id,
            change_type='consume',
            change_amount=-amount,
            related_id=booking_id,
            reason=f'抢占公益场次，消耗配额{amount}次',
            before_quota=old_quota,
            after_quota=quota.available_quota,
            change_time=current_time
        )
        
        logger.info(f'用户{user_id}消耗配额{amount}次，剩余{quota.available_quota}次')
        
        return quota


def update_slot_status(slot):
    """
    更新场次状态
    根据时间和配额自动更新状态
    """
    current_timestamp = int(time.time())
    open_timestamp = int(slot.open_time)
    end_timestamp = int(slot.end_time)
    
    if current_timestamp < open_timestamp:
        # 未到开抢时间
        slot.status = 0
    elif current_timestamp > end_timestamp:
        # 已过抢场截止时间
        slot.status = 3
    elif slot.booked_quota >= slot.total_quota:
        # 名额已满
        slot.status = 2
    else:
        # 可以抢场
        slot.status = 1
    
    return slot


@csrf_exempt
def get_free_court_slots(request):
    """
    获取可抢的公益网球场场次列表
    GET /api/free-courts/list
    """
    logger.info(f'get_free_court_slots 收到请求: method={request.method}, path={request.path}, META={request.META}')
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        # 获取筛选参数
        date = request.GET.get('date')
        city = request.GET.get('city')
        district = request.GET.get('district')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        
        # 限制每页最大数量
        page_size = min(page_size, 100)
        
        # 构建查询条件
        filters = {}
        
        if date:
            filters['date'] = date
        
        if city:
            filters['city'] = city
        
        if district:
            filters['district'] = district
        
        # 查询公益场次
        slots = FreeCourtSlotTable.objects.filter(**filters).order_by('date', 'time_slot')
        
        # 更新状态并过滤已结束的场次
        valid_slots = []
        for slot in slots:
            updated_slot = update_slot_status(slot)
            # 只返回未结束的场次
            if updated_slot.status != 3:
                valid_slots.append(updated_slot)
                # 保存状态更新
                if updated_slot.status != slot.status:
                    updated_slot.save()
        
        # 分页
        total = len(valid_slots)
        start = (page - 1) * page_size
        end = start + page_size
        slots_page = valid_slots[start:end]
        
        # 构建返回数据
        slots_list = []
        for slot in slots_page:
            slots_list.append({
                'slotId': slot.slot_id,
                'venueId': slot.venue_id,
                'courtId': slot.court_id,
                'courtName': slot.court_name,
                'venueName': slot.venue_name,
                'location': slot.location,
                'city': slot.city,
                'district': slot.district,
                'date': slot.date,
                'timeSlot': slot.time_slot,
                'totalQuota': slot.total_quota,
                'bookedQuota': slot.booked_quota,
                'status': slot.status,
                'openTime': int(slot.open_time),
                'endTime': int(slot.end_time)
            })
        
        return JsonResponse({
            'code': 200,
            'message': 'OK',
            'data': {
                'slots': slots_list,
                'page': page,
                'pageSize': page_size,
                'total': total
            }
        })
    
    except Exception as e:
        logger.error(f'获取公益场次列表失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def book_free_court(request):
    """
    抢占公益场次（提交公益订场）
    POST /api/free-courts/book
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        data = json.loads(request.body)
        
        slot_id = data.get('slotId')
        user_id = data.get('userId')
        
        if not slot_id or not user_id:
            return JsonResponse({'code': 400, 'message': '参数不完整'})
        
        # 使用事务确保数据一致性
        with transaction.atomic():
            # 1. 查询场次信息
            try:
                slot = FreeCourtSlotTable.objects.select_for_update().get(slot_id=slot_id)
            except FreeCourtSlotTable.DoesNotExist:
                return JsonResponse({'code': 404, 'message': '场次不存在'})
            
            # 2. 更新并检查场次状态
            slot = update_slot_status(slot)
            current_timestamp = int(time.time())
            
            # 时间校验
            if current_timestamp < int(slot.open_time):
                return JsonResponse({'code': 400, 'message': '未到开抢时间'})
            
            if current_timestamp > int(slot.end_time):
                return JsonResponse({'code': 400, 'message': '抢场时间已结束'})
            
            # 名额校验
            if slot.booked_quota >= slot.total_quota:
                return JsonResponse({'code': 400, 'message': '本次公益场名额已抢完'})
            
            # 3. 检查用户是否已经抢过这个场次
            existing_booking = FreeCourtBookingTable.objects.filter(
                slot_id=slot_id,
                user_id=user_id
            ).first()
            
            if existing_booking:
                return JsonResponse({'code': 400, 'message': '您已经抢过此场次'})
            
            # 4. 配额校验和扣减
            try:
                quota = check_and_reset_monthly_quota(user_id)
                if quota.available_quota < 1:
                    return JsonResponse({'code': 400, 'message': '本月公益抢场配额已用完'})
            except Exception as e:
                logger.error(f'配额检查失败: {str(e)}')
                return JsonResponse({'code': 500, 'message': '配额检查失败'})
            
            # 5. 创建订场记录
            booking_id = f"FREE-{slot_id}-{user_id}-{uuid.uuid4().hex[:8]}"
            current_time = str(int(time.time()))
            
            booking = FreeCourtBookingTable.objects.create(
                booking_id=booking_id,
                slot_id=slot_id,
                user_id=user_id,
                date=slot.date,
                time_slot=slot.time_slot,
                court_name=slot.court_name,
                venue_name=slot.venue_name,
                location=slot.location,
                quota_cost=1,
                status='confirmed',
                create_time=current_time
            )
            
            # 6. 更新场次名额
            slot.booked_quota += 1
            slot.update_time = current_time
            
            # 检查是否已满
            if slot.booked_quota >= slot.total_quota:
                slot.status = 2  # 已抢完
            
            slot.save()
            
            # 7. 扣减用户配额
            try:
                consume_quota(user_id, booking_id, 1)
            except ValueError as ve:
                # 这里理论上不会发生，因为前面已经检查过
                logger.error(f'配额扣减失败: {str(ve)}')
                raise transaction.TransactionManagementError('配额扣减失败')
            
            logger.info(f'公益场抢场成功: 用户{user_id}, 场次{slot_id}, 订场ID{booking_id}')
        
        return JsonResponse({
            'code': 200,
            'message': '抢场成功',
            'data': {
                'bookingId': booking_id,
                'slotId': slot_id,
                'quotaCost': 1
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': 'JSON格式错误'})
    
    except Exception as e:
        logger.error(f'抢场失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def get_my_free_court_bookings(request):
    """
    获取当前用户的公益订场记录
    GET /api/free-courts/my-bookings
    """
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        user_id = request.GET.get('userId')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('pageSize', 20))
        
        if not user_id:
            return JsonResponse({'code': 400, 'message': '用户ID不能为空'})
        
        # 限制每页最大数量
        page_size = min(page_size, 100)
        
        # 查询用户的订场记录
        bookings = FreeCourtBookingTable.objects.filter(
            user_id=user_id
        ).order_by('-create_time')
        
        # 分页
        total = bookings.count()
        start = (page - 1) * page_size
        end = start + page_size
        bookings_page = bookings[start:end]
        
        # 构建返回数据
        bookings_list = []
        for booking in bookings_page:
            bookings_list.append({
                'bookingId': booking.booking_id,
                'slotId': booking.slot_id,
                'date': booking.date,
                'timeSlot': booking.time_slot,
                'courtName': booking.court_name,
                'venueName': booking.venue_name,
                'location': booking.location,
                'quotaCost': booking.quota_cost,
                'status': booking.status,
                'createTime': int(booking.create_time)
            })
        
        return JsonResponse({
            'code': 200,
            'message': 'OK',
            'data': {
                'bookings': bookings_list,
                'page': page,
                'pageSize': page_size,
                'total': total
            }
        })
    
    except Exception as e:
        logger.error(f'获取用户订场记录失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def get_quota_info(request):
    """
    查询用户配额信息
    GET /api/quota/info
    """
    if request.method != 'GET':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        user_id = request.GET.get('userId')
        if not user_id:
            return JsonResponse({'code': 400, 'message': '用户ID不能为空'})
        
        # 检查并重置配额
        quota = check_and_reset_monthly_quota(user_id)
        
        return JsonResponse({
            'code': 200,
            'message': 'OK',
            'data': {
                'total_quota': quota.total_quota,
                'used_quota': quota.used_quota,
                'available_quota': quota.available_quota,
                'bonus_quota': quota.bonus_quota,
                'current_month': quota.current_month,
                'last_reset_time': int(quota.last_reset_time)
            }
        })
    
    except Exception as e:
        logger.error(f'查询配额失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})


@csrf_exempt
def add_bonus_quota(request):
    """
    分享奖励配额
    POST /api/quota/bonus
    - 通过邀请朋友获得额外配额
    - 奖励配额会在下月重置时累积到总配额中
    """
    if request.method != 'POST':
        return JsonResponse({'code': 405, 'message': '方法不允许'})
    
    try:
        data = json.loads(request.body)
        
        user_id = data.get('userId')
        share_id = data.get('shareId', '')
        amount = int(data.get('amount', 1))
        
        if not user_id:
            return JsonResponse({'code': 400, 'message': '用户ID不能为空'})
        
        current_time = str(int(time.time()))
        
        with transaction.atomic():
            quota = check_and_reset_monthly_quota(user_id)
            
            old_quota = quota.available_quota
            
            # 增加奖励配额（立即可用）
            quota.bonus_quota += amount
            quota.available_quota += amount
            quota.total_quota += amount
            quota.update_time = current_time
            quota.save()
            
            # 记录变动历史
            QuotaHistoryTable.objects.create(
                user_id=user_id,
                change_type='bonus',
                change_amount=amount,
                related_id=share_id,
                reason=f'分享邀请奖励，获得{amount}次配额',
                before_quota=old_quota,
                after_quota=quota.available_quota,
                change_time=current_time
            )
            
            logger.info(f'用户{user_id}获得分享奖励配额{amount}次')
        
        return JsonResponse({
            'code': 200,
            'message': '奖励配额添加成功',
            'data': {
                'added_quota': amount,
                'total_quota': quota.total_quota,
                'available_quota': quota.available_quota
            }
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'code': 400, 'message': 'JSON格式错误'})
    
    except Exception as e:
        logger.error(f'添加奖励配额失败: {str(e)}', exc_info=True)
        return JsonResponse({'code': 500, 'message': f'服务器错误: {str(e)}'})