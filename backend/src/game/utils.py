import httpx

import src.schemas.domain as d
from config import get_config

client = httpx.Client()

accepted_func_labels = [
    'noun',
    'verb',
    'adjective',
    'adverb',
]


def check_word_correctness(word: str) -> d.Word:
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
        return d.Word(content=word, is_correct=False)

    filtered_definitions = []
    for definition in data:
        # Filter out words finds without functional labels
        if not (definition.get('fl') and definition['fl'] in accepted_func_labels):
            continue

        # Filter out any definitions which are not the exact match - Mirriam-Webster returns
        # similar words (e.g 'god' -> 'god-awful'). In case multiple definitions exist,
        # it will index them using a colon (e.g 'god:1', 'god:2')
        if not definition['meta']['id'].lower().split(':')[0] == word:
            continue

        filtered_definitions.append(definition)

    description: list[tuple[str, list[str]]] = []
    for definition, _ in zip(filtered_definitions, range(3)):
        shortdefs: list[str] = [
            '- ' + shortdef if i > 0 else shortdef
            for i, shortdef in enumerate(definition['shortdef'])
        ]
        part_of_speech: str = definition['fl']
        description.append((part_of_speech, shortdefs))

    return d.Word(content=word, is_correct=True, definitions=description)
