import json
import os
import re

import jsonlines


def json_open(path):
    if not os.path.exists(path): return None
    with open(path, 'r') as reader:
        return json.load(reader)

def json_save(content, path):
    with open(path, 'w') as writer:
        json.dump(content, writer, indent=1)

goldbook_vocab = json_open('./goldbook_vocab.json')
entries = goldbook_vocab['entries']

def flatten_list_to_str(raw_list):
    if len(raw_list) >= 1:
        if isinstance(raw_list[0], list):
            return flatten_list_to_str(raw_list[0])
        else:
            return raw_list[0]
    else:
        return ''

with jsonlines.open('data.jsonl', mode='w') as writer:
    for entry in entries.values():
        if entry['term']:
            if isinstance(entry['definition'], list):
                definition = flatten_list_to_str(entry['definition'])
            else:
                definition = entry['definition'] or ''
            raw_text = entry['term'] + '\n\n' + definition
            re_pattern = re.compile('<[^>]+>', re.S)
            text = re_pattern.sub('', raw_text)
            writer.write({'text': text})

