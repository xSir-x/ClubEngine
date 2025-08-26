"""ClubEngine URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views



urlpatterns = [
    # path('admin/', admin.site.urls),
    # path('add', views.add),
    # path('user_orders', views.user_orders),
    # path('pay_rate', views.pay_rate),
    # path('get_top', views.get_top),
    # 登录接口
    path('userlogin', views.auth_user),
    path('userRegister', views.auth_register),
    path('searchUser', views.search_user),
    path('testAccess', views.test_access),

    # 页面接口
    path('add_fav_act', views.add_fav_act),
    path('get_all_type', views.get_all_type),
    path('get_acts_bytype', views.get_acts_bytype),  # redis缓存
    path('get_recomm_acts', views.get_recomm_acts),
    path('get_single_act_det', views.get_single_act_det),
    path('get_my_acts_bytype', views.get_my_acts_bytype),
    path('get_my_act', views.get_my_act),
    path('add_coopfav', views.add_coopfav),
    path('get_cooplist_type', views.get_cooplist_type),
    path('get_coopdet_bytype', views.get_coopdet_bytype),  # redis缓存
    path('get_coopdet', views.get_coopdet),

    path('modifyMembership', views.modify_membership),

    # 支付接口
    path('payOrder', views.minipay),
    path('notifyOrder', views.mininotify),
    path('genOrder', views.genorder),
    path('serchOrder', views.search_order),
    
    # 社交功能接口
    path('sendInvitation', views.send_invitation),
    path('getInvitation', views.get_invitation), 
    path('updateInvitation', views.update_invitation),
    path('getFriends', views.get_friends),
    
    # 评分接口
    path('rateCompetition', views.rate_competition),
]
