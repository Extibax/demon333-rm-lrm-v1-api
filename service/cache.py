from redis import Redis
from redis import exceptions
from . import logging
from . import Thread
import os


class ElasticCache():

    def __init__(self, host: str, port: int, enabled: bool = True, password: str = None):
        self.enabled = enabled
        if self.enabled:

            self.host = host
            self.port = port

            if password:
                logging.info(
                    f"[ELASTICACHE] Connecting to Elasticache using credentials {host}:{port} and password {password}")
                self.password = password
                self.client = Redis(
                    host=host,
                    port=port,
                    password=password,
                )
            else:
                logging.info(
                    f"[ELASTICACHE] Connecting to Elasticache using credentials {host}:{port}")
                self.client = Redis(
                    host=host,
                    port=port,
                )
            try:
                status = self.client.get("CONNECTION_STATUS").decode("utf-8")
                logging.info("[ELASTICACHE] connection status: " + status)
            except Exception as ex:
                logging.info(
                    "[ELASTICACHE] Can not stablish Elasticache connection. " + str(ex))

    def get_redis_key(self, key):

        return f"{os.environ.get('PYTHON_ENV','dev')}:{key}"

    def __set__(self, key, value):
        try:
            self.client.set(self.get_redis_key(key), value)
            logging.info(f"[ELASTICACHE] saved {key}")
        except exceptions.ConnectionError:
            return None

    def set(self, key: str, value: str):
        # client cannot wait until cache is completely saved in order to get a response.
        # If response is to large this can take up to 20 secs

        if self.enabled:
            print("value",value)
            Thread(
                target=self.__set__,
                args=(key, value)).start()

    def get(self, key: str):
        if self.enabled:
            try:
                logging.info(f"[ELASTICACHE] looking for {key}")
                data = self.client.get(self.get_redis_key(key))
                logging.info(
                    f"[ELASTICACHE] data {key} found on cache {str(data)[:10]}....{str(data)[-10:]}")
                return data
            except exceptions.ConnectionError:
                logging.info(f"[ELASTICACHE] Connection error")

                return None
