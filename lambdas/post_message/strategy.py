from lambdas.post_message.extract_text_from_base64 import extract_text_from_base64


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

        return phone_number, text

    @staticmethod
    def _extract_phone_number(data):
        return data['key']['remoteJid'].split('@')[0]

    def _process_message_content(self, content):
        if 'conversation' in content:
            return self._extract_text(content)

        if 'audioMessage' in content:
            return self._extract_text_from_audio(content)

        # TODO: O áudio dando certo, coloca aqui a lógica para processar imagens

        return None

    @staticmethod
    def _extract_text(content):
        return content.get('conversation')

    @staticmethod
    def _extract_text_from_audio(content):
        base_64 = content.get('base64')
        return extract_text_from_base64(base_64)
