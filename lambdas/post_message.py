import json
import boto3
import time
import os
import logging
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
step_functions = boto3.client('stepfunctions')


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f'Type {obj.__class__.__name__} not serializable')


def get_existing_message(phone_number):
    """Retrieve an existing message from DynamoDB."""
    return table.get_item(Key={'phone_number': phone_number})


def update_existing_message(phone_number, existing_message, new_text, timestamp):
    """Update the existing message in DynamoDB."""
    logger.info(f"Updating existing message for {phone_number}")
    existing_text = existing_message.get('text', '')
    concatenated_text = f"{existing_text} {new_text}".strip()

    return table.update_item(
        Key={'phone_number': phone_number},
        UpdateExpression="SET #txt = :t, last_update = :lu",
        ExpressionAttributeNames={'#txt': 'text'},
        ExpressionAttributeValues={
            ':t': concatenated_text,
            ':lu': timestamp
        },
        ReturnValues="ALL_NEW"
    )['Attributes']


def cancel_existing_execution(existing_message):
    """Cancel an existing Step Functions execution if it exists."""
    if 'execution_arn' in existing_message:
        execution_arn = existing_message['execution_arn']
        logger.info(f"Cancelling existing execution {execution_arn}")
        try:
            step_functions.stop_execution(
                executionArn=execution_arn,
                error='NewMessageReceived',
                cause='A new message was received, cancelling processing.'
            )
        except step_functions.exceptions.ExecutionDoesNotExist:
            logger.warning(f"Execution {execution_arn} does not exist, might have completed already.")


def create_new_message(phone_number, text, timestamp):
    """Create a new message entry in DynamoDB."""
    logger.info(f"Creating new message for {phone_number}")
    table.put_item(
        Item={
            'phone_number': phone_number,
            'text': text,
            'last_update': timestamp
        }
    )
    return {'text': text, 'last_update': timestamp}


def start_step_function_execution(phone_number, message_text, last_update):
    """Start a new Step Functions execution."""
    execution = step_functions.start_execution(
        stateMachineArn=os.environ['STEP_FUNCTION_ARN'],
        input=json.dumps({
            'phone_number': phone_number,
            'message': message_text,
            'last_update': last_update
        }, default=decimal_to_float)
    )
    return execution['executionArn']


def lambda_handler(event, context):
    """Lambda function entry point."""
    message = json.loads(event['body'])
    phone_number = message['phoneNumber']
    text = message['message']
    timestamp = int(time.time())

    response = get_existing_message(phone_number)

    if 'Item' in response:
        existing_message = response['Item']
        cancel_existing_execution(existing_message)
        updated_message = update_existing_message(phone_number, existing_message, text, timestamp)
    else:
        updated_message = create_new_message(phone_number, text, timestamp)

    execution_arn = start_step_function_execution(
        phone_number,
        updated_message['text'],
        updated_message['last_update']
    )

    table.update_item(
        Key={'phone_number': phone_number},
        UpdateExpression="SET execution_arn = :arn",
        ExpressionAttributeValues={':arn': execution_arn}
    )

    logger.info('Message received and Step Functions execution started for %s', phone_number)

    return {
        'statusCode': 200,
        'body': json.dumps('Message received and Step Functions execution started')
    }
