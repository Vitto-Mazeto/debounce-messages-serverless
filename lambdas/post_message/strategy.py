from lambdas.post_message.text_extraction_strategy import AudioExtractionStrategy, ImageExtractionStrategy


class MessageStrategy:
    def process_message(self, message):
        raise NotImplementedError("This method should be overridden by subclasses")


class ZApiStrategy(MessageStrategy):
    def process_message(self, message):
        phone_number = message['phone']
        text = message['text']['message']

        return phone_number, text

class EvolutionStrategy(MessageStrategy):
    def process_message(self, message):
        data = message.get('data', {})
        content = data.get('message', {})

        if data.get('key', {}).get('fromMe'):
            return None, None

        phone_number = self._extract_phone_number(data)
        text = self._process_message_content(content)
        instance = self._extract_instance(message)

        return phone_number, text, instance

    @staticmethod
    def _extract_phone_number(data):
        return data['key']['remoteJid'].split('@')[0]

    @staticmethod
    def _extract_instance(message):
        return message.get('instance')

    def _process_message_content(self, content):
        if 'conversation' in content:
            return self._extract_text(content)

        if 'audioMessage' in content:
            return self._extract_text_from_base64('audioMessage', content)

        if 'imageMessage' in content:
            return self._extract_text_from_base64('imageMessage', content)

        return None

    @staticmethod
    def _extract_text(content):
        return content.get('conversation')

    @staticmethod
    def _extract_text_from_base64(message_type, content):
        if message_type == 'audioMessage':
            base_64 = content.get('base64')
            strategy = AudioExtractionStrategy()
            return strategy.extract_text(base_64)

        if message_type == 'imageMessage':
            base_64 = content['imageMessage'].get('base64')
            strategy = ImageExtractionStrategy()
            return strategy.extract_text(base_64)

        raise ValueError(f"Unknown message type: {message_type}")
