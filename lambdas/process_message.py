import json
import boto3
import os

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def lambda_handler(event, context):
    phone_number = event['phone_number']
    message = event['message']
    last_update = event['last_update']
    
    # Double-check if the message is still the most recent one
    response = table.get_item(Key={'phone_number': phone_number})
    
    if 'Item' not in response or response['Item']['last_update'] != last_update:
        return {
            'statusCode': 200,
            'body': json.dumps('Message was updated, skipping processing')
        }
    
    # Process the message here
    # For example, send it to another service or perform some analysis
    print(f"Processing message from {phone_number}: {message}")
    
    # After processing, delete the message from DynamoDB
    table.delete_item(Key={'phone_number': phone_number})
    
    return {
        'statusCode': 200,
        'body': json.dumps('Message processed successfully')
    }