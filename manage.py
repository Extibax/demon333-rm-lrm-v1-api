#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import pandas as pd
import boto3
import time
from api.settings import s3
from service import Thread

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'api.settings')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


def fetch_l2():
    while True:
        # LOAD L2 CACHE FILE INVENTORY
        file_names = os.listdir("./cache")
        l2_local_files = pd.DataFrame({"file": file_names, "origin": [
            "local" for _ in file_names]})
        l2_local_files = l2_local_files[l2_local_files["file"].str[:16]
                                        == "filtered_queries"]

        # LOAD REMOTE L2 CACHE REPOSITORY

        paginator = s3.get_paginator('list_objects_v2')
        response = [x for x in paginator.paginate(
            Bucket='lrm-cache-layers',
            PaginationConfig={
                'MaxItems': 1000,
                'PageSize': 1,
            }
        )]
        s3_names = [x["Contents"][0]["Key"] for x in response]
        l2_remote_files = pd.DataFrame(
            {"file": s3_names, "origin": ["remote" for _ in s3_names]})
        l2_remote_files = l2_remote_files[l2_remote_files["file"].str[:16]
                                          == "filtered_queries"]
        cross = l2_remote_files.set_index("file").join(l2_local_files.set_index(
            "file"), rsuffix="_local", lsuffix="_remote", how="outer").reset_index()
        missing_in_local = cross[cross.origin_local.isna()]
        missing_in_remote = cross[cross.origin_remote.isna()]
        for _, series in missing_in_local.iterrows():
            with open("./cache/"+series["file"], 'wb') as f:
                s3.download_fileobj("lrm-cache-layers", series["file"], f)
                print("saved", series["file"])
        for _, series in missing_in_remote.iterrows():
            s3.upload_file(
                './cache/'+series["file"], 'lrm-cache-layers', series["file"])
            print("uploaded", series["file"])
        time.sleep(30)



if __name__ == '__main__':

    # Thread(target=fetch_l2).start()
    

    main()