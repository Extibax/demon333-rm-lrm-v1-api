from ntpath import join
from service import logging
from requests import get
from product.models import ProductType, Week, WeeklySale
from product.models import Product
from reports.models import Flooring
from store.models import PointOfSale
from service.storage_cache import StorageCache
from hashlib import md5
import pandas as pd
from django.db.models import Q, Max
from service import Thread
import numpy as np
from api.settings import LOAD_LAYER2
from functools import lru_cache
adapter = {
    # pandas name (joined.keys) : target name
    'division': "product_division",
    'group': 'product_group',
    'custom_account': "point_of_sale_account",
    'site_id_id': "point_of_sale",
    'country': "point_of_sale_country",
    'region': "point_of_sale_region",
    'zone': "point_of_sale_zone",
    'city': "point_of_sale_city",
    "site_id_id": "point_of_sale",
    "product_range": "product_range",
    "segment": "product_segment",
    # product types
    "INCHES": "product_inches",
    "LOAD": "product_load"
}
adapter_fp = adapter.copy()

adapter_fp['point_of_sale_id'] = adapter_fp["site_id_id"]
adapter_fp['week_id'] = "week_object_id"

product_fields = ("id", "group", "group__value",
                  "division", "sku", "division__value", "product_range", "product_range__value", "segment", "segment__value")
pos_fields = ("id", "site_id", "gscn_site_name", "city", "city__name", "account", "account__name", "zone", "zone__name",
              "region", "region__name", "country", "country__name", "custom_account", "custom_account__name")

products_query = Product.objects.all().values(*product_fields)
pos_query = PointOfSale.objects.all().values(*pos_fields)

# max_week = WeeklySale.objects.aggregate(
#     max=Max("week_object"))["max"]
max_week = 205

weeklysales = pd.DataFrame()


if LOAD_LAYER2:

    # data = [d[0] for d in data if d[1]]
    # if len(data):
    #weeklysales = pd.concat([d[0] for d in [StorageCache.get_pickle(f"weeklysales_{w}") for w in range(max_week+1)] if d[1]])
    weeklysales, _ = StorageCache.get_pickle(f"weeklysales")
    # def load_l2(w : int):
    #    logging.info(f"[L2] Downloading {w}")
    #    return StorageCache.get_from_s3(f"weeklysales_{w}")

    #threads = [Thread(target=load_l2,args=(w,)) for w in range(max_week+1)]

    # for thread in threads:
    #    thread.start()

    #weeklysales = pd.concat([d[0] for d in [thread.join() for thread in threads] if d[1]])
    #weeklysales = pd.concat([d[0] for d in [load_l2(w) for w in range(max_week+1)] if d[1]])


@lru_cache(maxsize=50)
def get_filtered_data_v2(min: int, max: int, filters) -> pd.DataFrame:
    dfs = list()

    # for w in range(min,max+1):
    #     logging.info("[L2] filtering for "+str(w))
    #     weeklysales[w]=weeklysales[w].rename(columns=adapter)
    #     temp = weeklysales[w].query(filters).rename(columns={v: k for k, v in adapter.items()})
    #     dfs.append(temp)
    #     del temp

    # logging.info("[L2] concatenating")
    # return  pd.concat(dfs)
    logging.info(f"[L2] filtering for {min} to {max}")
    temp = weeklysales.query(
        f"week_object_id>={min} and week_object_id<={max}")
    logging.info(f"[L2] renaming")
    temp = temp.rename(columns=adapter)
    logging.info(f"[L2] filtering")
    temp = temp.query(filters)
    logging.info(f"[L2] renaming back")
    temp = temp.rename(columns={v: k for k, v in adapter.items()})
    logging.info(f"[L2] returning")

    return temp


def get_product_type(type):
    return pd.DataFrame(ProductType.objects.filter(key=type).values()).rename(columns={"value": type}).drop(columns=["key", "id"])


def layer3_data(init_key: str, data_query=None, in_product=False):
    if in_product:
        key = init_key
    else:
        key = init_key + \
            md5(data_query.query.__str__().encode("utf-8")).hexdigest()
    content, status = StorageCache.get_pickle(key)
    if not status:
        logging.info(f"[FETCH] Reading {init_key} from DB")
        if in_product:
            content = get_product_type(init_key.upper())
        else:
            content = pd.DataFrame(data_query)
        StorageCache.set_pickle(key, content)
    return content

 # layer 3 Flooring


def l3_flooring(w: int) -> pd.DataFrame:
    flooring_key = f"flooring_plan_{w}"
    flooring, status = StorageCache.get_pickle(flooring_key)
    if not status:
        logging.info(f"[FETCH] Reading flooring {w} from DB")
        flooring = pd.DataFrame(
            Flooring.objects.filter(Q(week=w)).values())
        StorageCache.set_pickle(flooring_key, flooring)
    return flooring


def get_filtered_data(week, extra_data, filters=None, join_with_flooring=False):
    """Get filtered data from storage cache or db
    Output fields:
    site_id_id
    product_id
    id
    year
    week
    week_object_id
    first_date_of_week
    sold_units
    product_range
    product_range__value
    inventory
    sku
    gscn_site_name
    group
    group__value
    division
    division__value
    site_id
    city
    city__name
    account
    account__name
    zone
    zone__name
    region
    region__name
    country
    country__name
    INCHES
    LOAD
    """
    logging.info(f"[THREAD] fetching week {week}")

    # COMPUTE HASH FROM QUERYSET AND FILTERS
    queryset = WeeklySale.objects.filter(
        Q(week_object=week)).values()  # , many=True)

    filtered_key = "filtered_queries_" + \
        md5((f"{queryset.query.__str__()}{filters}{join_with_flooring}").encode(
            "utf-8")).hexdigest()
    try:
        content, status = StorageCache.get_pickle(filtered_key)
    except Exception as ex:
        logging.info(
            f"[THREAD] exception reading filtered key {filtered_key} for week {week}")
        status = False

    # IF AN ALREADY FILTERED DF IS CACHED, RETURN IT

    if status:
        return content

    key = "queries_"+md5(queryset.query.__str__().encode("utf-8")).hexdigest()
    content, status = StorageCache.get_pickle(key)

    # IF SALES DATA IS CACHED, LOAD IT
    logging.info("[THREAD] getting pickle joined data for week "+str(week))
    if status:
        df = content

    # ELSE LOAD DATA FROM DB
    else:
        df = pd.DataFrame(queryset)
        StorageCache.set_pickle(key, df)
    logging.info("[THREAD] got pickle sales data for week "+str(week))

    # define l3 extra data here
    products, pos, inches, load, flooring = extra_data

    #load = get_product_type("LOAD")

    logging.info("[THREAD] joining for week "+str(week))
    products = products.set_index("id").join(inches.set_index(
        "product_id")).join(load.set_index("product_id"))

    # JOIN SALES AND PRODUCT WITH SALES

    try:

        joined = df.set_index("product_id").join(products).reset_index().rename(columns={"index": "product_id"}).set_index(
            "site_id_id").join(pos.set_index("id")).reset_index().rename(columns={"index": "site_id_id"})

        logging.info("[THREAD] joined for week "+str(week))

        if join_with_flooring:
            #logging.info(f"[THREAD] reading flooring {week}")
            #flooring = pd.DataFrame(Flooring.objects.filter(Q(week=week)).values())

            if len(flooring) == 0:
                flooring["flooring_plan"] = 0.0
                logging.info(f"[THREAD] no flooring data for {week}")
            else:
                flooring = flooring.drop(columns=["id"])

                flooring = flooring.rename(
                    columns={"week_id": "week_object_id", "point_of_sale_id": "site_id_id"})

                flooring_index = ["week_object_id", "product_id", "site_id_id"]
                joined = joined.set_index(flooring_index).join(flooring.set_index(flooring_index)).rename(
                    columns={"target": "flooring_plan"}).reset_index().rename(columns={"index": "site_id_id"})

        joined = joined.rename(columns=adapter)

        # FILTER DATA BASED ON PERMISSIONS AND QUERY STRINGS

        if filters:

            logging.info("[THREAD] filtering for week "+str(week))
            joined = joined.query(filters)
            logging.info("[THREAD] filtered for week "+str(week))

        joined = joined.rename(columns={v: k for k, v in adapter.items()})

        # CACHE FILTERED DATA
        joined = joined.fillna(0)

        joined = joined.replace([np.inf, -np.inf], 0)

        #StorageCache.set_pickle(filtered_key, joined)
        logging.info(f"[THREAD] loaded {week}")
    except Exception as ex:

        print(f"Exception in week {week}: {ex}. {filtered_key} {key}")
    del inches, load, pos, products
    return joined


def get_filtered_data_in_range(min: int, max: int, filters, flooring: bool = True) -> pd.DataFrame:
    # LOAD POS AND PRODUCT DATA
    return get_filtered_data_v2(min, max, filters)

    products = layer3_data(data_query=products_query, init_key="products_")
    pos = layer3_data(data_query=pos_query, init_key="pos_")
    inches = layer3_data(init_key="inches", in_product=True)
    load = layer3_data(init_key="load", in_product=True)

    l3_extra_data = (
        products,
        pos,
        inches,
        load
    )

    data = list()
    threads = [Thread(target=get_filtered_data, args=(w, l3_extra_data+(l3_flooring(w),), filters, flooring))
               for w in range(min, max+1)]
    for thread in threads:
        thread.start()

    for thread in threads:
        data.append(thread.join())

    return pd.concat([pd.DataFrame(x) for x in data])


# =============================== new funcions data gets ===============================

# new function get filterd data
def get_filtered_data_flooring(week, extra_data, filters=None):
    logging.info(f"[THREAD] fetching week {week}")
    # define l3 extra data here
    products, pos, inches, load, week_data, df = extra_data
    df = df.drop(columns=["id"])

    logging.info("[THREAD] joining for week "+str(week))
    products = products.set_index("id").join(inches.set_index(
        "product_id")).join(load.set_index("product_id"))
    try:

        joined = df.set_index("product_id").join(products).reset_index().rename(columns={"index": "product_id"}).set_index("point_of_sale_id").join(pos.set_index("id")).reset_index().rename(columns={"index": "point_of_sale_id"}).set_index("week_id").join(week_data.set_index("id")).reset_index().rename(columns={"index": "week_id"}).rename(
            columns={"target": "flooring_plan"}).reset_index()

        filtered_key = "filtered_queries_" + \
            md5((f"{joined.query.__str__()}{filters}").encode(
                "utf-8")).hexdigest()

        try:
            content, status = StorageCache.get_pickle(filtered_key)
        except Exception as ex:
            logging.info(
                f"[THREAD] exception reading filtered key {filtered_key} for week {week}")
            status = False

        if status:
            return content

        key = "queries_" + \
            md5(joined.query.__str__().encode("utf-8")).hexdigest()
        content, status = StorageCache.get_pickle(key)

        joined = joined.rename(columns=adapter)
        logging.info("[THREAD] getting pickle joined data for week "+str(week))
        if status:
            joined = content
        # FILTER DATA BASED ON PERMISSIONS AND QUERY STRINGS
        if filters:

            logging.info("[THREAD] filtering for week "+str(week))
            joined = joined.query(filters)
            logging.info("[THREAD] filtered for week "+str(week))

        joined = joined.rename(columns={v: k for k, v in adapter.items()})

        # CACHE FILTERED DATA
        joined = joined.fillna(0)

        joined = joined.replace([np.inf, -np.inf], 0)

        StorageCache.set_pickle(filtered_key, joined)
        logging.info(f"[THREAD] loaded {week}")
    except Exception as ex:

        print(f"Exception in flooring week {week}: {ex}. {filtered_key} {key}")
    del inches, load, pos, products, week

    return joined


def get_filtered_data_in_range_fp(min: int, max: int, filters, flooring: bool = True) -> pd.DataFrame:

    # LOAD POS AND PRODUCT DATA
    product_fields = ("id", "group", "group__value",
                      "division", "sku", "division__value", "product_range", "product_range__value")
    pos_fields = ("id", "site_id", "gscn_site_name", "city", "city__name", "account", "account__name", "zone", "zone__name",
                  "region", "region__name", "country", "country__name", "custom_account", "custom_account__name")
    week_fields = ("id", "week", "year")

    products_query = Product.objects.all().values(*product_fields)
    pos_query = PointOfSale.objects.all().values(*pos_fields)
    week_query = Week.objects.all().values(*week_fields)

    products = layer3_data(data_query=products_query, init_key="products_")
    pos = layer3_data(data_query=pos_query, init_key="pos_")
    inches = layer3_data(init_key="inches", in_product=True)
    load = layer3_data(init_key="load", in_product=True)

    # dataframe week
    week = pd.DataFrame(week_query)

    l3_extra_data = (
        products,
        pos,
        inches,
        load,
        week
    )

    data = list()
    threads = [Thread(target=get_filtered_data_flooring, args=(w, l3_extra_data+(l3_flooring(w),), filters))
               for w in range(min, max+1)]
    for thread in threads:
        thread.start()

    for thread in threads:
        data.append(thread.join())

    return pd.concat([pd.DataFrame(x) for x in data])

# optimization phase 1

    return [weeklysales[w][0][weeklysales[w][0].filter(filters)] for w in range(len(weeklysales)) if w >= 185 and w <= 196]
