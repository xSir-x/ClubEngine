import random

from django.shortcuts import render
from django.views import View
from dbModel.models import ActivityInfoTable, MerchantInfoTable, UserInforTable, MerchantMaskTable, ActsMarkTable, \
    UserOrderTable
from django.utils import timezone
from datetime import datetime
from django.core.cache import cache


## 活动板块
class addFavActivity(View):
    @classmethod
    def execute(cls, need_fav, act_id, uid):
        """
        收藏活动操作:
        :param need_fav: bool
        :param act_id:
        :param uid:
        :return:
        """
        message = "ok!"
        try:
            fav_act_obj = ActsMarkTable.objects.filter(uid=uid, act_id=act_id)
            if fav_act_obj.exists():
                is_mark = fav_act_obj.values("is_mark")[0]["is_mark"]
                if need_fav:
                    if is_mark != 1:
                        ActsMarkTable.objects.filter(uid=uid, act_id=act_id).update(is_mark=1, mask_time=timezone.now())
                else:
                    if is_mark != 0:
                        ActsMarkTable.objects.filter(uid=uid, act_id=act_id).update(is_mark=0, mask_time=timezone.now())
            else:
                if need_fav:
                    ActsMarkTable.objects.create(uid=uid, act_id=act_id, is_mark=1, mask_time=timezone.now())
                else:
                    ActsMarkTable.objects.filter(uid=uid, act_id=act_id).update(is_mark=0, mask_time=timezone.now())
            return 1, message
        except IOError:
            message = "【addFavActivity】数据库【ActsMarkTable】操作收藏活动失败..."
            return 0, message


class getAllType(View):
    @classmethod
    def execute(cls, loc_code):
        """
        获取所有活动类型: 根据loc_code 查询该地区所有活动的type
        :param loc_code:
        :return: [{"act_id": act_id, "type": type}, ...]
        """
        res = {}
        try:
            get_acts_obj = ActivityInfoTable.objects.filter(loc_code=loc_code)
            if get_acts_obj.exists():
                res = get_acts_obj.values("type")
            return res
        except IOError:
            raise Exception("【getAllType】查询数据库【ActivityInfoTable】[param: %s]异常..." % loc_code)


def filter_lang(item_info, lang):
    """
    根据语言进行过滤
    :param item_info:
    :param lang:
    :return:
    """
    if lang:
        if lang == "zh":
            if "detail_en" in item_info:
                item_info.pop("detail_en")
            if "title_en" in item_info:
                item_info.pop("title_en")
        elif lang == "en":
            if "detail_en" in item_info:
                item_info.pop("detail_zh")
            if "title_en" in item_info:
                item_info.pop("title_zh")
    return item_info


def get_activity_dets(act_det, lang):
    """
    多表查询获取单个活动的所有信息: 包含活动信息表的所有信息、is_mark(活动是否被收藏)、attendence(被哪些收藏，收藏者的pic)
    :param act_det: 字典格式
    :param lang:
    :return:
    """
    act_det = filter_lang(act_det, lang)

    # 查询表【ActsMarkTable】获取is_mark字段
    act_id = act_det.get("act_id", None)
    assert act_id != None, Exception("缺少act_id字段...")
    actmark_obj = ActsMarkTable.objects.filter(act_id=act_id)
    is_mark = actmark_obj.values("is_mark")[0]["is_mark"] if actmark_obj.exists() else 0
    act_det.update({"is_mark": is_mark})

    # 查询订单表【UserOrderTable】获取"pic"字段追加到 attendence
    act_det.update({"attendence": get_attendence(act_id)})
    return act_det


def get_attendence(act_id):
    """获取attendence"""
    userod_obj = UserOrderTable.objects.filter(act_id=act_id, order_status=2)
    attendence = []
    if userod_obj.exists():
        att_uids = userod_obj.values("uid")
        for _item in att_uids:
            uid = _item.get("uid", None)
            assert uid != None, Exception("uid 字段在数据库不存在，请检查...")
            _pic = UserInforTable.objects.filter(uid=uid, order_status=2).values("pic")
            attendence.append(_pic)
    return attendence


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
        res = []

        key = type + "#" + loc_code + "#" + lang
        his_cache = cache.get(key, None)
        if his_cache:
            size = len(his_cache)
            assert pageId > size, Exception("pageId 大于查询到的page数: %s..." % len(res))
            return his_cache[pageId], size
        else:
            try:
                actinfo_obj = ActivityInfoTable.objects.filter(loc_code=loc_code, type=type)
                if actinfo_obj.exists():
                    type_acts = actinfo_obj.values()
                    temp = []
                    for i, act_item in enumerate(type_acts):
                        if len(temp) > pageSize:
                            res.append(temp)
                        act_item = get_activity_dets(act_item, lang)
                        temp.append(act_item)
                    if len(temp) > 0:
                        res.append(temp)
                    size = len(res)
                    assert pageId > size, Exception("pageId 大于查询到的page数: %s..." % len(res))
                    cache.set(key, res, timeout)
                    return res, size
            except IOError:
                raise Exception("【getActivitiesByType】查询数据库[ActivityInfoTable]异常...")


class getRecommandActivities(View):
    @classmethod
    def execute(cls, loc_code, lang=None):
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
        except IOError:
            raise Exception("【getRecommandActivities】查询数据库【ActivityInfoTable】[%s]异常..." % loc_code)


class getSingleActivityDetail(View):
    def execute(self, act_id, type, lang=None):
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
            act_obj = ActivityInfoTable.objects.filter(act_id=act_id, type=type)
            if act_obj.exists():
                act_info = act_obj.values()[0]
                act_det = get_activity_dets(act_info, lang)
            return act_det
        except IOError:
            raise Exception("【getSingleActivityDetail】查询数据库【ActivityInfoTable or UserOrderTable】异常...")


class getMyActivitiesBytype(View):
    def execute(self, uid, type, lang):
        """
        获取我的活动列表: 根据uid&type两个字段查询ActivityInfoTable某个的活动
        :param uid:
        :param type: ongoing/past/new/all
        :param lang: zh or en
        :return: List[dict{},]
        """
        res = []
        try:
            assert type in ["ongoing", "past", "new", "all"], Exception("type字段取值范围存在问题..")
            acts_obj = UserOrderTable.objects.filter(uid=uid)
            if acts_obj.exists():
                my_acts = acts_obj.values("act_id", "order_id", "order_status")
                for item in my_acts:
                    item_obj = ActivityInfoTable.objects.filter(act_id=item.get("act_id", None), type=type) \
                        if type.upper() != "ALL" else \
                        ActivityInfoTable.objects.filter(act_id=item.get("act_id", None))
                    assert item.get("act_id", None) != None, Exception("act_id 字段在数据库不存在，请检查...")
                    if not item_obj.exists():
                        continue
                    f_items = item_obj.values()
                    for _item_info in f_items:
                        item_info = filter_lang(_item_info, lang)
                        item_info.update(item)
                        res.append(item_info)
            return res
        except IOError:
            raise Exception("【getMyActivitiesBytype】查询数据库【UserOrderTable】异常...")


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
        except IOError:
            raise Exception("【getMySingleActivity】查询数据库【UserOrderTable】异常...")


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
            fav_act_obj = MerchantMaskTable.objects.filter(uid=uid, coop_id=coop_id)
            if fav_act_obj.exists():
                is_mark = fav_act_obj.values("is_mark")[0]["is_mark"]
                if need_fav:
                    if is_mark != 1:
                        MerchantMaskTable.objects.filter(uid=uid, coop_id=coop_id).update(is_mark=1,
                                                                                          mask_time=timezone.now())
                else:
                    if is_mark != 0:
                        MerchantMaskTable.objects.filter(uid=uid, coop_id=coop_id).update(is_mark=0,
                                                                                          mask_time=timezone.now())
            else:
                if need_fav:
                    MerchantMaskTable.objects.create(uid=uid, coop_id=coop_id, is_mark=1, mask_time=timezone.now())
                else:
                    MerchantMaskTable.objects.filter(uid=uid, coop_id=coop_id).update(is_mark=0,
                                                                                      mask_time=timezone.now())
            return 1, message
        except IOError:
            print("【addCoopFav】收藏商家异常...")
            return 0, message


class getClubCoopListType(View):
    def execute(self, loc_code):
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
                merch_infos = merch_obj.values("type")
                for item in merch_infos:
                    res.append(item)
            return res
        except IOError:
            raise Exception("【getClubCoopListType】获取合作商家失败...")


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
        res = []
        key = "CLUBCOOP#" + type + "#" + loc_code + "#" + lang
        his_cache = cache.get(key, [])
        cache_size = len(his_cache)
        if his_cache:
            assert pageId > cache_size, Exception("pageId 大于查询到的page数: %s..." % len(res))
            return his_cache[pageId], cache_size
        else:
            try:
                coop_merch_obj = MerchantInfoTable.objects.get(loc_code=loc_code, type=type)
                if coop_merch_obj.exists():
                    coop_merchs = coop_merch_obj.values()
                    temp = []
                    for i, coop_item in enumerate(coop_merchs):
                        if len(temp) > pageSize:
                            res.append(temp)
                        coop_item = filter_lang(coop_item, lang)
                        temp.append(coop_item)
                    if len(temp) > 0:
                        res.append(temp)
                    cache_size = len(res)
                    assert pageId > cache_size, Exception("pageId 大于查询到的page数: %s..." % len(res))
                    cache.set(key, res, timeout)
                return res, cache_size
            except IOError:
                raise Exception("【getClubCoopListByType】获取特定合作商家List失败...")


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
                    assert coop_id != None, Exception("coop_id 字段在数据库不存在，请检查...")
                    coop_acts_obj = ActivityInfoTable.objects.filter(coop_id=coop_id)
                    events = []
                    if coop_acts_obj.exists():
                        for act_det in coop_acts_obj.values():
                            act_id = act_det.get("act_id", None)
                            assert act_id != None, Exception("act_id 字段在数据库不存在，请检查...")
                            act_det.update({"attendence": get_attendence(act_id)})
                            events.append(act_det)
                    coop_item = filter_lang(coop_item, lang)
                    coop_item.update({"EventList": events})
                    return coop_item
        except IOError:
            raise Exception("【getOneCoopDetail】获取合作商家失败...")


## 会员板块
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
                res = UserInforTable.objects.values()
            return res
        except Exception as e:
            raise Exception(e)


class upgradeMembership(View):
    def execute(self, uid, name, level, wechat, profile, email, phone_no, location, register_time):
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
        msg = ""
        try:
            check_obj = UserInforTable.objects.filter(uid=uid)
            if not check_obj.exists():
                UserInforTable.objects.update(uid=uid,
                                              name=name,
                                              level=level,
                                              wechat=wechat,
                                              profile=profile,
                                              email=email,
                                              phone_no=phone_no,
                                              location=location,
                                              register_time=register_time)
                return 1, "OK"
            else:
                return 2, "Existed..."
        except Exception as e:
            return 0, e
