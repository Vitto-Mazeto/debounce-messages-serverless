import io
import base64
import os
from abc import ABC, abstractmethod

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class TextExtractionStrategy(ABC):
    def __init__(self):
        self.client = OpenAI()

    @abstractmethod
    def extract_text(self, base_64):
        raise NotImplementedError("This method should be overridden by subclasses")

    @staticmethod
    def _handle_extraction_error():
        return 'Escreva isso sem nenhuma explicação extra e sem as aspas: "Não consigo compreender a mídia no momento, poderia escrever o que deseja por favor?"'


class AudioExtractionStrategy(TextExtractionStrategy):
    def extract_text(self, base_64):
        if not base_64:
            return ''

        try:
            decoded_audio = base64.b64decode(base_64)

            audio_file = io.BytesIO(decoded_audio)
            audio_file.name = 'audio.mp3'

            transcript = self.client.audio.transcriptions.create(
                model=os.getenv('OPENAI_LLM_MODEL_NAME'),
                file=audio_file,
                language='pt'
            )

            return transcript.text
        except Exception as e:
            print(f'Error during audio transcription: {e}')
            return self._handle_extraction_error()


class ImageExtractionStrategy(TextExtractionStrategy):
    def extract_text(self, base_64):
        if not base_64:
            return ''

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Descreva o que está nessa imagem. Caso tenha texto, diga o que está escrito.",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base_64}"
                                },
                            },
                        ],
                    },
                ],
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f'Error during image text extraction: {e}')
            return self._handle_extraction_error()
