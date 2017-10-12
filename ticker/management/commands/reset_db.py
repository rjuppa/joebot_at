# -*- coding: utf-8 -*-
import pprint
from django.core.management.base import BaseCommand
from trader.btc_trader import BTCTrader
from trader.models import MARKETS


class Command(BaseCommand):
    """ Reset DB """

    def handle(self, *args, **options):
        for market, name in MARKETS:
            trader = BTCTrader(market)
            trader.clear_market()
            trader.deposit_btc(0.2)
