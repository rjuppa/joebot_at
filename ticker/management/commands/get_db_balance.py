# -*- coding: utf-8 -*-
import pprint
from django.core.management.base import BaseCommand
from ticker.tasks import get_balance_task
from trader.models import Wallet, MARKETS, get_coin_labels


class Command(BaseCommand):
    """ Run Celery task """

    def handle(self, *args, **options):
        result = []
        w = Wallet.get_or_create('BTC')
        for name in get_coin_labels():
            w = Wallet.get_or_create(name)
            print('Balance {}:   from:{}   to:{}'.format(name, w.balance_from(), w.balance_to()))

            ##print('Balance {}: {}\n'.format(name, balance[name]))

        #pprint.pprint(result)
