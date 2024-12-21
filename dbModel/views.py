import random

from django.shortcuts import render
from django.views import View
from dbModel.models import ActivityInfoTable, MerchantInfoTable, UserInforTable, MerchantMaskTable, ActsMarkTable, \
    UserOrderTable
from django.utils import timezone


## 活动板块
class addFavActivity(View):
    def execuate(self, act_id, uid):
        """
        收藏活动操作：Roc update： 根据uid + act_id 查询用户活动收藏表，有的话把 is_mark置1， 无的话，新增一条记录并且把is_mark字段置1
        :param act_id:
        :param uid:
        :return:
        """
        state = 0  # 0: 失败，1: 成功
        try:
            fav_act_obj = ActsMarkTable.objects.get(uid=uid, act_id=act_id)
            if fav_act_obj.exists():
                ActsMarkTable.objects.filter(uid=uid, act_id=act_id).update(is_mark=1)
            else:
                ActsMarkTable.objects.create(uid=uid, act_id=act_id, is_mark=1, update_time=timezone.now)
            return 1
        except IOError:
            print("【addFavActivity】数据库【ActsMarkTable】操作收藏活动失败...")
            return 0


class getAllType(View):
    def execuate(self, loc_code):
        """
        获取所有活动类型
        roc update：根据loc_code 查询该地区所有活动的type， 返回类型为 list of string （i.e [sport，music，resturant,...]）
        :param loc_code:
        :return:
            [{"act_id": act_id, "type": type},
            ...]
        """
        res = {}
        try:
            get_acts_obj = ActivityInfoTable.objects.filter(loc_code=loc_code)
            if get_acts_obj.exists():
                res = get_acts_obj.values("act_id", "type")
            return res
        except IOError:
            raise Exception("【getAllType】查询数据库【ActivityInfoTable】[param: %s]异常..." % loc_code)


class getActivitiesByType(View):
    def execuate(self, type, loc_code, pageId=0, pageSize=7):
        """
        获取所有活动列表: 直接读取表ActivityInfoTable
        ①、page查询需要进行redis缓存，redis设置过期时间；②、input para异常处理
        :param type:
        :param loc_code:
        :param pageId:
        :param pageSize:
        :return:
            [{}, {}]
        """

        res = []
        try:
            type_acts_obj = ActivityInfoTable.objects.filter(loc_code=loc_code, type=type)
            if type_acts_obj.exists():
                type_acts = type_acts_obj\
                    .values("act_id", "type", "title", "pic", "loc_code", "tag", "is_mark",
                                                "act_time", "attendence")\
                    .order_by('act_time')
                res = [type_acts[i:i + pageSize] for i in range(0, type_acts, pageSize)]
                return res
        except IOError:
            raise Exception("【getActivitiesByType】查询数据库[ActivityInfoTable]异常...")


class getRecommandActivities(View):
    def execuate(self, loc_code):
        """
        获取活动推荐列表:
        roc update: 1。查询ActivityInfoTable，返回该地区，is_recommand为1的act_id对应的活动信息
        2。attnedence通过act_id查询UserOrderTable中order_status=2(支付成功的)返回list of uid,
        :param loc_code:
        :return:
        [{act_id, type, title, time, pic, loc_code, tag, attendence, is_mark}]
        """
        res = []
        try:
            recomm_act_obj = ActivityInfoTable.objects.filter(loc_code=loc_code, is_recommend=1)
            if recomm_act_obj.exists():
                recomm_acts = recomm_act_obj\
                    .values("act_id", "type", "title", "pic", "loc_code", "tag", "is_mark",
                                                "act_time")
                for reco_act in recomm_acts:
                    act_id = reco_act.get("act_id", None)
                    attendence = UserOrderTable.objects.filter(act_id=act_id, paymentid=2).values().count()
                    reco_act.update({"attendence": attendence})
                    res.append(reco_act)
            return res
        except IOError:
            raise Exception("【getRecommandActivities】查询数据库【ActivityInfoTable】[%s]异常..." % loc_code)


class getSingleActivityDetail(View):
    def execuate(self, act_id, type):
        """
        获取单个活动细节:
        roc update: 1。查询ActivityInfoTable，目标act_id的活动信息
        2。attnedence通过act_id查询UserOrderTable中order_status=2(支付成功的)返回list of uid,
        :param act_id:
        :param type:
        :return:
            {act_id, title, time, detail, price, loc_code, tag, pic, attendence, is_mark}
        """
        res = []
        try:
            sing_act_obj = ActivityInfoTable.objects.filter(act_id=act_id, type=type)
            if sing_act_obj.exists():
                single_act = sing_act_obj\
                    .values("act_id", "title", "act_time", "detail", "price", "loc_code", "tag",
                                               "pic", "is_mark")
                attendence = UserOrderTable.objects.filter(act_id=act_id, paymentid=2).values().count()
                single_act.update({"attendence": attendence})
            return res
        except IOError:
            raise Exception("【getSingleActivityDetail】查询数据库【ActivityInfoTable or UserOrderTable】异常...")


class getMyActivitiesType(View):
    def execuate(self, uid, loc_code):
        """
        获取我的活动类型:
        roc update：根据uid查询用户的所有订单order_status并返回 list of order_status

        :param uid:
        :param loc_code:
        :return:
            [{"order_id": order_id,
            "order_status": order_status},
            ...]
        """
        res = []
        try:
            my_all_acts_obj = UserOrderTable.objects.filter(uid=uid, loc_code=loc_code)
            if my_all_acts_obj.exists():
                res = my_all_acts_obj.values("order_id", "order_status")
            return res
        except IOError:
            raise Exception("【getMyActivitiesType】查询数据库【UserOrderTable】异常...")


class getMyActivitiesBytype(View):
    def execuate(self, uid, type):
        """
        获取我的活动列表: UserOrderTable
        :param uid:
        :param type: ongoing/past/new/all
        :return:
            [{"order_id": order_id,
            "act_id": act_id,
            "act_time": act_time,
            "pic": pic,
            "price": price,
            "order_status": order_status
            "title": title},
            ...]
        """
        res = []
        try:
            assert type in ["ongoing", "past", "new", "all"], print("type字段取值范围存在问题..")
            my_acts_obj = UserOrderTable.objects.filter(uid=uid)
            if my_acts_obj.exists():
                my_acts = my_acts_obj.values("act_id", "order_id", "order_status")
                for item in my_acts:
                    item_infos = ActivityInfoTable.objects. \
                        filter(act_id=item.get("act_id"), type=type). \
                        values("act_time", "pic", "price", "title") if type != "all " else \
                        ActivityInfoTable.objects\
                            .filter(act_id=item.get("act_id"))\
                            .values("act_time", "pic", "price", "title")
                    res.append(item.update({item_infos}))
            return res
        except IOError:
            raise Exception("【getMyActivitiesBytype】查询数据库【UserOrderTable】异常...")


class getMySingleActivity(View):
    def execuate(self, order_id, uid):
        """
        获取我的单个活动列表: 查询UserOrderTable过滤即可, 然后根据act_id查询ActivityInfoTable
        :param order_id:
        :param uid:
            {"order_id": order_id, "title": title, "time": time, "detail": detail, "price": price,
            "loc_code": loc_code, "pic": pic,
            "order_status": order_status, "paymentid": paymentid, "pay_time": pay_time}
        """
        res = []
        try:
            my_act_obj = UserOrderTable.objects.filter(uid=uid, order_id=order_id)
            if my_act_obj.exists():
                res = my_act_obj\
                    .values("order_id", "title", "time", "detail", "price", "loc_code", "pic",
                                        "order_status", "paymentid", "pay_time")\
                    .order_by("order_time")
            return res
        except IOError:
            raise Exception("【getMySingleActivity】查询数据库【UserOrderTable】异常...")


## 商家板块
class addCoopFav(View):
    def execuate(self, uid, coopid):
        """
        收藏商家:
        Roc update： 根据uid + coopid 查询用户商户收藏表，有的话把is_mark置1， 无的话，新增一条记录并且把is_mark字段置1
        :param uid:
        :param coopid:
        :return:
        """
        try:
            merch_mask_obj = MerchantMaskTable.objects.get(coopid=coopid, uid=uid)
            if merch_mask_obj.exists():
                ActsMarkTable.objects.filter(coopid=coopid, uid=uid).update(is_mark=1)
            else:
                ActsMarkTable.objects.create(coopid=coopid, uid=uid, is_mark=1, update_time=timezone.now)
            return 1
        except IOError:
            print("【addCoopFav】收藏商家失败...")
            return 0


class getClubCoopListType(View):
    def execuate(self, loc_code):
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
            merch_obj = MerchantInfoTable.objects.get(loc_code=loc_code)
            if merch_obj.exists():
                merch_infos = merch_obj.value("coopid", "type")
                res = merch_infos
            return res
        except IOError:
            raise Exception("【getClubCoopListType】获取合作商家失败...")


class getClubCoopListByType(View):
    def execuate(self, type, loc_code, uid, pageId=0, pageSize=7):
        """
        获取合作商家信息:
        Roc update: 1。根据uid查询缓存，如果缓存存在，根绝pageID return 对应的coop信息， 如果缓存不存在执行2
                    2。根据type+loc_code 查询coop的info， count总共N条数据，并且计算最大分页id（N/pageSize）， 缓存根据uid+pageid记录每一个页面信息， return 对pageid的coop的info
        :param type:
        :param loc_code:
        :param uid:
        :param pageId:
        :param pageSize:
        :return:
            [{"coopid": coopid, "name": name, "type": type, "pic": pic, "loc_code": loc_code},
            ...]
        """
        res = []
        try:
            coop_merch_obj = MerchantInfoTable.objects.get(loc_code=loc_code, type=type)
            if coop_merch_obj.exists():
                coop_merchs = coop_merch_obj.values("coopid", "name", "type", "pic", "loc_code").order_by('act_time')
                res = [coop_merchs[i:i + pageSize] for i in range(0, coop_merchs, pageSize)]
            return res
        except IOError:
            raise Exception("【getClubCoopListByType】获取合作商家失败...")


class getOneCoopDetail(View):
    def execuate(self, coopid):
        """
        获取单个合作商家详情: 根据[coopid]查询MerchantInfoTable，然后根据[coopid]查询ActivityInfoTable
        :param coopid:
        :return:
            {"coopid", "name", "detail", "pic", "loc_code", "email", "wechatid",
                EventList: [{"act_id", "type", "title", "act_time", "pic", "loc_code", "tag", "attendence"}]}
        """
        coop_merchs = []
        try:
            coop_merch_obj = MerchantInfoTable.objects.get(coopid=coopid)
            if coop_merch_obj.exists():
                coop_merchs = coop_merch_obj.\
                    values("coopid", "name", "detail", "pic", "loc_code", "email", "wechatid").\
                    order_by('update_time')
                acts = ActivityInfoTable.objects.\
                    filter("coopid").\
                    values("act_id", "type", "title", "act_time", "pic", "loc_code", "tag")
                events = []
                for act in acts:
                    act.update("attendence", random.randint(5, 10))
                    events.append(act)
                coop_merchs.update({"EventList": events})
            return coop_merchs
        except IOError:
            raise Exception("【getOneCoopDetail】获取合作商家失败...")

## 会员板块
class getClubInfo(View):
    def execuate(self, type):
        """获取商会信息"""


class getMembershipInfo(View):
    def execuate(self, type):
        """获取会员制度信息"""


class getClubContactInfo(View):
    def execuate(self, type):
        """获取商会联系方式"""


class getMemberInfo(View):
    def execuate(self, type):
        """获取会员详细信息"""


class upgradeMembership(View):
    def execuate(self, userid, wechat, email, phone, profile, location):
        """注册会员"""
