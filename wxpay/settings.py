# -*- coding: utf-8 -*-
import json
import logging
import os
from random import sample
from string import ascii_letters, digits
import time
import uuid

print(os.getcwd())
# 微信支付商户号（直连模式）或服务商商户号（服务商模式，即sp_mchid)
MCHID = "1704578643"

# 商户证书私钥
with open(os.path.join(os.getcwd(), 'wxpay/cert/apiclient_key.pem')) as f:
    PRIVATE_KEY = f.read()

# 商户证书序列号
CERT_SERIAL_NO = '5DA0AED191E6B1FE6B165CA286D3F31B56CBE7D5'

# API v3密钥， https://pay.weixin.qq.com/wiki/doc/apiv3/wechatpay/wechatpay3_2.shtml
APIV3_KEY = 'y9865074351clubapp9074351865ubap'

# APPID，应用ID或服务商模式下的sp_appid
APPID = 'wxf07870791f65ca07'

APPID_NAME = '涯程科技(深圳)有限责任公司'

# 回调地址，也可以在调用接口的时候覆盖
NOTIFY_URL = 'https://localhost:80/notifyOrder'

# 微信支付平台证书缓存目录，减少证书下载调用次数，首次使用确保此目录为空目录。
# 初始调试时可不设置，调试通过后再设置，示例值:'./cert'。
# 新申请的微信支付商户号如果使用平台公钥模式，可以不用设置此参数。
CERT_DIR = None

# 日志记录器，记录web请求和回调细节
logging.basicConfig(filename=os.path.join(os.getcwd(), 'demo.log'), level=logging.DEBUG, filemode='a', format='%(asctime)s - %(process)s - %(levelname)s: %(message)s')
LOGGER = logging.getLogger("demo")

# 接入模式:False=直连商户模式，True=服务商模式
PARTNER_MODE = False

# 代理设置，None或者{"https": "http://10.10.1.10:1080"}，详细格式参见https://requests.readthedocs.io/en/latest/user/advanced/#proxies
PROXY = None

# 请求超时时间配置
TIMEOUT = (10, 30) # 建立连接最大超时时间是10s，读取响应的最大超时时间是30s

# 微信支付平台公钥
# 注：2024年09月后新申请的微信支付账号使用公钥模式初始化，需配置此参数。
with open(os.path.join(os.getcwd(), 'wxpay/cert/pub_key.pem')) as f:
    PUBLIC_KEY = f.read()

# 微信支付平台公钥ID
# 注：2024年09月后新申请的微信支付账号使用公钥模式初始化，需配置此参数。
PUBLIC_KEY_ID = 'PUB_KEY_ID_0117045786432025011400326400001236'
