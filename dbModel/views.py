from django.shortcuts import render
from django.views import View
from dbModel.models import ActivityInfoTable, MerchantInfoTable, UserInforTable, UserFavTable, UserOrderTable


## 活动板块

class addFavActivity(View):
    def execuate(self, loc_code, act_id, uid):
        """
        收藏活动操作：根据loc_code, act_id 查询表ActivityInfoTable，按照uid新增UserOrderTable ??????(逻辑存疑)
                    Roc update： 根据uid + act_id 查询用户活动收藏表，有的话把 is_mark置1， 无的话，新增一条记录并且把is_mark字段置1
        :param loc_code:
        :param act_id:
        :param uid:
        :return:
        """
        state = 0  # 0: 失败，1: 成功
        UserOrderTable.objects.get()
        return state


class getAllType(View):
    def execuate(self, loc_code):
        """
        获取所有活动类型: 直接读取表ActivityInfoTable中的type??????(存疑: 返回的数据类型 需要确认)
        roc update：根据loc_code 查询该地区所有活动的type， 返回类型为 list of string （i.e [sport，music，resturant,...]）
        :param loc_code:
        :return:
            {act_id: type}
        """
        res = {}
        try:
            filtered_acts = ActivityInfoTable.objects.filter(loc_code=loc_code)

            for row in filtered_acts:
                res.update({})
        except:
            print("查询数据库ActivityInfoTable[%s]异常..." % loc_code)
        return res


class getActivitiesByType(View):
    def execuate(self, type, loc_code,  uid=None, pageId=0,pageSize=7):
        """
        获取所有活动列表: 直接读取表ActivityInfoTable

        ①、page查询需要进行缓存，设置过期时间；②、input para异常处理
        :param type:
        :param loc_code:
        :param pageId:
        :param uid:
        :param pageSize:
        :return:
            {[], []}
        """

        res = {}
        try:
            filtered_acts = ActivityInfoTable.objects.filter(loc_code=loc_code, type=type)

        except:
            print("查询数据库ActivityInfoTable[%s]异常..." % loc_code)
        return res


class getRecommandActivities(View):
    def execuate(self, loc_code, uid):
        """
        获取活动推荐列表: 操作ActivityInfoTable，按照input字段过滤  ??????(存疑： 读取ActivityInfoTable获取所有推荐活动， 然后根据活动ID 和 uid 查询UserOrderTable, 组合结果输出？)
        roc update: 1。查询ActivityInfoTable，返回该地区，is_recommand为1的act_id对应的活动信息 2。attnedence通过act_id查询UserOrderTable中order_status=2(支付成功的)返回list of uid,
        :param loc_code:
        :param uid:
        :return:
        {[act_id, type, title, time, pic, loc_code, tag, attendence, is_mark]}
        """


class getSingleActivityDetail(View):
    def execuate(self, uid, act_id, type):
        """
        获取单个活动细节: 操作ActivityInfoTable  ??????(存疑：查询用户已经下单的活动的细节？
        roc update: 1。查询ActivityInfoTable，目标act_id的活动信息 2。attnedence通过act_id查询UserOrderTable中order_status=2(支付成功的)返回list of uid,
        :param uid:
        :param act_id:
        :param type:
        :return:
            {act_id, title, time, detail, price, loc_code, tag, pic, attendence, is_mark}
        """


class getMyActivitiesType(View):
    def execuate(self, uid, loc_code):
        """
        获取我的活动类型: ??????(存疑：查询用户已经下单的活动的细节？返回数据类型确认一下？
        roc update：根据uid查询用户的所有订单order_status并返回 list of order_status

        :param uid:
        :param loc_code:
        :return:
            {[order_id, order_status], []}
        """


class getMyActivitiesBytype(View):
    def execuate(self, uid, type):
        """
        获取我的活动列表: UserOrderTable
        :param uid:
        :param type:
        :return:
            {[order_id, title, time, pic, price, order_status], }
        """


class getMySingleActivity(View):
    def execuate(self, order_id, uid):
        """
        获取我的单个活动列表: 查询UserOrderTable过滤即可, 然后根据act_id查询ActivityInfoTable
        :param order_id:
        :param uid:
            {order_id, title, time, detail, price, loc_code, pic, order_status, paymentid, pay_time}
        """


## 商家板块

class addCoopFav(View):
    def execuate(self, loc_code, uid, coopid):
        """
        收藏商家: 根据字段[loc_code, coopid]查询MerchantInfoTable，然后根据[uid]更新UserOrderTable ????????
        Roc update： 根据uid + coopid 查询用户商户收藏表，有的话把is_mark置1， 无的话，新增一条记录并且把is_mark字段置1
        :param loc_code:
        :param uid:
        :param coopid:
        :return:
        """
        state = 0  # 0: 失败，1: 成功

        return state


class getClubCoopListType(View):
    def execuate(self, loc_code):
        """
        获取合作商家类型：根据字段[loc_code]读取MerchantInfoTable ??????????????
        Roc update： 根据字段[loc_code]读取MerchantInfoTable中对应的type字段，返回地区下的所有type ， 数据返回类型list of type
        :param loc_code:
        :return:
            {coopid: type}
        """


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
            {[coopid, name, type, pic, loc_code]}
        """


class getOneCoopDetail(View):
    def execuate(self, coopid):
        """
        获取单个合作商家详情: 根据[coopid]查询MerchantInfoTable，然后根据[coopid]查询ActivityInfoTable
        :param coopid:
        :return:
            {coopid, name, detail, pic, loc_code, email, wechatid,
                EventList: [{act_id, type, title, time, pic, loc_code, tag, attendence}]}
        """


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
