# -*- coding: utf-8 -*-
import pprint
from django.core.management.base import BaseCommand
from ticker.tasks import get_balance_task


class Command(BaseCommand):
    """ Run Celery task """

    def handle(self, *args, **options):
        result = get_balance_task()
        pprint.pprint(result)
