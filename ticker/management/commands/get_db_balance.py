# -*- coding: utf-8 -*-
import pprint
from decimal import Decimal
from django.core.management.base import BaseCommand
from ticker.tasks import get_price_task
from trader.models import Wallet, MARKETS, get_coin_labels


class Command(BaseCommand):
    """ Run Celery task """

    def get_price(self, prices, symbol):
        market = 'BTC_' + symbol
        for item in prices:
            key = next(iter(item))
            if key == market:
                return Decimal(item[key])
        return Decimal('0.0')

    def handle(self, *args, **options):
        w = Wallet.get_or_create('BTC')
        prices = get_price_task()
        print('Balance   BTC:   {:8.3f}'.format(w.balance_from()))
        for name in get_coin_labels():
            if name != 'BTC':
                w = Wallet.get_or_create(name)
                price = self.get_price(prices, name)
                balance = w.balance_to()
                print('Balance {}:   {:8.4f}   ({:8.5f} BTC)'.format(name.rjust(5), balance, balance*price))

        # pprint.pprint(prices)
