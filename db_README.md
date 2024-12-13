# Y-Club backend

## 关系型数据库设计
●活动信息表：primary key：act_id
字段列表	类型	长度	描述
act_id(PK)	str	64	活动id
coopid	str	64	商户ID
type	char	64	活动类型: ongoing/past/new(入参可all)
title	str	32	活动标题
pic	str	128	活动图片链接：注意图片大小/像素等
loc_code	str	32	地区编码
tag	str	32	活动自定义表示，属于Y-Club or others
detail	str	256	活动详情描述
act_time	time	--	活动时间
is_recommend	int	4	1-推荐 0-不推荐 （默认置0）
price	double	64	活动价格都以人民币存储

●商家信息表：primary key：coopid
字段列表	类型	长度	描述
coopid(PK)	str	64	商户ID
type	char	64	商户类型: 
pic	str	128	商户图片链接
loc_code	str	32	地区编码
name	str	16	商家名称
wechatid	str	32	商家微信ID
email	str	32	商家邮箱
detail	str	256	商家详情描述

●用户订单表：primary key：order_id   （自增）                 
字段列表	类型	长度	描述
order_id(PK)	int	64	订单ID
uid	str	64	用户ID
act_id	str	64	活动ID
coop_id	str	int	商户ID
pay_time	time	--	支付时间
order_time	time	--	下单时间
exp_time	time	--	过期时间
paymentid	int	64	支付ID：成功支付才存在，否则为空
order_status	int	4	订单状态：1-未支付 2-支付成功 3-支付失败
is_mark	int	4	收藏状态：0-未收藏；1-收藏
●用户商户收藏表：primary key：uid 
字段列表	类型	长度	描述
uid(PK)	str	64	用户id
coopid	str	64	商户id
is_mark	int	4	收藏商家状态：0-未收藏；1-收藏

●地区编码表：primary key：loc_code
字段列表	类型	长度	描述
loc_code(PK)	str	32	地区编码
eng_name	str	16	英文名
chn_name	str	16	中文名

●用户信息表（会员标记）primary key：uid
字段列表	类型	长度	描述
uid(PK)	str	64	用户id
name	str	16	用户名称
level	？	？	会员等级
wechat	str	32	微信ID
pic	str	128	用户头像图片
profile	str	256	用户个人简介
email	str	32	邮箱用户
