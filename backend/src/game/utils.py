import httpx

import src.schemas as s
from config import get_config


def check_word_correctness(word: str) -> s.Word:
    client = httpx.Client()
    response = client.get(f'{get_config().DICTIONARY_API_URL}{word}')

    # TODO: Handle connection errors and other exceptions
    if response.status_code == 404:
        # TODO: Function does 2  things - unpacks response and returns False on failed validation
        return s.Word(content=word, is_correct=False)

    definitions = {
        meaning['partOfSpeech']: meaning['definitions'][0]['definition']
        for meaning in response.json()[0]['meanings']
    }
    return s.Word(content=word, is_correct=True, description=definitions)
