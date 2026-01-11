from django.db import models


class ActivityInfoTable(models.Model):
    """活动信息表"""
    act_id = models.CharField(verbose_name="活动id", max_length=64, primary_key=True)
    coop_id = models.CharField(verbose_name="商户ID", max_length=64)
    type_en = models.CharField(verbose_name="英文活动类型名称", max_length=64)
    type_zh = models.CharField(verbose_name="中文活动类型名称", max_length=64)
    title_en = models.CharField(verbose_name="英文活动标题", max_length=32)
    title_zh = models.CharField(verbose_name="中文活动标题", max_length=32)
    pic = models.CharField(verbose_name="活动图片链接：注意图片大小/像素等", max_length=128)
    loc_code = models.CharField(verbose_name="地区编码", max_length=32)
    tag = models.CharField(verbose_name="活动自定义表示，属于Y-Club or others", max_length=32)
    detail_en = models.CharField(verbose_name="英文活动详情描述", max_length=256)
    detail_zh = models.CharField(verbose_name="中文活动详情描述", max_length=256)
    is_recommend = models.IntegerField(verbose_name="1-推荐 0-不推荐（默认置0）")
    price = models.FloatField(verbose_name="活动价格都以人民币存储", max_length=64)
    start_time = models.CharField(verbose_name="活动开始时间", max_length=64)
    end_time = models.CharField(verbose_name="活动结束时间", max_length=64)
    address = models.CharField(verbose_name="地址", max_length=128)
    longitude = models.CharField(verbose_name="经度", max_length=32)
    latitude = models.CharField(verbose_name="纬度", max_length=32)

    class Meta:
        db_table = "活动信息表"
        get_latest_by = "start_time"
        ordering = ['start_time']
        verbose_name = "actInfo"


class MerchantInfoTable(models.Model):
    """商家信息表"""
    coop_id = models.CharField(verbose_name="商户ID", max_length=64, primary_key=True)
    type_en = models.CharField(verbose_name="商户类型: ", max_length=64)
    type_zh = models.CharField(verbose_name="商户类型: ", max_length=64)
    pic = models.CharField(verbose_name="商户图片链接", max_length=128)
    loc_code = models.CharField(verbose_name="地区编码", max_length=32)
    name = models.CharField(verbose_name="商家名称", max_length=16)
    wechatid = models.CharField(verbose_name="商家微信ID", max_length=32)
    email = models.CharField(verbose_name="商家邮箱", max_length=32)
    detail_en = models.CharField(verbose_name="英文活动详情描述", max_length=256)
    detail_zh = models.CharField(verbose_name="中文活动详情描述", max_length=256)
    address = models.CharField(verbose_name="地址", max_length=128)
    longitude = models.CharField(verbose_name="经度", max_length=32)
    latitude = models.CharField(verbose_name="纬度", max_length=32)
    register_time = models.CharField(verbose_name="商户注册时间", max_length=64)

    class Meta:
        db_table = "商家信息表"
        get_latest_by = "register_time"
        ordering = ['register_time']
        verbose_name = "merchInfo"


class UserOrderTable(models.Model):
    """用户订单表"""
    order_id = models.CharField(verbose_name="订单ID：32个字符内，只能是数字、大小写字母_-|*且在同一个商户号下唯一。", max_length=32, primary_key=True)
    uid = models.CharField(verbose_name="用户ID", max_length=64)
    act_id = models.CharField(verbose_name="活动ID", max_length=64)
    coop_id = models.CharField(verbose_name="商户ID", max_length=64)
    pay_time = models.CharField(verbose_name="支付日期", max_length=64, null=True, blank=True)
    order_time = models.CharField(verbose_name="下单日期", max_length=64, null=True, blank=True)
    exp_time = models.IntegerField(verbose_name="过期时间")
    paymentid = models.CharField(verbose_name="支付ID：成功支付才存在，否则为空", max_length=128)
    order_status = models.IntegerField(verbose_name="订单状态：1-未支付 2-支付成功 3-支付失败")
    refund_status = models.IntegerField(verbose_name="退款状态：0-未退款 1-部分退款 2-全额退款", default=0)

    class Meta:
        db_table = "user_order"
        get_latest_by = "pay_time"
        ordering = ['pay_time']
        verbose_name = "userOrder"


class ActsMarkTable(models.Model):
    """收藏活动表"""
    act_id = models.CharField(verbose_name="活动id", max_length=64, primary_key=True)
    uid = models.CharField(verbose_name="用户ID", max_length=64)
    is_mark = models.IntegerField(verbose_name="收藏状态：0-未收藏；1-收藏")
    mask_time = models.CharField(verbose_name="收藏日期", max_length=64)

    class Meta:
        db_table = "活动收藏表"
        get_latest_by = "mask_time"
        ordering = ['mask_time']
        verbose_name = "userAct"


class MerchantMaskTable(models.Model):
    """收藏商家表"""
    coop_id = models.CharField(verbose_name="商户id", max_length=64, primary_key=True)
    uid = models.CharField(verbose_name="用户ID", max_length=64)
    is_mark = models.IntegerField(verbose_name="收藏商家状态：0-未收藏；1-收藏")
    mask_time = models.CharField(verbose_name="收藏日期", max_length=64)

    class Meta:
        db_table = "商家收藏表"
        get_latest_by = "mask_time"
        ordering = ['mask_time']
        verbose_name = "userFav"


class AreaCodeTable(models.Model):
    """地区编码表"""
    loc_code = models.CharField(verbose_name="地区编码", max_length=64, primary_key=True)
    eng_name = models.CharField(verbose_name="英文", max_length=64)
    chn_name = models.CharField(verbose_name="中文", max_length=64)

    class Meta:
        db_table = "地区编码表"


class UserInforTable(models.Model):
    """用户信息表（会员标记）"""
    uid = models.CharField(verbose_name="用户id", max_length=64, primary_key=True)
    name = models.CharField(verbose_name="用户名称", max_length=16, unique=True)  # 添加唯一性约束
    pic = models.CharField(verbose_name="用户头像图片链接", max_length=128)
    profile = models.CharField(verbose_name="用户个人简介", max_length=256)
    location = models.CharField(verbose_name="用户地址", max_length=256)
    register_time = models.CharField(verbose_name="注册日期", max_length=64)
    # level = models.IntegerField(verbose_name="会员等级")
    # level_status = models.IntegerField(verbose_name="状态：0-已过期；1-正常")
    # wechat = models.CharField(verbose_name="微信ID", max_length=32)
    # email = models.CharField(verbose_name="邮箱用户", max_length=64)
    # phone_no = models.CharField(verbose_name="电话号码", max_length=32)
    class Meta:
        db_table = "user_info"
        get_latest_by = "register_time"
        ordering = ['register_time']
        verbose_name = "user_info"


class UserRatingTable(models.Model):
    """用户评分表（用户评分）"""
    uid = models.CharField(verbose_name="用户id", max_length=100, primary_key=True)
    tech_one = models.CharField(verbose_name="用户正手评分", max_length=10)
    tech_two = models.CharField(verbose_name="反手评分", max_length=10)
    tech_three = models.CharField(verbose_name="动作控点评分", max_length=10)
    tech_four = models.CharField(verbose_name="切削评分", max_length=10)
    tech_five = models.CharField(verbose_name="发球评分", max_length=10)
    person_one = models.CharField(verbose_name="沟通评分", max_length=10)
    person_two = models.CharField(verbose_name="时间观念评分", max_length=10)
    person_three = models.CharField(verbose_name="竞技精神评分", max_length=10)
    person_four = models.CharField(verbose_name="形象评分", max_length=10)
    person_five = models.CharField(verbose_name="慷慨度评分", max_length=10)
    class Meta:
        db_table = "user_rating"
        get_latest_by = "uid"
        ordering = ['uid']
        verbose_name = "user_rating"


class UserInvTable(models.Model):
    """用户邀请表（用户邀请表）"""
    inv_id = models.CharField(verbose_name="约球id", max_length=100, primary_key=True)
    inviterId = models.CharField(verbose_name="邀请者用户id", max_length=100)
    inviteeId = models.CharField(verbose_name="被邀者用户id", max_length=10)
    matchTime = models.CharField(verbose_name="约球时间", max_length=10)
    msg = models.CharField(verbose_name="约球信息", max_length=10)
    place = models.CharField(verbose_name="约球地点", max_length=10)
    status = models.CharField(verbose_name="状态 0-邀请中 1-已接受", max_length=10)
    other = models.CharField(verbose_name="其他", max_length=10)
    createTime = models.CharField(verbose_name="创建时间", max_length=10)
    
    class Meta:
        db_table = "user_inv"
        get_latest_by = "createTime"
        ordering = ['createTime']
        verbose_name = "user_inv"


class UserFriendTable(models.Model):
    """用户好友表"""
    id = models.AutoField(primary_key=True)  # 添加这一行
    userId = models.CharField(verbose_name="用户id", max_length=100)
    friendId = models.CharField(verbose_name="好友id", max_length=100)
    createTime = models.CharField(verbose_name="创建时间", max_length=64)
    other = models.CharField(verbose_name="其他", max_length=256, blank=True, null=True)
    
    class Meta:
        db_table = "user_friend"
        unique_together = ('userId', 'friendId')  # 确保同一对好友关系不会重复
        get_latest_by = "createTime"
        ordering = ['createTime']
        verbose_name = "user_friend"

class UserRatingLongTable(models.Model):
    """用户长周期评分表（用户评分）"""
    uid = models.CharField(verbose_name="用户id", max_length=100, primary_key=True)
    tech_one = models.CharField(verbose_name="用户正手评分", max_length=10)
    tech_two = models.CharField(verbose_name="反手评分", max_length=10)
    tech_three = models.CharField(verbose_name="动作控点评分", max_length=10)
    tech_four = models.CharField(verbose_name="切削评分", max_length=10)
    tech_five = models.CharField(verbose_name="发球评分", max_length=10)
    person_one = models.CharField(verbose_name="沟通评分", max_length=10)
    person_two = models.CharField(verbose_name="时间观念评分", max_length=10)
    person_three = models.CharField(verbose_name="竞技精神评分", max_length=10)
    person_four = models.CharField(verbose_name="形象评分", max_length=10)
    person_five = models.CharField(verbose_name="慷慨度评分", max_length=10)
    n = models.CharField(verbose_name="评分记录总数", max_length=10)
    class Meta:
        db_table = "user_rating_long"
        get_latest_by = "uid"
        ordering = ['uid']
        verbose_name = "user_rating_long"

class UserRatingShortTable(models.Model):
    """用户短周期评分表（用户评分）"""
    id = models.AutoField(primary_key=True)  # 添加主键字段
    uid = models.CharField(verbose_name="用户id", max_length=100)
    tech_one = models.CharField(verbose_name="用户正手评分", max_length=10)
    tech_two = models.CharField(verbose_name="反手评分", max_length=10)
    tech_three = models.CharField(verbose_name="动作控点评分", max_length=10)
    tech_four = models.CharField(verbose_name="切削评分", max_length=10)
    tech_five = models.CharField(verbose_name="发球评分", max_length=10)
    person_one = models.CharField(verbose_name="沟通评分", max_length=10)
    person_two = models.CharField(verbose_name="时间观念评分", max_length=10)
    person_three = models.CharField(verbose_name="竞技精神评分", max_length=10)
    person_four = models.CharField(verbose_name="形象评分", max_length=10)
    person_five = models.CharField(verbose_name="慷慨度评分", max_length=10)
    rating_time = models.CharField(verbose_name="评分时间", max_length=64)
    class Meta:
        db_table = "user_rating_short"
        get_latest_by = "uid"
        ordering = ['uid']
        verbose_name = "user_rating_short"


class CoachCourseTable(models.Model):
    """教练课程表"""
    course_id = models.CharField(verbose_name="课程ID", max_length=64, primary_key=True)
    coach_id = models.CharField(verbose_name="教练ID", max_length=64)
    coach_name = models.CharField(verbose_name="教练姓名", max_length=32)
    
    # 课程信息
    title = models.CharField(verbose_name="课程标题", max_length=128)
    description = models.TextField(verbose_name="课程描述")
    cover_image = models.CharField(verbose_name="封面图片", max_length=256)
    level = models.CharField(verbose_name="课程级别", max_length=32)  # beginner/intermediate/advanced
    category = models.CharField(verbose_name="课程分类", max_length=32)  # technique/physical/strategy等
    
    # 时间和地点
    course_date = models.CharField(verbose_name="课程日期", max_length=32)  # YYYY-MM-DD
    course_time = models.CharField(verbose_name="课程时间", max_length=16)  # HH:MM
    duration = models.IntegerField(verbose_name="课程时长(分钟)")
    location = models.CharField(verbose_name="上课地点", max_length=256)
    
    # 学员人数
    min_students = models.IntegerField(verbose_name="最少学员数")
    max_students = models.IntegerField(verbose_name="最多学员数")
    current_students = models.IntegerField(verbose_name="当前报名人数", default=0)
    
    # 价格信息
    original_price = models.DecimalField(verbose_name="原价", max_digits=10, decimal_places=2)
    current_price = models.DecimalField(verbose_name="现价", max_digits=10, decimal_places=2)
    
    # 状态和时间戳
    status = models.IntegerField(verbose_name="课程状态", default=1)  # 1-待开课 2-进行中 3-已结束 4-已取消
    is_deleted = models.BooleanField(verbose_name="是否删除", default=False)
    create_time = models.CharField(verbose_name="创建时间", max_length=64)
    update_time = models.CharField(verbose_name="更新时间", max_length=64, null=True, blank=True)
    
    class Meta:
        db_table = "coach_course"
        get_latest_by = "create_time"
        ordering = ['-create_time']
        verbose_name = "教练课程"
        indexes = [
            models.Index(fields=['coach_id', 'course_date']),
            models.Index(fields=['status', 'course_date']),
        ]


class CourseEnrollmentTable(models.Model):
    """课程报名表"""
    enrollment_id = models.CharField(verbose_name="报名ID", max_length=64, primary_key=True)
    course_id = models.CharField(verbose_name="课程ID", max_length=64)
    user_id = models.CharField(verbose_name="用户ID", max_length=64)
    user_name = models.CharField(verbose_name="用户姓名", max_length=32)
    
    # 订单信息
    order_id = models.CharField(verbose_name="订单ID", max_length=64, null=True, blank=True)
    payment_status = models.IntegerField(verbose_name="支付状态", default=1)  # 1-未支付 2-已支付 3-已退款
    paid_amount = models.DecimalField(verbose_name="支付金额", max_digits=10, decimal_places=2)
    
    # 状态和时间
    enrollment_status = models.IntegerField(verbose_name="报名状态", default=1)  # 1-已报名 2-已取消 3-已完成
    enroll_time = models.CharField(verbose_name="报名时间", max_length=64)
    cancel_time = models.CharField(verbose_name="取消时间", max_length=64, null=True, blank=True)
    
    class Meta:
        db_table = "course_enrollment"
        get_latest_by = "enroll_time"
        ordering = ['-enroll_time']
        verbose_name = "课程报名"
        indexes = [
            models.Index(fields=['course_id', 'enrollment_status']),
            models.Index(fields=['user_id', 'enrollment_status']),
        ]


class RefundOrderTable(models.Model):
    """退款订单表"""
    refund_id = models.CharField(verbose_name="退款单号", max_length=64, primary_key=True)
    order_id = models.CharField(verbose_name="原订单ID", max_length=64)
    transaction_id = models.CharField(verbose_name="微信支付订单号", max_length=64)
    user_id = models.CharField(verbose_name="用户ID", max_length=64)
    
    # 金额信息（单位：分）
    total_amount = models.IntegerField(verbose_name="原订单金额(分)")
    refund_amount = models.IntegerField(verbose_name="退款金额(分)")
    
    # 退款原因和状态
    refund_reason = models.CharField(verbose_name="退款原因", max_length=256)
    refund_status = models.IntegerField(verbose_name="退款状态", default=1)  
    # 1-退款中 2-退款成功 3-退款失败 4-退款关闭
    
    # 时间戳
    refund_time = models.CharField(verbose_name="发起退款时间", max_length=64)
    success_time = models.CharField(verbose_name="退款成功时间", max_length=64, null=True, blank=True)
    
    # 微信退款单号
    wx_refund_id = models.CharField(verbose_name="微信退款单号", max_length=64, null=True, blank=True)
    
    # 课程相关（如果是课程退款）
    course_id = models.CharField(verbose_name="课程ID", max_length=64, null=True, blank=True)
    enrollment_id = models.CharField(verbose_name="报名ID", max_length=64, null=True, blank=True)
    
    class Meta:
        db_table = "refund_order"
        get_latest_by = "refund_time"
        ordering = ['-refund_time']
        verbose_name = "退款订单"
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['user_id', 'refund_status']),
        ]
