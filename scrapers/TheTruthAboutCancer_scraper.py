import csv
import time
import sys
import requests
from bs4 import BeautifulSoup

output_file = '../articles/TheTruthAboutCancer.csv'
fieldnames = ['title', 'content', 'publishedAt', 'url']
with open(output_file, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

'''get all links'''
article_urls = set()
url1 = 'https://thetruthaboutcancer.com/?s=coronavirus'
url2 = 'https://thetruthaboutcancer.com/?s=covid-19'
url3 = 'https://thetruthaboutcancer.com/?s=covid'

for url in [url1, url2, url3]:
    req = requests.get(url)
    page = req.content
    soup = BeautifulSoup(page, 'html.parser')

    main_content = soup.find('div', class_='category-wrap')
    articles = main_content.find_all('article')

    for entry in articles:
        item = entry.find('header', class_='entry-header')
        article_urls.add(item.a['href'])

'''get content for each article'''
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, 'html.parser')

    # title
    header = soup.find('header', class_='entry-header')
    title = header.find('h1', class_='entry-title').get_text()

    # content
    article = soup.find('div', class_='entry-content')
    text = article.find_all(['p', 'li', 'h1', 'h2', 'h3'])
    content = '\n'.join([i.get_text() for i in text])

    # publishedAt
    metadata = header.find('p', class_='entry-meta')
    datetime = str(metadata.find('br')).split('<br/')[0][4:]

    with open(output_file, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'title': title, 'content': content, 'publishedAt': datetime, 'url': link}) 