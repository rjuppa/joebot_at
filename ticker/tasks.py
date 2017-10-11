# -*- coding: utf-8 -*-

# file with periodical tasks
from __future__ import absolute_import

from django.db.models import Q
from celery.utils.log import get_task_logger
from celery import shared_task
from decimal import Decimal
from joebot_at.taskapp.celery import app as celery_app
from datetime import datetime
from dateutil.relativedelta import relativedelta
from tabulate import tabulate

from .ots import OTS
from trader.models import Wallet, MARKETS, get_coin_labels
from trader.btc_trader import BTCTrader

from ticker.api.polo import Poloniex2, API
from configobj import ConfigObj


logger = get_task_logger(__name__)

@shared_task
def test_task():
    print('Hello! It is {}'.format(datetime.utcnow()))
    return True


@shared_task
def get_ticker_task():
    exchange = API()
    data = exchange.returnTicker()
    result = []
    for name in data:
        if name in [m[0] for m in MARKETS]:
            result.append({name: data[name]})
            # print('{}: {}\n'.format(name, data[name]))
    return result


@shared_task
def get_price_task():
    exchange = API()
    data = exchange.returnTicker()
    result = []
    for name in data:
        if name in [m[0] for m in MARKETS]:
            result.append({name: data[name]['last']})
            # print('Last price {}: {}\n'.format(name, data[name]['last']))
    return result


@shared_task
def process_month_avg_task():
    # it is need to import in runtime!
    from ticker.strategies.month_average import MonthAverageStrategy
    strat = MonthAverageStrategy('BTC_BCH')
    strat.check_for_trading()

    strat = MonthAverageStrategy('BTC_ETH')
    strat.check_for_trading()

    strat = MonthAverageStrategy('BTC_ZEC')
    strat.check_for_trading()

    strat = MonthAverageStrategy('BTC_XRP')
    strat.check_for_trading()

    strat = MonthAverageStrategy('BTC_DASH')
    strat.check_for_trading()

    strat = MonthAverageStrategy('BTC_LTC')
    strat.check_for_trading()

    strat = MonthAverageStrategy('BTC_STR')
    strat.check_for_trading()

    strat = MonthAverageStrategy('BTC_XMR')
    strat.check_for_trading()

    strat = MonthAverageStrategy('BTC_STRAT')
    strat.check_for_trading()

    strat = MonthAverageStrategy('BTC_GNO')
    strat.check_for_trading()

    return True


@shared_task
def get_balance_task():

    config = ConfigObj('config.ini')
    api_key = bytes(config['api_key'], encoding='utf8')
    secret = bytes(config['secret'], encoding='utf8')
    polo = API(dict(api_key=api_key, secret=secret))
    balance = polo.returnBalances()
    if balance:
        result = []
        for name in balance.keys():
            if name in get_coin_labels():
                result.append({name: balance[name]})
                ##print('Balance {}: {}\n'.format(name, balance[name]))
        return result
    else:
        return 'ERROR: Balance call failed.'
