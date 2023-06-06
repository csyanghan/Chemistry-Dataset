import json
import math
import os
import threading

import jsonlines
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers={'User-Agent':user_agent,} 


index_ulrs = []
for i in range(65, 88):
    index_ulrs.append('https://goldbook.iupac.org/terms/index/' + chr(i))
index_ulrs.append('https://goldbook.iupac.org/terms/index/XYZ')

def get_urls_for_every_index(index_url):
    r = requests.get(index_url, headers)
    soup = BeautifulSoup(r.text, 'html.parser')
    questions_url = soup.select('#terms .list-group-item')
    questions_url = ['https://goldbook.iupac.org' + url['href'] +'/json' for url in questions_url]
    return questions_url

term_urls = []
for url in index_ulrs:
    term_urls += get_urls_for_every_index(url)

print('craw {} urls'.format(len(term_urls)))

def json_open(path):
    if not os.path.exists(path): return None
    with open(path, 'r') as reader:
        return json.load(reader)

def json_save(content, path):
    with open(path, 'w') as writer:
        json.dump(content, writer, indent=1)

cached = json_open('cache.json') or []

def download(url):
    r = requests.get(url, headers)
    try:
        return {
            'title': r.json()['term']['title'],
            'content': r.json()['term']['definitions'][0]['text']
        }
    except Exception:
        return None
    
def thread_download(thread_id, start, end, qa_array, writer):
    for idx in tqdm(range(start, end), desc='线程{}'.format(thread_id)):
        if qa_array[idx] not in cached:
            term_title_content = download(qa_array[idx])
            lock.acquire()
            if term_title_content:
                writer.write(term_title_content)
                cached.append(qa_array[idx])
                json_save(cached, 'cache.json')
            lock.release()

try:
    with jsonlines.open('data.jsonl', mode='w') as writer:

        lock = threading.Lock()
        threads = []
        thread_num = 3

        step = math.floor(len(term_urls) / thread_num)
        for i in range(0, thread_num):
            interval_start = i * step
            interval_end = (i+1) * step
            t = threading.Thread(target=thread_download, kwargs={'thread_id': i, 'start': interval_start, 'end':interval_end, 'qa_array':term_urls, 'writer': writer})
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

except Exception as e:
    json_save(cached, 'cache.json')
