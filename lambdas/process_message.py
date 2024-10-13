import json
import boto3
import os
import logging
import requests

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get environment variables
DYNAMODB_TABLE = os.environ['DYNAMODB_TABLE']
PROCESSING_LAMBDA_FUNCTION = os.environ.get('PROCESSING_LAMBDA_FUNCTION')
API_URL = os.environ.get('API_URL')
SEND_TO_API = os.environ.get('SEND_TO_API', 'false').lower()

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

def send_to_api(phone_number, message, last_update):
    """Send the message to an external API."""
    payload = {
        'phone_number': phone_number,
        'message': message,
        'last_update': last_update
    }

    try:
        response = requests.post(API_URL, json=payload)
        response.raise_for_status()  # Raises an error if the response is not 2xx
        logger.info('Successfully sent message to API: %s', response.json())
    except requests.exceptions.RequestException as e:
        logger.error(f'Error sending message to API: {str(e)}')

def lambda_handler(event, context):
    phone_number = event['phone_number']
    message = event['message']
    last_update = event['last_update']
    
    logger.info('Received event: %s', json.dumps(event))

    # Double-check if the message is still the most recent one
    response = table.get_item(Key={'phone_number': phone_number})

    if 'Item' not in response or response['Item']['last_update'] != last_update:
        logger.info('Message was updated, skipping processing for %s', phone_number)
        return {
            'statusCode': 200,
            'body': json.dumps('Message was updated, skipping processing')
        }

    logger.info('Processing message: %s', message)

    # Choose to either send to another Lambda or to an API
    if SEND_TO_API == 'true' and API_URL:
        send_to_api(phone_number, message, last_update)
    elif PROCESSING_LAMBDA_FUNCTION:
        invoke_lambda(phone_number, message, last_update)

    # After sending, delete the message from DynamoDB
    table.delete_item(Key={'phone_number': phone_number})
    logger.info('Message from %s processed and deleted from DynamoDB', phone_number)

    return {
        'statusCode': 200,
        'body': json.dumps('Message processed successfully')
    }
