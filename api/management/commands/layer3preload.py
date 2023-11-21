from product.models import WeeklySale
from reports.models import Week
from reports.fetch import layer3_data,l3_flooring,products_query,pos_query
from service import logging
from service.storage_cache import StorageCache

from hashlib import md5
from django.core.management.base import BaseCommand
from django.db.models import Q, Min, Max
import pandas as pd


class Command(BaseCommand):
    help = 'Preloads all sales data'

    # def add_arguments(self, parser):
    #    parser.add_argument('poll_ids', nargs='+', type=int)

    def handle(self, *args, **options):
        ########################################################################
        # Preloading data
        ########################################################################
        products = layer3_data(data_query=products_query, init_key="products_")
        pos = layer3_data(data_query=pos_query, init_key="pos_")
        inches = layer3_data(init_key="inches", in_product=True)
        load = layer3_data(init_key="load", in_product=True)
        
        week_range = WeeklySale.objects.aggregate(
            max=Max("week_object"), min=Min("week_object"))
        logging.info(
            f"[LAYER3-PRELOAD] Preloading data from {week_range['min']} to {week_range['max']}")
        for week in range(week_range["min"], week_range["max"]+1):
            l3_flooring(week)
            logging.info(f"[LAYER3-PRELOAD] Preload {week}")

            d = WeeklySale.objects.filter(
                Q(week_object=week)).values()

            key = "queries_"+md5(d.query.__str__().encode("utf-8")).hexdigest()
            _, status = StorageCache.get_pickle(key)

            if status:
                continue
            else:
                df = pd.DataFrame(d)
                StorageCache.set_pickle(key, df)
