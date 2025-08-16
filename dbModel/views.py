from django.views import View
from dbModel.models import ActivityInfoTable, MerchantInfoTable, UserInforTable, MerchantMaskTable, ActsMarkTable, \
    UserOrderTable
# from django.utils import timezone
import time
from datetime import datetime
from django.core.cache import cache
from util.external_api import store_in_redis, retrieve_from_redis

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
        mask_time = str(int(time.time()))
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
            mask_time = str(int(time.time()))
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
            if not check_obj.exists():
                # res = UserInforTable.objects.values()
                res = {}
            res = check_obj.values('uid', 'name', 'pic', 'profile', 'location', 'register_time').first()
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
                UserInforTable.objects.update(uid=uid,
                                              name=name,
                                              profile=profile,                                              location=location,
                                              register_time=register_time)
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
