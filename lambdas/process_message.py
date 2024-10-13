import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

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
    
    # Process the message here
    logger.info('Processing message from %s: %s', phone_number, message)
    
    # After processing, delete the message from DynamoDB
    table.delete_item(Key={'phone_number': phone_number})
    logger.info('Message from %s processed and deleted from DynamoDB', phone_number)

    return {
        'statusCode': 200,
        'body': json.dumps('Message processed successfully')
    }
