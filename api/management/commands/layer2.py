from datetime import datetime
from product.models import WeeklySale
from reports.models import Week
from reports.fetch import layer3_data,l3_flooring,products_query,pos_query
from service import logging
from service.storage_cache import StorageCache

from hashlib import md5
from django.core.management.base import BaseCommand
from django.db.models import Q, Min, Max
import pandas as pd

dtypes={
    "site_id_id":"uint16",
    "product_id":"uint16",
    "year":"uint16",
    "week":"uint8",
    # "sold_units":"uint16",
    # "inventory":"uint16",
    "group":"uint8",
    "division":"uint8",
    "product_range":"uint8",
    "segment":"uint8",
    "city":"uint16",
    "account":"uint16",
    "zone":"uint16",
    "region":"uint16",
    "country":"uint8",
    "custom_account":"uint16",
    "flooring_plan":"uint8",

}

class Command(BaseCommand):
    help = 'Preloads all sales data'

    # def add_arguments(self, parser):
    #    parser.add_argument('poll_ids', nargs='+', type=int)
    def load_l2(self,w : int):
        
        return StorageCache.get_pickle(f"weeklysales_{w}")
    def handle(self, *args, **options):
        ########################################################################
        # Preloading data
        ########################################################################
        products = layer3_data(data_query=products_query, init_key="products_")
        pos = layer3_data(data_query=pos_query, init_key="pos_")
        inches = layer3_data(init_key="inches", in_product=True)
        load = layer3_data(init_key="load", in_product=True)
        
        # JOIN PRODUCTS WITH TYPES
        products = products.set_index("id").join(inches.set_index("product_id")).join(load.set_index("product_id"))
        
        #del inches
        #del load
        
        
        week_range = WeeklySale.objects.aggregate(
            max=Max("week_object"), min=Min("week_object"))
        logging.info(
            f"[LAYER-2] Processing data from {week_range['min']} to {week_range['max']}")

        #data = [pd.DataFrame() for _ in range(week_range["min"], week_range["max"]+2)]
        data = pd.DataFrame()
        # PROCESS EACH WEEK
        a = datetime.now() 
          
        for week in range(week_range["min"], week_range["max"]+1):
            df, status = StorageCache.get_pickle(f"weeklysales_{week}")
            if status: continue

            logging.info(f"[LAYER2] Preload {week}")

            d = WeeklySale.objects.filter(Q(week_object=week)).values()

            key = "queries_"+md5(d.query.__str__().encode("utf-8")).hexdigest()
            
            
            df, status = StorageCache.get_pickle(key)

            if not status:
                df = pd.DataFrame(d)
                StorageCache.set_pickle(key, df)
            
            # JOIN WITH WEEKLY FLOORING
            flooring = l3_flooring(week)
            
            if len(flooring) == 0:
                #df["flooring_plan"] = 0.0
                pass
                #logging.info(f"[THREAD] no flooring data for {week}")
            else:
                flooring = flooring.drop(columns=["id"])

                flooring = flooring.rename(
                    columns={"week_id": "week_object_id", "point_of_sale_id": "site_id_id"})

                flooring_index = ["week_object_id", "product_id", "site_id_id"]
                df = df.set_index(flooring_index).join(flooring.set_index(flooring_index)).rename(
                    columns={"target": "flooring_plan"}).reset_index().rename(columns={"index": "site_id_id"})
            #if week==157:

            if len(df):
                
                df = df.set_index("product_id").join(products).reset_index().rename(columns={"index": "product_id"}).set_index("site_id_id").join(pos.set_index("id")).reset_index().rename(columns={"index": "site_id_id"})
                df.drop(columns=["id","first_date_of_week"],inplace=True)

            #logging.info(f"[LAYER-2] dropping unnecesary columns")
            
            StorageCache.set_pickle(f"weeklysales_{week}",df)

        logging.info(f"[LAYER-2] Joining all pickle")
        weeklysales = pd.concat([d[0] for d in [self.load_l2(w) for w in range(week_range["max"]+1)] if d[1] and len(d[0])])
        weeklysales.flooring_plan.fillna(0,inplace=True)
        #logging.info(f"[LAYER-2] downcasting dtypes")
        weeklysales=weeklysales.astype(dtypes, copy=False)
        
        logging.info(f"[LAYER-2] saving")
        StorageCache.set_pickle(f"weeklysales",weeklysales)


            
