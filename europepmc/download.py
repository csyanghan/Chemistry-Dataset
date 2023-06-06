import json
import math
import os
import threading

import requests
import wget
from bs4 import BeautifulSoup
from tqdm import tqdm

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
headers={'User-Agent':user_agent,} 

r = requests.get('https://europepmc.org/ftp/archive/v.2023.06/oa/', headers)
soup = BeautifulSoup(r.text, 'html.parser')

files_href = soup.find_all('a')
files_url = [ 'https://europepmc.org/pub/databases/pmc/archive/v.2023.06/oa/' + href['href'] for href in files_href  if href['href'].endswith('.gz')]

def json_open(path):
    if not os.path.exists(path): return None
    with open(path, 'r') as reader:
        return json.load(reader)

def json_save(content, path):
    with open(path, 'w') as writer:
        json.dump(content, writer, indent=1)

cached = json_open('cache.json') or []

def download(url):
    path = 'data/' + url.split('/')[len(url.split('/'))-1]
    wget.download(url, path)

def thread_download(thread_id, start, end, qa_array):
    for idx in tqdm(range(start, end), desc='线程{}'.format(thread_id)):
        if qa_array[idx] not in cached:
            download(qa_array[idx])
            lock.acquire()
            cached.append(qa_array[idx])
            json_save(cached, 'cache.json')
            lock.release()

lock = threading.Lock()
threads = []
thread_num = 1

step = math.floor(len(files_url) / thread_num)
for i in range(0, thread_num):
    interval_start = i * step
    interval_end = (i+1) * step
    t = threading.Thread(target=thread_download, kwargs={'thread_id': i, 'start': interval_start, 'end':interval_end, 'qa_array':files_url})
    threads.append(t)
    t.start()

for t in threads:
    t.join()

