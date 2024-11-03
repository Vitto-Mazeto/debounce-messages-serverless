import json
import boto3
import os
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
PROCESSING_LAMBDA_FUNCTION = os.environ.get('PROCESSING_LAMBDA_FUNCTION')
PROCESSING_LAMBDAS_MAP = json.loads(os.environ.get('PROCESSING_LAMBDAS_MAP', '{}'))

# Set up DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)

def invoke_lambda(app_id, phone_number, message, last_update):
    """Invoke another Lambda function to process the message."""
    lambda_client = boto3.client('lambda')
    payload = {
        'phone_number': phone_number,
        'message': message,
        'last_update': last_update
    }

    target_lambda_function = PROCESSING_LAMBDAS_MAP.get(app_id)
    if not target_lambda_function:
        logger.error(f'No processing Lambda configured for app_id {app_id}')
        return

    try:
        response = lambda_client.invoke(
            FunctionName=target_lambda_function,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        logger.info(f'Invoked Lambda for app_id {app_id} with response: {response}')
    except Exception as e:
        logger.error(f'Failed to invoke Lambda for app_id {app_id}: {str(e)}')

def lambda_handler(event, context):
    logger.info('Received event: %s', json.dumps(event))
    
    app_id = event['app_id']
    phone_number = event['phone_number']
    message = event['message']
    last_update = event['last_update']

    # Double-check if the message is still the most recent one
    response = table.get_item(Key={'app_id': app_id, 'phone_number': phone_number})

    if 'Item' not in response or response['Item']['last_update'] != last_update:
        logger.info('Message was updated, skipping processing for %s', phone_number)
        return {
            'statusCode': 200,
            'body': json.dumps('Message was updated, skipping processing')
        }

    logger.info('Processing message: %s', message)
    
    invoke_lambda(app_id, phone_number, message, last_update)

    # After sending, delete the message from DynamoDB
    try:
        table.delete_item(Key={'app_id': app_id, 'phone_number': phone_number})
        logger.info('Message from app %s and phone number %s processed and deleted from DynamoDB', app_id, phone_number)
    except Exception as e:
        logger.error(f'Failed to delete item for app {app_id} and phone number {phone_number}: {str(e)}')

    return {
        'statusCode': 200,
        'body': json.dumps('Message processed successfully')
    }
