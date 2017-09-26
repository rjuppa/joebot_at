# -*- coding: utf-8 -*-
# Copyright 2016-2017 LANshark Consulting Group, LLC. All Rights Reserved.
from django.conf.urls import url

from . import views

urlpatterns = [
    # trades
    url(r'^trade/list$',
        views.TradeList.as_view(),
        name='trade-list'),

]
