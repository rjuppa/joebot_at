# -*- coding: utf-8 -*-
import pprint
from django.core.management.base import BaseCommand
from ticker.tasks import get_ticker_task


class Command(BaseCommand):
    """ Run Celery task """

    def handle(self, *args, **options):
        result = get_ticker_task()
        pprint.pprint(result)
