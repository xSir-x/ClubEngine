# Y-Club backend

## 关系型数据库设计
● 活动信息表：
> primary key：act_id

|字段列表	|类型	|长度	|描述|
|-----|-----|-----|-----|
|act_id(PK)	|str	|64	|活动id|
|coopid	|str	|64	|商户ID|
|type	|char	|64	|活动类型: ongoing/past/new(入参可all)|
|title	|str	|32	|活动标题|
|pic	|str	128	|活动图片链接：注意图片大小/像素等|
|loc_code	|str	|32	|地区编码|
|tag	|str	|32	|活动自定义表示，属于Y-Club or others|
|detail	|str	|256	|活动详情描述|
|act_time	|time	|--	|活动时间|
|is_recommend	|int	|4	|1-推荐 0-不推荐 （默认置0）|
|price	|double	|64	|活动价格都以人民币存储|

● 商家信息表：
> primary key：coopid

|字段列表	|类型	|长度	|描述|
|-----|-----|-----|-----|
|coopid(PK)	|str	|64	|商户ID|
|type	|char	|64	|商户类型: |
|pic	|str	|128	|商户图片链接|
|loc_code	|str	|32	|地区编码|
|name	|str	|16	|商家名称|
|wechatid	|str	|32	|商家微信ID|
|email	|str	|32	|商家邮箱|
|detail|	str	|256	|商家详情描述|
|update_time|||更新时间|

● 用户订单表：
> primary key：order_id   （自增）
             
|字段列表	|类型	|长度	|描述|
|-----|-----|-----|-----|
|order_id(PK)	|int	|64	订单ID|
|uid	|str	|64	|用户ID|
|act_id	|str	|64	|活动ID|
|coop_id	|str	|int	|商户ID|
|pay_time	|time	|--	|支付时间|
|order_time	|time	|--	|下单时间|
|exp_time	|time	|--	|过期时间|
|paymentid	|int	|64	|支付ID：成功支付才存在，否则为空|
|order_status	|int	|4	|订单状态：1-未支付 2-支付成功 3-支付失败|
|is_mark	|int	|4	|收藏状态：0-未收藏；1-收藏|
|update_time|||入库时间|

● 商户收藏表：
> primary key：uid

|字段列表	|类型	|长度	|描述|
|-----|-----|-----|-----|
|uid(PK)|	str|	64|	用户id|
|coopid|	str|	64|	商户id|
|is_mark|	int|	4|	收藏商家状态：0-未收藏；1-收藏|
|update_time|||收藏日期|

● 活动收藏表：
> primary key：uid

|字段列表	|类型	|长度	|描述|
|-----|-----|-----|-----|
|uid(PK)|	str|	64|	用户id|
|act_id|	str|	64|	商户id|
|is_mark|	int|	4|	收藏商家状态：0-未收藏；1-收藏|
|update_time|||收藏日期|

● 地区编码表：
> primary key：loc_code

|字段列表	|类型	|长度	|描述|
|-----|-----|-----|-----|
|loc_code(PK)	|str	|32	|地区编码|
|eng_name	|str	|16	|英文名|
|chn_name	|str	|16	|中文名|

● 用户信息表（会员标记）
> primary key：uid

|字段列表	|类型	|长度	|描述|
|-----|-----|-----|-----|
|uid(PK)	|str	|64	|用户id|
|name	|str	|16	|用户名称|
|level	|？	|？	|会员等级|
|wechat	|str	|32	|微信ID|
|pic	|str	|128	|用户头像图片|
|profile	|str	|256	|用户个人简介|
|email	|str	|32	|邮箱用户|
|update_time|||注册日期|

## 后端接口: 活动板块

> Func: 收藏活动【addFavActivity】
```
-  request: act_id, uid
-  response: int(0: 失败，1: 成功)
```

> Func: 获取所有活动类型 【getAllType】
```
-  request: loc_code
-  response: 
        [{"act_id": , "type": }
        , ...]
```

> Func: 获取所有活动列表【getActivitiesByType】
```
-  request: type, loc_code, , pageId=0（指定pageid）, pageSize=7 (默认7，[1, 100])
-  response: 
        [{"act_id": , 
        "type": , 
        "title": , 
        "pic": , 
        "loc_code": , 
        "tag": , 
        "is_mark": , 
        "act_time": , 
        "attendence": }
        , ...]
```
改动：time -> act_time
<font color=red>
  request: type: str(指定type字段/all), loc_code:str，uid:(可以为空), pageId=0（指定pageid）, pageSize=7 (默认7，[1, 100])
  response: {
            res:[{
                 act_id: string
                 type：string
.                title: string
.                act_time: timestamp
.                pic: string
				   loc_code：string
                 tag：string（i.e Y-club/new）
				   attendence：[string]
                 is_mark: int (1-收藏，0-未收藏)
.                }]
.           }
注意: ①、page查询需要进行缓存，设置过期时间；②、input para异常处理
</font>

> Func: 获取活动推荐列表（每个地区有一个默认的推荐活动，来自运营打标）【getRecommandActivities】
```
-  request: loc_code, uid
-  response: 
        [{"act_id": ,
            "type": ,
            "title": ,
            "act_time": ,
            "pic": ,
            "loc_code": ,
            "tag": ,
            "attendence": ,
            "is_mark}, 
        ...]
```

改动：time -> act_time

request: loc_code，uid
  response: {
            res:[{
                 act_id: string
                 type：string
.                title: string
.                time: timestamp
.                pic: string
				   loc_code：string
                 tag：string（i.e Y-club/new）
                 attendence：[string]（需要同步计算有多少个人报名了？？？）
					is_mark: int (1-收藏，0-未收藏)
.                }]
.           }


> Func: 获取单个活动细节【getSingleActivityDetail】
```
-  request: type, act_id, uid
-  response: 
        {act_id": ,
            "title": ,
            "time": ,
            "detail": ,
            "price": ,
            "loc_code": ,
            "tag": ,
            "pic": ,
            "attendence": ,
            "is_mark": }
```
改动：删除了uid， time -> act_time

  request: type=single, act_id:string，uid: str
  response: {
                 act_id: string
.                title: string
.                time: timestamp
.                detail: string
.                price: string
.                loc_code: string
				   tag：string（i.e Y-club/new）
.                pic: [string]
				  attendence：[string]]（需要同步计算有多少个人报名了？？？）
 is_mark: int (1-收藏，0-未收藏)
.           }

> Func: 获取我的活动类型【getMyActivitiesType】
```
-  request: uid, loc_code
-  response: 
        [{"order_id": ,
          "order_status": }
          , ...]
```

  request: loc_code=hk, uid: str
  response: {
            res:[{
				 order_id
order_status
}]
.           }

> Func: 获取我的活动列表【getMyActivitiesBytype】
```
-  request: uid, loc_code
-  response: 
        [{"order_id": ,
            "act_id": ,
            "act_time": ,
            "pic": ,
            "price": ,
            "order_status": 
            "title": }
            , ...]
```
改动： time -> act_time


  request: type: (ongoing/past/new/all)，uid: str
  response: {
            actlist:[{
                order_id: string
.                title: string
.                time: timestamp
.                pic: string
.                price: double
.                order_status: int 备注：1-未支付 2-支付成功 3-支付失败
.                }]
.           }

> Func: 获取我的单个活动列表【getMySingleActivity】
```
-  request: uid, loc_code
-  response: 
        {"order_id": , 
        "title": , 
        "order_time": , 
        "detail": , 
        "price": ,
        "loc_code": ,
        "pic": ,
        "order_status": , 
        "paymentid": , 
        "pay_time": }
```
改动： time -> order_time

  request:  order_id:int，uid：str
  response: {
                order_id: string
.                title: string
.                time: timestamp
.                detail: string
.                price: double
.                loc_code: string
.                pic: string
。              order_status: int 备注：1-未支付 2-支付成功 3-支付失败
。              paymentid：int
。              payTime：timeStamp
.           }


支付活动（跟Canyu讨论下细节）
payActivity


### 商家板块

> Func: 收藏商家【addCoopFav】
```
-  request: loc_code, uid, coopid
-  response: int(0: 失败，1: 成功)
```
改动： loc_code用处是？？

> Func: 获取合作商家类型【getClubCoopListType】
```
-  request: loc_code
-  response: 
        [{"coopid": coopid, "type": type},
            ...]
```
  request: loc_code=hk
  response: {
             res：[type: string, ...]
.           }

> Func: 获取合作商家信息【getClubCoopListByType】
```
-  request: type, loc_code, uid, pageId=0, pageSize=7 (默认7，[1, 100])
-  response: 
        [{"coopid": , "name": , "type": , "pic": , "loc_code": },
            ...]
```
改动： uid, pageId两个字段好像没有用？？


 request:  type:str，loc_code:string,uid=xxxx, pageId=0（从第一页开始）,   pageSize=7 (默认7，[1, 100])
 response: {
             coopList：[{
.                coopid:string,
                name:string,
.               type:string,
.               pic: string,
.               loc_code:string
.             }]
.           }

> Func: 获取单个合作商家详情【getOneCoopDetail】
```
-  request: coopid
-  response: 
        {"coopid", "name", "detail", "pic", "loc_code", "email", "wechatid",
                EventList: [{"act_id", "type", "title", "act_time", "pic", "loc_code", "tag", "attendence"}]}
```
  
request: coopid: str
response: {
             coopInfo：{
.                coopid:string,
                name:string,
.               detail:string
.               pic: string,
.               loc_code:string,
.               email:string
.               wechatid:string
.               EventList:[{
                 act_id: string
                 type：string
.                title: string
.                time: timestamp
.                pic: string
				   loc_code：string
                 tag：string（i.e Y-club/new）
				   attendence：[pic,string]
                }]
.             }
.           }

注：需要关联多个表



### 会员板块：

> 获取商会信息
- getClubInfo

request: type=all
  response: {
             detail：string
.           }



> 获取会员制度信息
- getMembershipInfo

request: type=all
  response: {
             detail：string
.           }



> 获取商会联系方式
- getClubContactInfo

request: type=all
response: {
             wechatID：string
。           e-mail：string
.           }




> 获取会员详细信息
- getMemberInfo
 
request: type=all，userId：string
  response: {
.             userid:string
             name：string
。           activityCnt：int
。           membershipExpDays：int
。           memebrshipLevel：string
。           memebrshipLevelStatus：int
。           profilePic：string
.           }


> 注册会员：
- upgradeMembership
  
request：userid：string， wechat：string， e-mail：string， phone：string， profession：string，location：string

response： {
status:1-成功，2-失败s
.}




