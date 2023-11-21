#from rest_framework.response import Response

from service import Thread,logging
from api.settings import LOG_RESOURCES
import os

from time import sleep


class ResourceMonitorMiddleware:

    

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # Code that is executed in each request before the view is called

        response = self.get_response(request)

        # Code that is executed in each request after the view is called
        return response

    def log_resources(self):
        for _ in range(3):
            try:
                logging.info("[RESOURCE LOG] LOGGING")
                from reports.models import MonitorCPU,MonitorRAM
                import psutil
                import requests
                
                MonitorRAM(
                    gb=psutil.virtual_memory().used / 1000000000,
                    value=psutil.virtual_memory().percent, 
                    env=os.environ.get("PYTHON_ENV", "local"),
                    ip = requests.get("https://checkip.amazonaws.com/").content.decode("utf-8")[:-1]
                ).save()
                MonitorCPU(
                    value=psutil.cpu_percent(0), 
                    env=os.environ.get("PYTHON_ENV", "local"),
                    ip = requests.get("https://checkip.amazonaws.com/").content.decode("utf-8")[:-1]
                ).save()
            except Exception as ex:
                print(ex)
            sleep(6)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if LOG_RESOURCES:
            Thread(target = self.log_resources).start()
        
    def process_template_response(self, request, response):
        return response