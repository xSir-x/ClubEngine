from django.views import View
from dbModel.models import ActivityInfoTable, MerchantInfoTable, UserInforTable, MerchantMaskTable, ActsMarkTable, \
    UserOrderTable, UserRatingTable, UserInvTable, UserFriendTable, UserRatingLongTable, UserRatingShortTable
# from django.utils import timezone
import time
from datetime import datetime, timedelta
from django.core.cache import cache
from util.external_api import store_in_redis, retrieve_from_redis
from django.db import transaction

from util.log import logHander

_logger = logHander(__name__)


## 活动板块
class addFavActivity(View):
    @classmethod
    def execute(cls, need_fav: bool, act_id: str, uid: str):
        """
        收藏活动操作: 收藏成功返回1，否则返回0
        :param need_fav: bool
        :param act_id:
        :param uid:
        :return:
        """
        mask_time = str(int(time.time() * 1000))  # 修改为毫秒级时间戳
        try:
            fav_act_obj = ActsMarkTable.objects.filter(uid=uid, act_id=act_id)
            if fav_act_obj.exists():
                is_mark = fav_act_obj.values("is_mark")[0]["is_mark"]
                if need_fav:
                    if is_mark != 1:
                        ActsMarkTable.objects.filter(uid=uid, act_id=act_id). \
                            update(is_mark=1, mask_time=mask_time)
                else:
                    if is_mark != 0:
                        ActsMarkTable.objects.filter(uid=uid, act_id=act_id). \
                            update(is_mark=0, mask_time=mask_time)
            else:
                if need_fav:
                    ActsMarkTable.objects. \
                        create(uid=uid, act_id=act_id, is_mark=1, mask_time=mask_time)
                else:
                    ActsMarkTable.objects. \
                        filter(uid=uid, act_id=act_id). \
                        update(is_mark=0, mask_time=mask_time)
            return 1, "活动收藏成功!"
        except Exception as e:
            message = "【addFavActivity】数据库【ActsMarkTable】操作收藏活动失败: %s" % e
            _logger.error(message)
            return 0, message


class getAllType(View):
    @classmethod
    def execute(cls, loc_code: str, lang: str):
        """
        获取所有活动类型: 根据loc_code 查询该地区所有活动的type
        :param loc_code:
        :param lang: 语言类型
        :return:
            [{"type": "活动类型1"}, {"type": "活动类型2"}, ...]
        """
        res = []
        try:
            acts_obj = ActivityInfoTable.objects.filter(loc_code=loc_code)
            if acts_obj.exists():
                act_types = acts_obj.values("type_en") \
                    if lang == "en" else acts_obj.values("type_zh")
                dummp = []
                for item in act_types:
                    _type = list(item)[-1]
                    if _type not in dummp:
                        res.append(item)
                    dummp.append(_type)
            return res
        except Exception as e:
            raise Exception("【getAllType】查询数据库【ActivityInfoTable】[err: %s]异常..." % e)


def filter_lang(item_info, lang: str):
    """
    根据语言进行过滤
    :param item_info:
    :param lang:
    :return:
    """
    if lang == "zh":
        if "detail_zh" in item_info:
            item_info.pop("detail_en")
        if "title_zh" in item_info:
            item_info.pop("title_en")
        if "type_zh" in item_info:
            item_info.pop("type_en")
    elif lang == "en":
        if "detail_en" in item_info:
            item_info.pop("detail_zh")
        if "title_en" in item_info:
            item_info.pop("title_zh")
        if "type_en" in item_info:
            item_info.pop("type_zh")
    return item_info


def get_activity_dets(act_det, lang: str):
    """
    多表查询获取单个活动的所有信息: 包含活动信息表的所有信息、is_mark(活动是否被收藏)、attendence(被哪些收藏，收藏者的pic)
    :param act_det: 字典格式
    :param lang:
    :return:
    """
    try:
        act_det = filter_lang(act_det, lang)
        _logger.info(" >>[GET is_mark]: input: %s." % act_det)
        # 查询表【ActsMarkTable】获取is_mark字段
        act_id = act_det.get("act_id", None)
        actmark_obj = ActsMarkTable.objects.filter(act_id=act_id)
        is_mark = actmark_obj.values("is_mark")[0]["is_mark"] if actmark_obj.exists() else 0
        act_det.update({"is_mark": is_mark})
        # 查询订单表【UserOrderTable】获取"pic"字段追加到 attendence
        _logger.info(" >>: act_id: %s, is_mark: %s" % (act_id, is_mark))
        act_det.update({"attendence": get_attendence(act_id)})
        return act_det
    except Exception as e:
        raise Exception("查询数据库 get attendence 异常: %s." % e)


def get_attendence(act_id):
    """获取attendence"""
    try:
        order2_obj = UserOrderTable.objects.filter(act_id=act_id, order_status=2)
        _logger.info(" >>[GET attendence]: act_id:%s, obj: %s" % (act_id, order2_obj))
        attendence = []
        if order2_obj.exists():
            att_uids = order2_obj.values("uid")
            _logger.info(" >>: att_uids: %s" % (att_uids))
            for _item in att_uids:
                uid = _item.get("uid", None)
                if uid:
                    _pic_obj = UserInforTable.objects.filter(uid=uid)
                    if _pic_obj.exists():
                        for item in _pic_obj.values("pic"):
                            pic = list(item)[-1]
                            attendence.append(pic)
        return attendence
    except Exception as e:
        raise Exception("查询数据库 get attendence 异常: %s." % e)


class getActivitiesByType(View):
    @classmethod
    def execute(cls, type: str, loc_code: str, lang: str, timeout=300, pageId=0, pageSize=7):
        """
        获取所有活动列表: s1: 查询ActivityInfoTable获取所有的活动
        s2: 根据活动信息查询is_mark和attendence(通过act_id查询UserOrderTable中order_status=2的pic)
        :param type: 活动类型
        :param loc_code: 活动区域
        :param lang: 活动语言
        :param pageId: 指定pageID
        :param pageSize: 活动页数
        :return: List[dict{}, ...]
        """

        size, page = 0, []
        try:
            _logger.info("*** GET_ACTS_BYTYPE >> type: %s, loc_code: %s, lang: %s" % (type, loc_code, lang))
            key = type + "#" + str(loc_code) + "#" + lang
            his_cache = retrieve_from_redis(key)
            _logger.info(" >>: cache验证: %s" % his_cache)
            if his_cache is not None:
                his_cache = eval(his_cache)
                size = len(his_cache)
                page = his_cache[pageId] if pageId < size else []
                return page, size
            else:
                res = []
                type, lang = type.lower(), lang.lower()
                actinfo_obj = None
                if type == "all":
                    actinfo_obj = ActivityInfoTable.objects.filter(loc_code=loc_code)
                else:
                    actinfo_obj = ActivityInfoTable.objects.filter(loc_code=loc_code, type_en=type) \
                        if lang == "en" else \
                        ActivityInfoTable.objects.filter(loc_code=loc_code, type_zh=type)
                _logger.info(" >>: cache为空，查表, actinfo_obj: %s." % actinfo_obj)
                if actinfo_obj.exists():
                    type_acts = actinfo_obj.values()
                    temp = []
                    for i, act_item in enumerate(type_acts):
                        if len(temp) > pageSize:
                            res.append(temp)
                            temp = []
                        _logger.info(" >>: ITEM: %s" % act_item)
                        temp.append(get_activity_dets(act_item, lang))
                    if len(temp) > 0:
                        res.append(temp)
                    size = len(res)
                    _logger.info(" >>: pageId: %s, res: %s" % (pageId, res))
                    store_in_redis(key, str(res), timeout)
                page = res[pageId] if pageId < size else []
                _logger.info("*** output[GET_ACTS_BYTYPE]: size: %s, page: %s." % (size, page))
                return page, size
        except Exception as e:
            raise Exception("【getActivitiesByType】异常...: %s." % e)


class getRecommandActivities(View):
    @classmethod
    def execute(cls, loc_code: str, lang: str):
        """
        获取活动推荐列表:  s1: 根据loc_code&is_recommand=1两个字段查询ActivityInfoTable获取所有的活动
        s2: 根据活动信息查询is_mark和attendence(通过act_id查询UserOrderTable中order_status=2的pic)
        :param loc_code:
        :param lang:
        :return: List[dict{},]
        """
        res = []
        try:
            recomm_act_obj = ActivityInfoTable.objects.filter(loc_code=loc_code, is_recommend=1)
            if recomm_act_obj.exists():
                recomm_acts = recomm_act_obj.values()
                for i, act_item in enumerate(recomm_acts):
                    act_item = get_activity_dets(act_item, lang)
                    res.append(act_item)
            return res
        except Exception as e:
            raise Exception("【getRecommandActivities】查询数据库【ActivityInfoTable】[%s]异常: %s" % (loc_code, e))


class getSingleActivityDetail(View):
    def execute(self, act_id, type: str, lang: str):
        """
        获取单个活动细节: s1: 根据act_id&type两个字段查询ActivityInfoTable某个的活动
        s2: 根据活动信息查询is_mark和attendence(通过act_id查询UserOrderTable中order_status=2的pic)

        :param act_id:
        :param type:
        :param lang:
        :return: dict{}
        """
        try:
            act_det = {}
            act_obj = ActivityInfoTable.objects.filter(act_id=act_id, type_en=type) \
                if lang == "en" else ActivityInfoTable.objects.filter(act_id=act_id, type_zh=type)
            if act_obj.exists():
                act_info = act_obj.values()[0]
                act_det = get_activity_dets(act_info, lang)
            return act_det
        except Exception as e:
            raise Exception("【getSingleActivityDetail】查询数据库【ActivityInfoTable or UserOrderTable】异常: %s" % e)


class getMyActivitiesBytype(View):
    def execute(self, uid, lang, type="ALL"):
        """
        获取我的活动列表: 根据uid&type两个字段查询ActivityInfoTable某个的活动
        :param uid:
        :param lang: zh or en
        :param type:
        :return: List[dict{},]
        """
        res = []
        try:
            type = type.lower()
            lang = lang.lower()
            acts_obj = UserOrderTable.objects.filter(uid=uid)
            if acts_obj.exists():
                my_acts = acts_obj.values("act_id", "order_id", "order_status")
                for item in my_acts:
                    item_obj = None
                    if type == "all":
                        item_obj = ActivityInfoTable.objects. \
                            filter(act_id=item.get("act_id", None))
                    elif lang == "en":
                        item_obj = ActivityInfoTable.objects. \
                            filter(act_id=item.get("act_id", None), type_en=type)
                    elif lang == "zh":
                        item_obj = ActivityInfoTable.objects. \
                            filter(act_id=item.get("act_id", None), type_zh=type)
                    if not item_obj.exists():
                        continue
                    f_items = item_obj.values()
                    for _item_info in f_items:
                        item_info = filter_lang(_item_info, lang)
                        item_info.update(item)
                        res.append(item_info)
            return res
        except Exception as e:
            raise Exception("【getMyActivitiesBytype】查询数据库【UserOrderTable】异常: %s." % e)


class getMySingleActivity(View):
    def execute(self, order_id, uid, lang):
        """
        获取我的单个活动列表: 根据 uid & order_id 查询UserOrderTable，获取act_id，再根据act_id查询ActivityInfoTable
        :param order_id:
        :param uid:
        :param lang: zh or en
        :return: Dict{}
        """
        res = []
        try:
            my_act_obj = UserOrderTable.objects.filter(uid=uid, order_id=order_id)
            if my_act_obj.exists():
                order_infos = my_act_obj.values()
                for order in order_infos:
                    act_det_obj = ActivityInfoTable.objects.filter(act_id=order.get("act_id"))
                    if not act_det_obj.exists():
                        continue
                    act_det = act_det_obj.values()
                    for _det in act_det:
                        item_info = filter_lang(_det, lang)
                        item_info.update(order)
                        res.append(item_info)
            return res
        except Exception as e:
            raise Exception("【getMySingleActivity】查询数据库【UserOrderTable】异常: %s" % e)


## 商家板块
class addCoopFav(View):
    def execute(self, need_fav, uid, coop_id):
        """
        收藏商家:
        Roc update： 根据uid + coopid 查询用户商户收藏表，有的话把is_mark置1， 无的话，新增一条记录并且把is_mark字段置1
        :param uid:
        :param coop_id:
        :return:
        """
        message = "ok!"
        try:
            mask_time = str(int(time.time() * 1000))  # 修改为毫秒级时间戳
            fav_act_obj = MerchantMaskTable.objects.filter(uid=uid, coop_id=coop_id)
            if fav_act_obj.exists():
                is_mark = fav_act_obj.values("is_mark")[0]["is_mark"]
                if need_fav:
                    if is_mark != 1:
                        MerchantMaskTable.objects.filter(uid=uid, coop_id=coop_id). \
                            update(is_mark=1, mask_time=mask_time)
                else:
                    if is_mark != 0:
                        MerchantMaskTable.objects.filter(uid=uid, coop_id=coop_id). \
                            update(is_mark=0, mask_time=mask_time)
            else:
                if need_fav:
                    MerchantMaskTable.objects. \
                        create(uid=uid, coop_id=coop_id, is_mark=1, mask_time=mask_time)
                else:
                    MerchantMaskTable.objects.filter(uid=uid, coop_id=coop_id). \
                        update(is_mark=0, mask_time=mask_time)
            return 1, message
        except Exception as e:
            print("【addCoopFav】收藏商家异常: %s" % e)
            return 0, message


class getClubCoopListType(View):
    def execute(self, loc_code, lang):
        """
        获取合作商家类型：
        Roc update： 根据字段[loc_code]读取MerchantInfoTable中对应的type字段，返回地区下的所有type ， 数据返回类型list of type
        :param loc_code:
        :return:
            [{"coopid": coopid, "type": type},
            ...]
        """
        res = []
        try:
            merch_obj = MerchantInfoTable.objects.filter(loc_code=loc_code)
            if merch_obj.exists():
                merch_types = merch_obj.values("type_en") \
                    if lang.lower() == "en" else merch_obj.values("type_zh")
                dummp = []
                for item in merch_types:
                    _type = list(item)[-1]
                    if _type not in dummp:
                        res.append(item)
                    dummp.append(_type)
            return res
        except Exception as e:
            raise Exception("【getClubCoopListType】获取合作商家失败: %s" % e)


class getClubCoopListByType(View):
    def execute(self, type, loc_code, lang, timeout=300, pageId=0, pageSize=7):
        """
        获取合作商家信息: 根据type, loc_code, lang 过滤 MerchantInfoTable
        :param type:
        :param loc_code:
        :param lang:
        :param pageId:
        :param pageSize:
        :return:
        """
        try:
            res = []
            page_res, cache_size = [], 0
            key = "CLUBCOOP#" + type + "#" + loc_code + "#" + lang
            his_cache = retrieve_from_redis(key)
            if his_cache is not None:
                his_cache = eval(his_cache)
                cache_size = len(his_cache) if his_cache else 0
                page_res = his_cache[pageId] if pageId < cache_size else []
                return page_res, cache_size
            else:
                type, lang = type.lower(), lang.lower()
                coop_merch_obj = None
                if type == "all":
                    coop_merch_obj = MerchantInfoTable.objects.filter(loc_code=loc_code)
                else:
                    coop_merch_obj = MerchantInfoTable.objects.filter(loc_code=loc_code, type_en=type) \
                        if lang == "en" else \
                        MerchantInfoTable.objects.filter(loc_code=loc_code, type_zh=type)

                if coop_merch_obj.exists():
                    coop_merchs = coop_merch_obj.values()
                    temp = []
                    for i, coop_item in enumerate(coop_merchs):
                        if len(temp) > pageSize:
                            res.append(temp)
                            temp = []
                        temp.append(filter_lang(coop_item, lang))
                    if len(temp) > 0:
                        res.append(temp)
                    cache_size = len(res)
                    store_in_redis(key, str(res), timeout)
                    page_res = res[pageId] if pageId < cache_size else []
                return page_res, cache_size
        except Exception as e:
            raise Exception("【getClubCoopListByType】获取特定合作商家List失败: %s" % e)


class getOneCoopDetail(View):
    def execute(self, coop_id, lang="zh"):
        """
        获取单个合作商家详情:
        s1: 根据 coopid,lang 查询MerchantInfoTable

        :param coop_id:
        :param lang:
        :return:
        """
        """
        获取单个合作商家详情: 根据[coopid]查询MerchantInfoTable，然后根据[coopid]查询ActivityInfoTable
        :param coop_id:
        :return:
            {"coop_id", "name", "detail", "pic", "loc_code", "email", "wechatid",
                EventList: [{"act_id", "type", "title", "act_time", "pic", "loc_code", "tag", "attendence"}]}
        """
        try:
            coop_merch_obj = MerchantInfoTable.objects.filter(coop_id=coop_id)
            if coop_merch_obj.exists():
                coop_merchs = coop_merch_obj.values()
                for coop_item in coop_merchs:
                    coop_id = coop_item.get("coop_id", None)
                    coop_acts_obj = ActivityInfoTable.objects.filter(coop_id=coop_id)
                    events = []
                    if coop_acts_obj.exists():
                        for act_det in coop_acts_obj.values():
                            act_id = act_det.get("act_id", None)
                            act_det.update({"attendence": get_attendence(act_id)})
                            events.append(act_det)
                    coop_item = filter_lang(coop_item, lang)
                    coop_item.update({"EventList": events})
                    return coop_item
        except Exception as e:
            raise Exception("【getOneCoopDetail】获取合作商家失败: %s" % e)


## TODO：会员板块

class getClubInfo(View):
    def execute(self, type):
        """获取商会信息"""


class getMembershipInfo(View):
    def execute(self, type):
        """获取会员制度信息"""


class getClubContactInfo(View):
    def execute(self, type):
        """获取商会联系方式"""


class getMemberInfo(View):
    def execute(self, uid):
        """获取会员详细信息"""
        res = {}
        try:
            check_obj = UserInforTable.objects.filter(uid=uid)
            rating_obj = UserRatingTable.objects.filter(uid=uid)
            if not check_obj.exists():
                # res = UserInforTable.objects.values()
                res = {}
            res = check_obj.values('uid', 'name', 'pic', 'profile', 'location', 'register_time').first()
            res_rating = rating_obj.values('tech_one', 'tech_two', 'tech_three',
                                           'tech_four', 'tech_five',
                                           'person_one', 'person_two', 'person_three',
                                           'person_four', 'person_five').first()
            print("res_rating",res_rating)
            print("res",res)
            res.update(res_rating)
            print("res after union:", res)
            return res
        except Exception as e:
            raise Exception(e)


class registerMembership(View):
    def execute(self, uid, name, profile, location, register_time):
        """
        注册会员:
        :param uid:
        :param name:
        :param level:
        :param wechat:
        :param profile:
        :param email:
        :param location:
        :param register_time:
        :return: 0: 注册失败，1: 注册成功, 2: 用户已存在
        """
        try:
            check_obj = UserInforTable.objects.filter(uid=uid)
            if not check_obj.exists():
                UserInforTable.objects.create(uid=uid,
                                              name=name,
                                              profile=profile,
                                              pic="default.jpg",
                                              location=location,                    
                                              register_time=register_time)
                UserRatingTable.objects.create(uid=uid,
                                                tech_one= "0.0",
                                                tech_two = "0.0",
                                                tech_three = "0.0",
                                                tech_four = "0.0",
                                                tech_five = "0.0",
                                                person_one = "0.0",
                                                person_two = "0.0",
                                                person_three = "0.0",
                                                person_four = "0.0",
                                                person_five = "0.0")
                return 1, "OK"
            else:
                return 2, "Existed..."
        except Exception as e:
            return 0, e


class modifyMembership(View):
    def execute(self, uid, name=None, pic=None, profile=None, location=None):
        """
        会员信息修改
        :param uid:
        :param name:
        :param wechat:
        :param pic:
        :param profile:
        :param email:
        :param phone_no:
        :param location:
        :return:
        """
        try:
            check_obj = UserInforTable.objects.filter(uid=uid)
            if not check_obj.exists():
                msg = "异常用户，用户数据库无此人信息..."
                return 0, msg
            if name:
                UserInforTable.objects.filter(uid=uid).update(name=name)
            elif pic:
                UserInforTable.objects.filter(uid=uid).update(pic=pic)
            elif profile:
                UserInforTable.objects.filter(uid=uid).update(profile=profile)
            elif location:
                UserInforTable.objects.filter(uid=uid).update(location=location)
            return 1, "OK"
        except Exception as e:
            return 0, e

class createInvitation(View):
    def execute(self,inviterId, inviteeId, matchTime, msg, place):
        """
        创建约球邀请:
        :param uid:
        :param name:
        :param level:
        :param wechat:
        :param profile:
        :param email:
        :param location:
        :param register_time:
        :return: 0: 注册失败，1: 注册成功, 2: 用户已存在
        """
        try:
            check_obj = UserInvTable.objects.filter(inviterId=inviterId, inviteeId=inviteeId, matchTime=matchTime)
            if not check_obj.exists():
                createTime = str(int(time.time() * 1000))
                UserInvTable.objects.create(inviterId=inviterId,
                                            inviteeId=inviteeId,
                                            matchTime=matchTime,
                                            createTime=createTime,
                                            msg=msg,                    
                                            place=place,
                                            status="0")
               
                return 1, "invitation created"
            else:
                return 2, "invitation Existed"
        except Exception as e:
            return 0, e


class getInvitationByStatus(View):
    @classmethod
    def execute(cls, inviterId=None, inviteeId=None, status=None, beforeAt=None):
        """
        根据状态获取邀请列表
        :param inviterId: 邀请者ID，如果提供则过滤发出的邀请
        :param inviteeId: 被邀请者ID，如果提供则过滤收到的邀请
        :param status: 邀请状态：0-待处理，1-已接受，2-已拒绝，3-已过期
        :param beforeAt: 过滤条件，只返回matchTime大于等于beforeAt的记录
        :return: 邀请列表
        """
        res = []
        try:
            # 构建过滤条件
            filter_kwargs = {}
            if inviterId:
                filter_kwargs['inviterId'] = inviterId
            if inviteeId:
                filter_kwargs['inviteeId'] = inviteeId
            if status is not None:
                filter_kwargs['status'] = status
            if beforeAt is not None:
                filter_kwargs['matchTime__gte'] = beforeAt
                
            # 查询邀请
            invitations = UserInvTable.objects.filter(**filter_kwargs)
            if not invitations.exists():
                return res
                
            # 获取邀请列表
            invitations_data = invitations.values(
                'inv_id', 'inviterId', 'inviteeId', 'matchTime', 
                'createTime', 'msg', 'place', 'status'
            )

            from util.external_api import retrieve_from_redis
            for inv in invitations_data:
                # 获取邀请者信息
                inviter = UserInforTable.objects.filter(uid=inv['inviterId']).first()
                # 获取被邀请者信息
                invitee = UserInforTable.objects.filter(uid=inv['inviteeId']).first()
                
                if inviter:
                    inv['inviterName'] = inviter.name
                    inv['inviterPic'] = inviter.pic
                
                if invitee:
                    inv['inviteeName'] = invitee.name
                    inv['inviteePic'] = invitee.pic
                
                # rated30 字段判断
                # 只有已接受的邀请（status==1）才允许评分
                if str(inv['status']) == '1':
                    # 评分key: rating_邀请者_被邀请者
                    rating_key = f"rating_{inv['inviterId']}_{inv['inviteeId']}"
                    rated_flag = retrieve_from_redis(rating_key)
                    inv['rated30'] = 0 if rated_flag else 1
                else:
                    inv['rated30'] = 0
                
                res.append(inv)
                
            return res
        except Exception as e:
            _logger.error(f"获取邀请列表异常: {str(e)}")
            raise Exception(f"获取邀请列表失败: {str(e)}")


class updateInvitation(View):
    @classmethod
    def execute(cls, inv_id, inviterId, inviteeId, action, access_token):
        """
        更新邀请状态
        :param inv_id: 邀请ID
        :param inviterId: 邀请者ID
        :param inviteeId: 被邀请者ID  
        :param action: 操作类型 accept-接受, reject-拒绝
        :param access_token: 访问令牌
        :return: 操作结果
        """
        try:
            # 验证邀请是否存在
            invitation = UserInvTable.objects.filter(inv_id=inv_id).first()
            if not invitation:
                return 0, "邀请不存在"
            
            # 验证邀请者和被邀请者是否匹配
            if invitation.inviterId != inviterId or invitation.inviteeId != inviteeId:
                return 0, "邀请信息不匹配"
            
            if action == "accept":
                # 接受邀请：将状态改为1
                UserInvTable.objects.filter(inv_id=inv_id).update(status="1")
                
                # 检查好友关系是否已存在
                friend_exists = UserFriendTable.objects.filter(
                    userId=inviterId, 
                    friendId=inviteeId
                ).exists()
                
                if not friend_exists:
                    # 创建双向好友关系
                    create_time = str(int(time.time() * 1000))  # 修改为毫秒级时间戳
                    
                    # 创建 inviterId -> inviteeId 的好友关系
                    UserFriendTable.objects.create(
                        userId=inviterId,
                        friendId=inviteeId,
                        createTime=create_time,
                        other=""
                    )
                    
                    # 创建 inviteeId -> inviterId 的好友关系
                    UserFriendTable.objects.create(
                        userId=inviteeId,
                        friendId=inviterId,
                        createTime=create_time,
                        other=""
                    )
                
                return 1, "邀请已接受，好友关系已建立"
                
            elif action == "reject":
                # 拒绝邀请：将状态改为2
                UserInvTable.objects.filter(inv_id=inv_id).update(status="2")
                return 1, "邀请已拒绝"
            
            else:
                return 0, "无效的操作类型"
                
        except Exception as e:
            _logger.error(f"更新邀请状态异常: {str(e)}")
            return 0, f"更新邀请状态失败: {str(e)}"


class getFriends(View):
    @classmethod
    def execute(cls, userId, friendshipCreateTime=None):
        """
        获取用户好友列表
        :param userId: 用户ID
        :param friendshipCreateTime: 好友关系创建时间过滤条件，只返回大于等于此时间的好友
        :return: 好友信息列表
        """
        res = []
        try:
            # 构建查询条件
            filter_kwargs = {'userId': userId}
            if friendshipCreateTime is not None:
                filter_kwargs['createTime__gte'] = friendshipCreateTime
            
            # 查询用户好友表，获取所有该用户的好友ID
            friend_relationships = UserFriendTable.objects.filter(**filter_kwargs)
            
            if not friend_relationships.exists():
                return res
            
            # 获取所有好友ID
            friend_ids = friend_relationships.values_list('friendId', flat=True)
            
            # 根据好友ID查询用户信息表，获取好友详细信息
            friends_info = UserInforTable.objects.filter(uid__in=friend_ids)
            
            if friends_info.exists():
                # 获取好友信息并添加好友关系创建时间
                for friend in friends_info.values('uid', 'name', 'pic', 'profile', 'location', 'register_time'):
                    # 获取该好友关系的创建时间
                    friend_relation = friend_relationships.filter(friendId=friend['uid']).first()
                    if friend_relation:
                        friend['friendshipCreateTime'] = friend_relation.createTime
                        friend['other'] = friend_relation.other or ""
                    
                    res.append(friend)
            
            return res
            
        except Exception as e:
            _logger.error(f"获取好友列表异常: {str(e)}")
            raise Exception(f"【getFriends】获取好友列表失败: {str(e)}")


class RateCompetition(View):
    def execute(self, rater_uid, rated_uid, ratings):
        """
        用户评分接口 - 每对用户一个月只能互评一次
        :param rater_uid: 评分者用户ID
        :param rated_uid: 被评分者用户ID  
        :param ratings: 评分数据字典，包含tech_one到tech_five和person_one到person_five
        :return: 成功返回1，失败返回0和错误信息
        """
        try:
            # 只检查 Redis，简化逻辑
            rating_cache_key = f"rating_{rater_uid}_{rated_uid}"
            last_rating_time = retrieve_from_redis(rating_cache_key)
            if last_rating_time:
                return 0, "该用户对在30天内已经互评过，无法重复评分"

            current_time_str = datetime.now().isoformat()
            with transaction.atomic():
                # 1. 更新UserRatingShortTable（队列方式，保持最新30条记录）
                self._update_short_table(rated_uid, ratings, current_time_str)
                # 2. 更新UserRatingLongTable  
                self._update_long_table(rated_uid)
                # 3. 更新UserRatingTable（综合评分）
                self._update_main_rating_table(rated_uid)
                # 4. 记录本次评分，防止重复评分
                store_in_redis(rating_cache_key, current_time_str, 30 * 24 * 3600)  # 30天过期
            return 1, "评分成功"
        except Exception as e:
            _logger.error(f"【RateCompetition】评分异常: {e}")
            return 0, f"评分失败: {str(e)}"
    
    def _update_short_table(self, uid, ratings, rating_time):
        """更新短周期评分表（队列方式，保持最新30条记录）"""
        # 获取用户当前所有短周期评分记录，按时间排序
        short_ratings = list(UserRatingShortTable.objects.filter(
            uid=uid
        ).order_by('rating_time'))
        
        # 如果记录数已达到30条，移除最旧的记录并聚合到长周期表
        if len(short_ratings) >= 30:
            oldest_rating = short_ratings[0]
            self._aggregate_to_long_table(uid, oldest_rating)
            oldest_rating.delete()
        
        # 添加新的评分记录
        UserRatingShortTable.objects.create(
            uid=uid,
            tech_one=str(ratings.get('tech_one', 0)),
            tech_two=str(ratings.get('tech_two', 0)),
            tech_three=str(ratings.get('tech_three', 0)),
            tech_four=str(ratings.get('tech_four', 0)),
            tech_five=str(ratings.get('tech_five', 0)),
            person_one=str(ratings.get('person_one', 0)),
            person_two=str(ratings.get('person_two', 0)),
            person_three=str(ratings.get('person_three', 0)),
            person_four=str(ratings.get('person_four', 0)),
            person_five=str(ratings.get('person_five', 0)),
            rating_time=rating_time
        )
    
    def _aggregate_to_long_table(self, uid, old_rating):
        """将最旧的评分聚合到长周期表"""
        long_rating, created = UserRatingLongTable.objects.get_or_create(
            uid=uid,
            defaults={
                'tech_one': '0', 'tech_two': '0', 'tech_three': '0', 
                'tech_four': '0', 'tech_five': '0',
                'person_one': '0', 'person_two': '0', 'person_three': '0',
                'person_four': '0', 'person_five': '0', 'n': '0'
            }
        )
        
        # 获取当前计数
        current_n = int(long_rating.n) if long_rating.n else 0
        new_n = current_n + 1
        
        # 计算新的平均值
        rating_fields = ['tech_one', 'tech_two', 'tech_three', 'tech_four', 'tech_five',
                        'person_one', 'person_two', 'person_three', 'person_four', 'person_five']
        
        for field in rating_fields:
            current_avg = float(getattr(long_rating, field)) if getattr(long_rating, field) else 0
            old_value = float(getattr(old_rating, field)) if getattr(old_rating, field) else 0
            
            # 计算新的平均值: (当前平均值 * 当前计数 + 新值) / (计数 + 1)
            new_avg = (current_avg * current_n + old_value) / new_n
            setattr(long_rating, field, str(round(new_avg, 2)))
        
        long_rating.n = str(new_n)
        long_rating.save()
    
    def _update_long_table(self, uid):
        """确保长周期表存在记录"""
        UserRatingLongTable.objects.get_or_create(
            uid=uid,
            defaults={
                'tech_one': '0', 'tech_two': '0', 'tech_three': '0', 
                'tech_four': '0', 'tech_five': '0',
                'person_one': '0', 'person_two': '0', 'person_three': '0',
                'person_four': '0', 'person_five': '0', 'n': '0'
            }
        )
    
    def _update_main_rating_table(self, uid):
        """更新主评分表：0.6*短周期 + 0.4*长周期"""
        # 获取短周期平均分
        short_ratings = UserRatingShortTable.objects.filter(uid=uid)
        short_avg = self._calculate_average_ratings(short_ratings, 'short')
        
        # 获取长周期平均分
        try:
            long_rating = UserRatingLongTable.objects.get(uid=uid)
            long_avg = {
                'tech_one': float(long_rating.tech_one) if long_rating.tech_one else 0,
                'tech_two': float(long_rating.tech_two) if long_rating.tech_two else 0,
                'tech_three': float(long_rating.tech_three) if long_rating.tech_three else 0,
                'tech_four': float(long_rating.tech_four) if long_rating.tech_four else 0,
                'tech_five': float(long_rating.tech_five) if long_rating.tech_five else 0,
                'person_one': float(long_rating.person_one) if long_rating.person_one else 0,
                'person_two': float(long_rating.person_two) if long_rating.person_two else 0,
                'person_three': float(long_rating.person_three) if long_rating.person_three else 0,
                'person_four': float(long_rating.person_four) if long_rating.person_four else 0,
                'person_five': float(long_rating.person_five) if long_rating.person_five else 0,
            }
        except UserRatingLongTable.DoesNotExist:
            long_avg = {field: 0 for field in ['tech_one', 'tech_two', 'tech_three', 'tech_four', 'tech_five',
                                              'person_one', 'person_two', 'person_three', 'person_four', 'person_five']}
        
        # 计算综合评分：0.6*短周期 + 0.4*长周期
        final_ratings = {}
        for field in ['tech_one', 'tech_two', 'tech_three', 'tech_four', 'tech_five',
                     'person_one', 'person_two', 'person_three', 'person_four', 'person_five']:
            final_score = 0.6 * short_avg[field] + 0.4 * long_avg[field]
            final_ratings[field] = str(round(final_score, 2))
        
        # 更新或创建主评分表记录
        UserRatingTable.objects.update_or_create(
            uid=uid,
            defaults=final_ratings
        )
    
    def _calculate_average_ratings(self, ratings_queryset, table_type='short'):
        """计算评分平均值"""
        if not ratings_queryset.exists():
            return {field: 0 for field in ['tech_one', 'tech_two', 'tech_three', 'tech_four', 'tech_five',
                                          'person_one', 'person_two', 'person_three', 'person_four', 'person_five']}
        
        ratings_list = list(ratings_queryset.values())
        count = len(ratings_list)
        
        averages = {}
        for field in ['tech_one', 'tech_two', 'tech_three', 'tech_four', 'tech_five',
                     'person_one', 'person_two', 'person_three', 'person_four', 'person_five']:
            total = sum(float(rating[field]) if rating[field] else 0 for rating in ratings_list)
            averages[field] = total / count if count > 0 else 0
        
        return averages
