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
|pic	|str	|128	|活动图片链接：注意图片大小/像素等|
|loc_code	|str	|32	|地区编码|
|tag	|str	|32	|活动自定义表示，属于Y-Club or others|
|detail	|str	|256	|活动详情描述|
|act_time	|time	|--	|活动时间|
|is_recommend	|int	|4	|1-推荐 0-不推荐 （默认置0）|
|price	|double	|64	|活动价格都以人民币存储|
|timestamp	|time	|--	|格式: 1607829282121|

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

# 后端接口: 
- 接口异常代码： (200: 成功, 300: 程序异常)
## 活动板块

### Func: 收藏活动【addFavActivity】

```
-  request: act_id, uid, lang(取值范围: [en, zh])
-  response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"status": 0/1(int，0: 失败，1: 成功)
}
```


### Func: 获取所有活动类型 【getAllType】

```
-  request: loc_code
-  response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"res": [{"type": "类型1"}, {"type": "类型2"}, ...]
}
```


### Func: 获取所有活动列表【getActivitiesByType】

```
-  request: type, loc_code, uid, lang(取值范围: ["en", "zh"]), pageId=0（指定pageid）, pageSize=7 (默认7，[1, 100])
-  response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"total": 21,
	"res": [{"act_id": , 
	        "type": , 
	        "title": ,
		"starttime": 1607829282121, (字段是哪个表？)
	        "pic": , 
	        "loc_code": ,
		"address": ,
		"latitude": ,(经度, str)
		"atitude": ,(经度, str)
	        "tag": , 
	        "is_mark": , 
	        "act_time": , 
	        "attendence": }, ...]	(数据如何计算？)
}
        
```
注意: ①、page查询需要进行redis缓存，redis设置过期时间；②、input para异常处理


### Func: 获取活动推荐列表（每个地区有一个默认的推荐活动，来自运营打标）【getRecommandActivities】

```
-  request: loc_code, uid
-  response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
        "res": [{"act_id": ,
            "type": ,
            "title": ,
            "starttime": , (取自: timestamp字段)
            "pic": ,
            "loc_code": ,
            "tag": ,
            "attendence": , (数据如何计算？)
            "is_mark": }, ...]
}
```


### Func: 获取单个活动细节【getSingleActivityDetail】

```
-  request: type, act_id, uid
-  response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"res": {"act_id": ,
	    	"title": ,
	    	"starttime": , (字段是哪个表？)
	    	"endtime": , (字段是哪个表？)
	    	"detail": ,
	    	"price": ,
	    	"loc_code": ,
		"address": ,
		"latitude": ,(经度, str)
		"atitude": ,(经度, str)
	    	"tag": ,
	    	"pic": ,
	    	"attendence": , (数据如何计算？)
	    	"is_mark": }
}
```


### Func: 获取我的活动类型【getMyActivitiesType】(接口删除)

```
-  request: uid, loc_code
-  response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"res": 
}
```


### Func: 获取我的活动列表【getMyActivitiesBytype】

```
-  request: uid, loc_code
-  response:{
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"res": [{"order_id": ,
            "act_id": ,
            "act_time": ,
            "pic": ,
            "price": ,
            "order_status": 
            "title": }, ...]
}
```
注意： 所有活动信息这边都需要传

### Func: 获取我的单个活动列表【getMySingleActivity】

```
-  request: uid, loc_code
-  response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"res": {"order_id": , 
		"title": , 
		"order_time": , 
		"detail": , 
		"price": ,
		"loc_code": ,
		"pic": ,
		"order_status": , 
		"paymentid": , 
		"pay_time": }
}
        
```
注意： 所有活动信息这边都需要传


支付活动（跟Canyu讨论下细节）
payActivity


## 商家板块

### Func: 收藏商家【addCoopFav】

```
-  request: loc_code, uid, coopid, lang (loc_code用处是？)
-  response:{
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"status": 0/1(int，0: 失败，1: 成功)
}
```


### Func: 获取合作商家类型【getClubCoopListType】
```
-  request: loc_code
-  response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"res": [{"type": "类型1"}, {"type": "类型2"}, ...]
}
```

### Func: 获取合作商家信息【getClubCoopListByType】
```
-  request: type, loc_code, uid, lang, pageId=0, pageSize=7 (默认7，[1, 100])
-  response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"total": 21, 
        "res": [{
		"coopid": ,
		"name": ,
		"type": ,
		"pic": ,
		"address": ,
		"latitude": ,(经度, str)
		"atitude": ,(经度, str)
		"is_mark": ,
		"loc_code": }, ...]
   }
```


### Func: 获取单个合作商家详情【getOneCoopDetail】
```
-  request: coopid, lang
-  response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"res": {"coopid": ,
		"name": ,
		"detail": ,
		"pic": ,
		"loc_code": ,
		"email": ,
		"wechatid": ,
		"address": , 
		"EventList": [{"act_id": ,
				"type": ,
				"title": ,
				"act_time": ,
				"pic": ,
				"loc_code": ,
				"tag": ,
				"attendence": }]}
}   
```
注： EventList需活动字段细节一致


### 会员板块：

### Func: 获取商会信息【getClubInfo】
```
- request: type
- response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"res"：string
}
```

### Func: 获取会员制度信息【getMembershipInfo】
```
- request: type
- response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
}
```

### Func: 获取商会联系方式【getClubContactInfo】
```
- request: type
- response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
}
```



### Func: 获取会员详细信息【getMemberInfo】
```
- request: type=all，userId：string
- response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"res":{
		userid:string
             	name：string
           	activityCnt：int
         	membershipExpDays：int
           	memebrshipLevel：string
           	memebrshipLevelStatus：int
           	profilePic：string
	}
}
```

### Func: 注册会员：【upgradeMembership】
```
- request: userid, wechat, email, phone, profession, location
- response: {
	"state": 200
	"exceptions": "异常详情", （非必填） 
	"status": 0/1(int，0: 失败，1: 成功)
}
```





