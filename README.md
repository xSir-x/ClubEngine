# Y-Club backend

> 注意：数据库所有时间暂时以 timezone.now()方式存储，如果涉及计算，需要单独转换为timestamp形式

## 数据库初始化
```
python3 manage.py makemigrations dbModel
python3 manage.py migrate # 注意：如果表已经存在，无法覆盖
```

## 服务启动脚本
```
python3 manage.py runserver
```

## 后端接口: 
- 接口异常代码： (200: 成功, 300: 程序异常)
- 详细接口文档：
【腾讯文档】会员小程序接口文档 https://docs.qq.com/doc/DYVJqckhWd3pXVlJo


## 关系型数据库设计
- 详细的接口字段见：dbModel/models.py （如以下字段存疑请以.py文件定义为准，修改请及时同步设计DB增删改查）
- 数据使用MYSQL

● 活动信息表：【ActivityInfoTable】

| 字段列表	         |类型	|长度	|描述|
|---------------|-----|-----|-----|
| act_id(PK)	   |str	|64	|活动id|
| coop_id	      |str	|64	|商户ID|
| type	         |char	|64	|活动类型: ongoing/past/new(入参可all)|
| title_en	     |str	|32	|活动标题|
| title_zh	     |str	|32	|活动标题|
| pic	          |str	|128	|活动图片链接：注意图片大小/像素等|
| loc_code	     |str	|32	|地区编码|
| tag	          |str	|32	|活动自定义表示，属于Y-Club or others|
| detail_zh	    |str	|256	|活动详情描述|
| detail_en	    |str	|256	|活动详情描述|
| is_recommend	 |int	|4	|1-推荐 0-不推荐 （默认置0）|
| price	        |double	|64	|活动价格都以人民币存储|
| start_time	   |time	|--	|格式: 1607829282121|
| end_time	     |time	|--	|格式: 1607829282121|
| address	      |str	|	|地址|
| longitude	    |str	|	|经度|
| latitude	     |str	|	|维度|

● 商家信息表：【MerchantInfoTable】

| 字段列表	          |类型	|长度	|描述|
|----------------|-----|-----|-----|
| coop_id(PK)	   |str	|64	|商户ID|
| type	          |char	|64	|商户类型: |
| pic	           |str	|128	|商户图片链接|
| loc_code	      |str	|32	|地区编码|
| name	          |str	|16	|商家名称|
| wechatid	      |str	|32	|商家微信ID|
| email	         |str	|32	|商家邮箱|
| detail_zh	     |str	|256	|商户描述|
| detail_en	     |str	|256	|商户描述|
| address	       |str	|	|地址|
| latitude	      |str	|	|经度|
| atitude	       |str	|	|维度|
| register_time	 |time	|--	|格式: 1607829282121|

● 用户订单表：【UserOrderTable】
             
|字段列表	|类型	|长度	|描述|
|-----|-----|-----|-----|
|order_id(PK)	|int	|64	|订单ID（自增）|
|uid	|str	|64	|用户ID|
|act_id	|str	|64	|活动ID|
|coop_id	|str	|int	|商户ID|
|pay_time	|time	|--	|支付时间|
|order_time	|time	|--	|下单时间|
|exp_time	|time	|--	|过期时间|
|paymentid	|int	|64	|支付ID：成功支付才存在，否则为空|
|order_status	|int	|4	|订单状态：1-未支付 2-支付成功 3-支付失败|

● 商户收藏表：【MerchantMaskTable】

| 字段列表	      |类型	|长度	|描述|
|------------|-----|-----|-----|
| uid(PK)    |	str|	64|	用户id|
| coop_id    |	str|	64|	商户id|
| is_mark    |	int|	4|	收藏商家状态：0-未收藏；1-收藏|
| mask_time	 |time	|--	|格式: 1607829282121|

● 活动收藏表：【ActsMarkTable】

|字段列表	|类型	|长度	|描述|
|-----|-----|-----|-----|
|uid(PK)|	str|	64|	用户id|
|act_id|	str|	64|	商户id|
|is_mark|	int|	4|	收藏商家状态：0-未收藏；1-收藏|
|mask_time	|time	|--	|格式: 1607829282121|

● 地区编码表：【AreaCodeTable】

|字段列表	|类型	|长度	|描述|
|-----|-----|-----|-----|
|loc_code(PK)	|str	|32	|地区编码|
|eng_name	|str	|16	|英文名|
|chn_name	|str	|16	|中文名|

● 用户信息表（会员标记）【UserInforTable】

|字段列表	|类型	|长度	|描述|
|-----|-----|-----|-----|
|uid(PK)	|str	|64	|用户id|
|name	|str	|16	|用户名称|
|level	|？	|？	|会员等级|
|wechat	|str	|32	|微信ID|
|pic	|str	|128	|用户头像图片|
|profile	|str	|256	|用户个人简介|
|email	|str	|32	|邮箱用户|
|register_time|time|--|注册日期|




