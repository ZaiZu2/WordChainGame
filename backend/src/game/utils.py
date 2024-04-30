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

    if response.status_code // 100 == 5:
        raise Exception('Dictionary API is not available')

    data = response.json()

    # Mirriam-Webster returns a list of similar words if the word is not found
    if any(isinstance(elem, str) for elem in data):
        return s.Word(content=word, is_correct=False)

    definitions = [definition for definition in data if definition.get('fl')]

    description: list[tuple[str, str]] = [
        (definition['fl'], definition['shortdef'][0])
        for i, definition in enumerate(definitions)
        if i < 3 and definition.get('fl')
    ]
    return s.Word(content=word, is_correct=True, description=description)
