from ast import Return
import pandas as pd
import pickle
from service import logging, Thread
from api.settings import STORAGE_CACHE_ENABLED
from api.settings import s3
from botocore.exceptions import ClientError
class StorageCache():

    @classmethod
    def set_pickle(cls, key, object):
        def save():
            if not STORAGE_CACHE_ENABLED:
                return
            pkl_file = open("./cache/" + key + ".pkl", 'wb')
            pickle.dump(object, pkl_file)
            logging.info(f"[STORAGE] Saved {key}")
            pkl_file.close()

        # Thread(save).start()
        save()

    @classmethod
    def get_pickle(cls, key):
        if not STORAGE_CACHE_ENABLED:
            return False, False
        obj = None
        try:

            f = open(f"./cache/{key}.pkl", 'rb')
            obj = pickle.load(f)
            f.close()
        except FileNotFoundError:
            logging.info(f"[STORAGE] file {key}.pkl doesn't exist")
            return obj, False
        except Exception as ex:
            logging.info(f"[STORAGE] error loading file {key}.pkl")
            return obj, False
            
        logging.info(f"[STORAGE] found {key}")
        return obj, True

    @classmethod
    def get_from_s3(cls,key):
        if not STORAGE_CACHE_ENABLED:
            return False, False
        data = cls.get_pickle(key)

        # if data[1]:
        #     return data

        obj = None
        try:
            with open("./cache/"+key+".pkl", 'wb') as f:
                s3.download_fileobj("etlgscmsales","weeklysales/"+key+".pkl", f)
                logging.info(f"[STORAGE/S3] downloaded {key}")
        except ClientError as ex:
            if "404" in str(ex):
                logging.info(f"[STORAGE/S3] Error not found {key}")


        return cls.get_pickle(key)