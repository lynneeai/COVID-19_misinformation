import csv
import time
import requests
from bs4 import BeautifulSoup

output_file = '../articles/DCClothesline.csv'
fieldnames = ['title', 'content', 'publishedAt', 'url']
with open(output_file, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

'''get all article urls'''
article_urls = set()
url1 = 'https://www.dcclothesline.com/?s=coronavirus'
url2 = 'https://www.dcclothesline.com/?s=covid-19'
url3 = 'https://www.dcclothesline.com/?s=covid'

for url in [url1, url2, url3]:
    while True:
        req = requests.get(url)
        page = req.content
        soup = BeautifulSoup(page, 'html.parser')

        main_content = soup.find('div', class_='td-ss-main-content')
        articles = main_content.find_all('div', class_='td-block-span6')

        for entry in articles:
            item = entry.find('h3', class_='entry-title td-module-title')
            article_urls.add(item.a['href'])

        # find next page url
        try:
            page_nav = main_content.find('div', class_='page-nav td-pb-padding-side')
            all_pages = page_nav.find_all('a')
            has_next = False
            for p in all_pages:
                if p.find_all('i', class_='td-icon-menu-right'):
                    url = p['href']
                    has_next = True
            if not has_next:
                break
        except:
            break

'''get content for each article'''
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, 'html.parser')

    main_content = soup.find('div', class_='td-container td-post-template-2')

    # title
    header = main_content.find('header', class_='td-post-title')
    title = header.find('h1', class_='entry-title').get_text()

    # content
    article = main_content.find('div', class_='td-post-content tagdiv-type')
    text = article.findChildren('p', recursive=False)
    content = '\n'.join([i.get_text() for i in text])

    # publishedAt
    metadata = header.find('div', class_='td-module-meta-info')
    datetime = metadata.find('span', class_='td-post-date').time['datetime']

    with open(output_file, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'title': title, 'content': content, 'publishedAt': datetime, 'url': link}) 