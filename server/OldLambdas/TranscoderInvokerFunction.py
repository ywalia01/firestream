import json
import boto3
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
ecs_client = boto3.client('ecs')

CLUSTER_ARN = 'arn:aws:ecs:us-east-1:492025348070:cluster/dev'
TASK_DEFINITION_ARN = 'arn:aws:ecs:us-east-1:492025348070:task-definition/firestream-transcoder'
SUBNETS = ['subnet-0014f6d47f71a87bd', 'subnet-0028ffb7fb9b2e528', 'subnet-0c582a5e06ff22802']
SECURITY_GROUPS = ['sg-0e95614f453d5b26e']

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
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
    
    # Extract S3 details directly from the event
    s3_event = event.get('s3', {})
    bucket_name = s3_event.get('bucket', {}).get('name')
    object_key = s3_event.get('object', {}).get('key')
    
    if not bucket_name or not object_key:
        logger.error('Missing bucket name or object key in the event')
        return

    # Prepare ECS task parameters
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
                    'name': 'firestream-transcoder',
                    'environment': [
                        {'name': 'BUCKET_NAME', 'value': bucket_name},
                        {'name': 'KEY', 'value': object_key}
                    ]
                }
            ]
        }
    }
    
    # Launch ECS task asynchronously
    with ThreadPoolExecutor() as executor:
        executor.submit(launch_ecs_task, ecs_params)

    logger.info(f"Initiated asynchronous ECS task launch for object {object_key} in bucket {bucket_name}")
    return f"Processed event for object {object_key} in bucket {bucket_name}"