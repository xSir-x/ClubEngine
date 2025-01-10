# -*- coding: utf-8 -*-

from wxpay.lib.wechatpayv3.wechatpayv3 import WeChatPay, WeChatPayType
from wxpay.settings import *


class WXMinPay(object):
    def __init__(self):
        self.wxpay = WeChatPay(
            wechatpay_type=WeChatPayType.NATIVE,
            mchid=MCHID,
            private_key=PRIVATE_KEY,
            cert_serial_no=CERT_SERIAL_NO,
            apiv3_key=APIV3_KEY,
            appid=APPID,
            notify_url=NOTIFY_URL,
            logger=LOGGER,
            partner_mode=PARTNER_MODE,
            proxy=PROXY,
            timeout=TIMEOUT,
            public_key=PUBLIC_KEY,
            public_key_id=PUBLIC_KEY_ID)

