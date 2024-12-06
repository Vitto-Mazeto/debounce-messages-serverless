import json
import os
import logging
import requests

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# https://42pensads1.execute-api.us-east-1.amazonaws.com/debouncer-post-message?appId=patricia

# Get environment variables
EVOLUTION_API_BASE_URL = os.environ.get('EVOLUTION_API_BASE_URL')  # {"patricia": "http://54.80.129.243:8080/message/sendText/TesteNutrix", "app2": "https://app2.com"}
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY')

def send_text_message(phone, message, instance):
    """Envia mensagem via Evolution API"""
    api_url = f"{EVOLUTION_API_BASE_URL}/{instance}"
    headers = {"Content-Type": "application/json", "apikey": EVOLUTION_API_KEY}
    
    payload = {
        "number": phone,
        "text": message
    }

    response = requests.post(api_url, json=payload, headers=headers)

    if str(response.status_code).startswith('20'):
        logger.info('Message sent successfully to %s', phone)
    else:
        logger.error('Failed to send message: %s', response.text)

def lambda_handler(event, context):
    logger.info('Received event: %s', json.dumps(event))

    for record in event['Records']:
        # Decodifica a mensagem da fila
        message = json.loads(record['body'])
        
        instance = message.get('instance')
        phone_number = message.get('phone_number')
        message_to_send = message.get('message_to_send')

        logger.info('Processing message for instance: %s, phone_number: %s', instance, phone_number)

        try:
            send_text_message(phone_number, message_to_send, instance)
        except Exception as e:
            logger.error(f'Error sending message to {phone_number}: {str(e)}')

    return {
        'statusCode': 200,
        'body': json.dumps('Messages processed successfully')
    }
