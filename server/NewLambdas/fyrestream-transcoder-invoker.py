import json
import boto3
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ecs_client = boto3.client('ecs')
secrets_client = boto3.client('secretsmanager')

SECRET_NAME = os.environ['SECRET_NAME']

def get_secret():
    try:
        get_secret_value_response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
        return json.loads(get_secret_value_response['SecretString'])
    except Exception as e:
        logger.error(f"Error retrieving secret: {str(e)}")
        raise e

config = get_secret()
CLUSTER_ARN = config['CLUSTER_ARN']
TASK_DEFINITION_ARN = config['TASK_DEFINITION_ARN']
SUBNETS = config['SUBNETS'].split(',')
SECURITY_GROUPS = [config['SECURITY_GROUP']]

def json_serial(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def launch_ecs_task(ecs_params):
    try:
        ecs_response = ecs_client.run_task(**ecs_params)
        logger.info('ECS task started: %s', json.dumps(ecs_response, indent=2, default=json_serial))
    except Exception as error:
        logger.error('Error starting ECS task: %s', str(error))

def lambda_handler(event, context):
    logger.info('Received event: %s', json.dumps(event, indent=2))
    
    s3_event = event.get('s3', {})
    bucket_name = s3_event.get('bucket', {}).get('name')
    object_key = s3_event.get('object', {}).get('key')
    
    if not bucket_name or not object_key:
        logger.error('Missing bucket name or object key in the event')
        return

    ecs_params = {
        'cluster': CLUSTER_ARN,
        'taskDefinition': TASK_DEFINITION_ARN,
        'launchType': 'FARGATE',
        'networkConfiguration': {
            'awsvpcConfiguration': {
                'subnets': SUBNETS,
                'securityGroups': SECURITY_GROUPS,
                'assignPublicIp': 'ENABLED'
            }
        },
        'overrides': {
            'containerOverrides': [
                {
                    'name': 'fyrestream-transcoder',
                    'environment': [
                        {'name': 'BUCKET_NAME', 'value': bucket_name},
                        {'name': 'KEY', 'value': object_key}
                    ]
                }
            ]
        }
    }
    
    with ThreadPoolExecutor() as executor:
        executor.submit(launch_ecs_task, ecs_params)

    logger.info(f"Initiated asynchronous ECS task launch for object {object_key} in bucket {bucket_name}")
    return f"Processed event for object {object_key} in bucket {bucket_name}"
