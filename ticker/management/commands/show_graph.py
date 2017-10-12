# -*- coding: utf-8 -*-
import pprint
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from ticker.strategies.ema_month import EmaMonthStrategy
from trader.models import MARKETS


class Command(BaseCommand):
    """ Run Celery task """

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
                strat = EmaMonthStrategy(market)
                strat.start_from(datetime.utcnow())
                pprint.pprint(options['market'])
            else:
                raise CommandError('Market not supported.')
        else:
            raise CommandError('Market not found.')


