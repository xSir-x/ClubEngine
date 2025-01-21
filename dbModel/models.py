from django.db import models


class ActivityInfoTable(models.Model):
    """活动信息表"""
    act_id = models.CharField(verbose_name="活动id", max_length=64, primary_key=True)
    coop_id = models.CharField(verbose_name="商户ID", max_length=64)
    type = models.CharField(verbose_name="活动类型: ongoing/past/new(入参可all)", max_length=64)
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
    type = models.CharField(verbose_name="商户类型: ", max_length=64)
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

    class Meta:
        db_table = "用户订单表"
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
    name = models.CharField(verbose_name="用户名称", max_length=16)
    level = models.IntegerField(verbose_name="会员等级")
    exptime = models.IntegerField(verbose_name="过期日期")
    level_status = models.IntegerField(verbose_name="状态：0-已过期；1-正常")
    wechat = models.CharField(verbose_name="微信ID", max_length=32)
    pic = models.CharField(verbose_name="用户头像图片链接", max_length=128)
    profile = models.CharField(verbose_name="用户个人简介", max_length=256)
    email = models.CharField(verbose_name="邮箱用户", max_length=64)
    phone_no = models.CharField(verbose_name="电话号码", max_length=32)
    location = models.CharField(verbose_name="用户地址", max_length=256)
    register_time = models.CharField(verbose_name="注册日期", max_length=64)

    class Meta:
        db_table = "用户信息表"
        get_latest_by = "register_time"
        ordering = ['register_time']
        verbose_name = "userInfo"
