import json
import boto3
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client('lambda')
sqs_client = boto3.client('sqs')
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
QUEUE_URL = config['QUEUE_URL']

def lambda_handler(event, context):
    logger.info('Received event: %s', json.dumps(event, indent=2))

    for record in event['Records']:
        logger.info('Processing record: %s', json.dumps(record, indent=2))

        try:
            body = json.loads(record['body'])
        except json.JSONDecodeError as error:
            logger.error('Error parsing record body: %s', error)
            continue

        if 'Records' in body and body['Records'][0]['eventSource'] == 'aws:s3':
            s3_event = body['Records'][0]
            logger.info('S3 event: %s', json.dumps(s3_event, indent=2))

            if s3_event['eventName'] == 's3:TestEvent':
                delete_params = {
                    'QueueUrl': QUEUE_URL,
                    'ReceiptHandle': record['receiptHandle']
                }
                try:
                    sqs_client.delete_message(**delete_params)
                    logger.info('Test event deleted from SQS queue')
                except Exception as error:
                    logger.error('Error deleting test event from SQS queue: %s', error)
                continue

            payload = {
                'eventVersion': s3_event.get('eventVersion'),
                'eventSource': s3_event.get('eventSource'),
                'awsRegion': s3_event.get('awsRegion'),
                'eventTime': s3_event.get('eventTime'),
                'eventName': s3_event.get('eventName'),
                'userIdentity': s3_event.get('userIdentity'),
                'requestParameters': s3_event.get('requestParameters'),
                'responseElements': s3_event.get('responseElements'),
                's3': {
                    's3SchemaVersion': s3_event.get('s3', {}).get('s3SchemaVersion'),
                    'configurationId': s3_event.get('s3', {}).get('configurationId'),
                    'bucket': s3_event.get('s3', {}).get('bucket'),
                    'object': s3_event.get('s3', {}).get('object')
                }
            }
            
            logger.info('Prepared payload: %s', json.dumps(payload, indent=2))

            invoke_params = {
                'FunctionName': 'fyrestream-transcoder-invoker',
                'InvocationType': 'Event',
                'Payload': json.dumps(payload)
            }

            try:
                response = lambda_client.invoke(**invoke_params)
                logger.info('Successfully invoked Transcoder Invoker Function. StatusCode: %s, ExecutedVersion: %s',
                            response.get('StatusCode'), response.get('ExecutedVersion'))
            except Exception as error:
                logger.error('Error invoking Transcoder Invoker Function: %s', str(error))
        else:
            logger.warning('Record does not contain S3 event: %s', json.dumps(record, indent=2))

    return f"Processed {len(event['Records'])} messages."
