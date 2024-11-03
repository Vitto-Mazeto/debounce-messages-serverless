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

# Set up DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)

def invoke_lambda(phone_number, message, last_update):
    """Invoke another Lambda function to process the message."""
    lambda_client = boto3.client('lambda')
    payload = {
        'phone_number': phone_number,
        'message': message,
        'last_update': last_update
    }

    try:
        response = lambda_client.invoke(
            FunctionName=PROCESSING_LAMBDA_FUNCTION,
            InvocationType='Event',  # Asynchronous invocation
            Payload=json.dumps(payload)
        )
        logger.info(f'Invoked processing Lambda with response: {response}')
    except Exception as e:
        logger.error(f'Failed to invoke processing Lambda: {str(e)}')

def lambda_handler(event, context):
    logger.info('Received event: %s', json.dumps(event))
    phone_number = event['phone_number']
    message = event['message']
    last_update = event['last_update']
    

    # Double-check if the message is still the most recent one
    response = table.get_item(Key={'phone_number': phone_number})

    if 'Item' not in response or response['Item']['last_update'] != last_update:
        logger.info('Message was updated, skipping processing for %s', phone_number)
        return {
            'statusCode': 200,
            'body': json.dumps('Message was updated, skipping processing')
        }

    logger.info('Processing message: %s', message)
    print("Lambda is commented")
    # invoke_lambda(phone_number, message, last_update)

    # After sending, delete the message from DynamoDB
    table.delete_item(Key={'phone_number': phone_number})
    logger.info('Message from %s processed and deleted from DynamoDB', phone_number)

    return {
        'statusCode': 200,
        'body': json.dumps('Message processed successfully')
    }
