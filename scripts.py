import boto3, os
from typing import List
from service import logging
import sys
ecs = boto3.client(
    'ecs',
    aws_access_key_id=os.environ.get("ACCESS_KEY", "AKIASWI4AZITDQ7SCW2G"),
    aws_secret_access_key=os.environ.get(
        "SECRET_KEY", "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"),
    region_name="us-east-1"
)

def list_clusters():
    response = ecs.list_clusters()
    return response

def list_tasks(cluster):
    response = ecs.list_tasks(
        cluster=cluster,
        #serviceName='lrm',
        desiredStatus='RUNNING',
        launchType='FARGATE'
    )
    return response

def stop_tasks(cluster, task_id, reason):    
    response = ecs.stop_task(
        cluster=cluster,
        task=task_id,
        reason=reason
    )
    return response

def describe_cluster(cluster_list:List[str]):
    response = ecs.describe_clusters(
    clusters=cluster_list
    )
    return response


cluster_name = ['lrm-v2-'+sys.argv[1]]
logging.info("[SCRIPT] Getting cluster")
res_clusters = describe_cluster(cluster_name)
##foreach cluster get tasks
if len(res_clusters["clusters"]) > 0:
    for cluster in res_clusters["clusters"]:
        logging.info("[SCRIPT] Getting tasks")
        res_tasks = list_tasks(cluster["clusterArn"])
        if len(res_tasks["taskArns"]) > 0:
            ##foreach task close it
            for task in res_tasks["taskArns"]:        
                stop_tasks(cluster["clusterArn"], task, 'new backend version')
                logging.info("[SCRIPT] Closing task: "+ task)
        else:
            print("There is no task available")
else:
    print(f"The cluster {cluster_name[0]} is not available")

logging.info("[SCRIPT] Process Completed")