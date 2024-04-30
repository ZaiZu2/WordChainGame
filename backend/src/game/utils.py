import httpx

import src.schemas as s
from config import get_config

client = httpx.Client()


def check_word_correctness(word: str) -> s.Word:
    response = client.get(
        get_config().DICTIONARY_API_URL.format(
            word=word, api_key=get_config().DICTIONARY_API_KEY
        )
    )

    # TODO: Handle connection errors and other exceptions
    if response.status_code == 404:
        # TODO: Function does 2  things - unpacks response and returns False on failed validation
        return s.Word(content=word, is_correct=False)
    if response.status_code == 500:
        raise Exception('Dictionary API is not available')

    definitions = [
        definition for definition in response.json() if definition.get('hom')
    ]

    description: list[tuple[str, str]] = [
        (definition['fl'], definition['shortdef'][0]) for definition in definitions
    ]
    return s.Word(content=word, is_correct=True, description=description)
