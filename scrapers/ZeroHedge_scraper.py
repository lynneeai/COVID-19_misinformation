import csv
import time
import sys
import requests
import pickle
from bs4 import BeautifulSoup
from tqdm import tqdm

REFETCH_URLS = False
url_temp_file = './zerohedge_urls'

output_file = '../articles/ZeroHedge.csv'
fieldnames = ['title', 'content', 'publishedAt', 'url']
with open(output_file, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

'''get all links'''
if REFETCH_URLS:
    article_urls = set()
    url_root = 'https://www.zerohedge.com'
    url_search_root = 'https://www.zerohedge.com/search-content'
    url1 = 'https://www.zerohedge.com/search-content?search_api_fulltext=coronavirus&sort_by=search_api_relevance&page=0'
    # url2 = 'https://jimbakkershow.com/?s=covid-19'
    # url3 = 'https://jimbakkershow.com/?s=covid'

    for url in [url1]:
        while True:
            print(url)
            req = requests.get(url)
            page = req.content
            soup = BeautifulSoup(page, 'html.parser')

            main_content = soup.find('div', class_='views-element-container')
            articles = main_content.find_all('div', class_='views-row')

            for entry in articles:
                item = entry.find('span', class_='views-field views-field-title')
                url_article = item.a['href']
                article_urls.add(f'{url_root}{url_article}')

            # find next page url
            page_nav = main_content.find('nav', class_='pager')
            next_button = page_nav.find_all('li', class_='pager__item pager__item--next')
            if next_button:
                url_next = next_button[0].a['href']
                url = f'{url_search_root}{url_next}'
            else:
                break

    with open(url_temp_file, 'wb') as fp:
        pickle.dump(article_urls, fp)

'''get content for each article'''
with open (url_temp_file, 'rb') as fp:
    article_urls = pickle.load(fp)

for link in tqdm(article_urls):
    try:
        req = requests.get(link)
        page = req.content
        soup = BeautifulSoup(page, 'html.parser')

        # title
        header = soup.find('h1', class_='page-title')
        title = header.span.get_text()

        # content
        article = soup.find('div', class_='node__content')
        text = article.find_all(['p', 'li', 'h1', 'h2', 'h3'])
        content = '\n'.join([i.get_text() for i in text])

        # publishedAt
        metadata = soup.find('div', class_='submitted-datetime')
        datetime = metadata.span.get_text()
    except:
        print(link)
        break

    with open(output_file, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'title': title, 'content': content, 'publishedAt': datetime, 'url': link}) 