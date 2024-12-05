import io
import base64
import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()

def extract_text_from_base64(base_64):
    if not base_64:
        return ''

    try:
        decoded_audio = base64.b64decode(base_64)

        audio_file = io.BytesIO(decoded_audio)
        audio_file.name = 'audio.mp3'

        transcript = client.audio.transcriptions.create(model=os.getenv('OPENAI_LLM_MODEL_NAME'), file=audio_file)

        return transcript.text
    except Exception as e:
        print(f'Error during audio transcription: {e}')
        return 'Escreva isso sem nenhuma explicação extra e sem as aspas: "Não consigo compreender áudios no momento, poderia escrever o que deseja por favor?"'
