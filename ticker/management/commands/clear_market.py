# -*- coding: utf-8 -*-
import pprint
from django.core.management.base import BaseCommand, CommandError
from trader.btc_trader import BTCTrader
from trader.models import MARKETS


class Command(BaseCommand):
    """ Clear Market """

    def add_arguments(self, parser):
        parser.add_argument('market', type=str)

        parser.add_argument(
            '--market',
            action='store_true',
            dest='market',
            help='market name',
        )

    def handle(self, *args, **options):
        if 'market' in options:
            market = options['market']
            if market in [m[0] for m in MARKETS]:
                trader = BTCTrader(market)
                trader.clear_market()
            else:
                raise CommandError('Market not supported.')
        else:
            raise CommandError('Market not found.')
