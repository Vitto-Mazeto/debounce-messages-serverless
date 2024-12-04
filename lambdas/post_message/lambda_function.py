import json
import boto3
import time
import os
import logging
from decimal import Decimal

from strategy import ZApiStrategy, EvolutionStrategy

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
step_functions = boto3.client('stepfunctions')

def get_strategy(api_type: str):
    if api_type == 'z-api':
        return ZApiStrategy()
    if api_type == 'evolution':
        return EvolutionStrategy()
    raise ValueError(f"Unknown API type: {api_type}")

def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f'Type {obj.__class__.__name__} not serializable')

def get_existing_message(app_id, phone_number):
    """Retrieve an existing message from DynamoDB."""
    try:
        return table.get_item(Key={'app_id': app_id, 'phone_number': phone_number})
    except Exception as e:
        logger.error(f"Failed to retrieve message for app_id {app_id} and phone {phone_number}: {str(e)}")
        raise

def update_existing_message(app_id, phone_number, existing_message, new_text, timestamp):
    """Update the existing message in DynamoDB."""
    logger.info(f"Updating existing message for {phone_number} in app {app_id}")
    existing_text = existing_message.get('text', '')
    concatenated_text = f"{existing_text} {new_text}".strip()

    try:
        return table.update_item(
            Key={'app_id': app_id, 'phone_number': phone_number},
            UpdateExpression="SET #txt = :t, last_update = :lu",
            ExpressionAttributeNames={'#txt': 'text'},
            ExpressionAttributeValues={
                ':t': concatenated_text,
                ':lu': timestamp
            },
            ReturnValues="ALL_NEW"
        )['Attributes']
    except Exception as e:
        logger.error(f"Failed to update message for app_id {app_id} and phone {phone_number}: {str(e)}")
        raise

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
        except Exception as e:
            logger.error(f"Failed to cancel execution {execution_arn}: {str(e)}")

def create_new_message(app_id, phone_number, text, timestamp):
    """Create a new message entry in DynamoDB."""
    logger.info(f"Creating new message for {phone_number} in app {app_id}")
    try:
        table.put_item(
            Item={
                'app_id': app_id,
                'phone_number': phone_number,
                'text': text,
                'last_update': timestamp
            }
        )
        return {'text': text, 'last_update': timestamp}
    except Exception as e:
        logger.error(f"Failed to create new message for app_id {app_id} and phone {phone_number}: {str(e)}")
        raise

def start_step_function_execution(app_id, phone_number, message_text, last_update):
    """Start a new Step Functions execution."""
    try:
        execution = step_functions.start_execution(
            stateMachineArn=os.environ['STEP_FUNCTION_ARN'],
            input=json.dumps({
                'app_id': app_id,
                'phone_number': phone_number,
                'message': message_text,
                'last_update': last_update
            }, default=decimal_to_float)
        )
        return execution['executionArn']
    except Exception as e:
        logger.error(f"Failed to start Step Function execution for app_id {app_id} and phone {phone_number}: {str(e)}")
        raise

def lambda_handler(event, context):
    logger.info('Received event: %s', json.dumps(event))
    """Lambda function entry point."""
    try:
        # Obter app_id e processar a mensagem
        app_id = event['queryStringParameters'].get('appId')
        message = json.loads(event['body'])
        strategy = get_strategy("evolution")

        phone_number, text = strategy.process_message(message)
        timestamp = int(time.time())
        logger.info('Received message from %s in app %s: %s', phone_number, app_id, text)

        # Obter ou atualizar a mensagem existente
        response = get_existing_message(app_id, phone_number)
        if 'Item' in response:
            existing_message = response['Item']
            logger.info('Existing message found: %s', existing_message)
            cancel_existing_execution(existing_message)
            updated_message = update_existing_message(app_id, phone_number, existing_message, text, timestamp)
        else:
            updated_message = create_new_message(app_id, phone_number, text, timestamp)

        # Iniciar execução do Step Functions
        execution_arn = start_step_function_execution(
            app_id,
            phone_number,
            updated_message['text'],
            updated_message['last_update']
        )

        # Atualizar a execução na tabela
        table.update_item(
            Key={'app_id': app_id, 'phone_number': phone_number},
            UpdateExpression="SET execution_arn = :arn",
            ExpressionAttributeValues={':arn': execution_arn}
        )

        logger.info('Message received and Step Functions execution started for %s in app %s', phone_number, app_id)

        return {
            'statusCode': 200,
            'body': json.dumps('Message received and Step Functions execution started')
        }
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps('Internal server error')
        }
