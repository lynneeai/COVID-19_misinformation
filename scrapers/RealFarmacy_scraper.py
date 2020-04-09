import csv
import time
import sys
import requests
from bs4 import BeautifulSoup

output_file = '../articles/RealFarmacy.csv'
fieldnames = ['title', 'content', 'publishedAt', 'url']
with open(output_file, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

'''get all links'''
article_urls = set()
url1 = 'https://realfarmacy.com/?s=coronavirus'
url2 = 'https://realfarmacy.com/?s=covid-19'
url3 = 'https://realfarmacy.com/?s=covid'

for url in [url1, url2, url3]:
    while True:
        req = requests.get(url)
        page = req.content
        soup = BeautifulSoup(page, 'html.parser')

        main_content = soup.find('div', class_='main-content-inner clearfix')
        articles = main_content.find_all('div', class_='entry-blog')

        for entry in articles:
            item = entry.find('h2', class_='page-title')
            article_urls.add(item.a['href'])

        # find next page url
        page_nav = main_content.find('ul', class_='post-nav')
        next_button = page_nav.find_all('li', class_='nav-previous previous')
        if next_button:
            url = next_button[0].a['href']
        else:
            break

'''get content for each article'''
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, 'html.parser')

    main_content = soup.find('div', class_='main-content-inner').article

    # title
    header = main_content.find('h2', class_='page-title')
    title = header.a.get_text()

    # content
    article = main_content.find('div', class_='entry-summary blog-entry-summary')
    text = article.find_all(['p', 'li', 'h1', 'h2', 'h3'])
    content = '\n'.join([i.get_text() for i in text])

    # # publishedAt
    # metadata = header.find('div', class_='post-meta vcard')
    # datetime = metadata.find('span', class_='updated').get_text()

    with open(output_file, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'title': title, 'content': content, 'publishedAt': '', 'url': link}) 