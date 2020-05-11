import csv
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

output_file = '../articles/BigLeaguePolitics.csv'
fieldnames = ['title', 'content', 'publishedAt', 'url']
with open(output_file, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

'''get all article urls'''
article_urls = set()
url1 = 'https://bigleaguepolitics.com/?s=coronavirus'
url2 = 'https://bigleaguepolitics.com/?s=covid-19'
url3 = 'https://bigleaguepolitics.com/?s=covid'

for url in [url1, url2, url3]:
    while True:
        req = requests.get(url)
        page = req.content
        soup = BeautifulSoup(page, 'html.parser')

        main_content = soup.find('div', class_='mvp-main-blog-body left relative')
        articles = main_content.find_all('li', class_='mvp-blog-story-wrap left relative infinite-post')

        for entry in articles:
            article_urls.add(entry.a['href'])

        # find next page url
        page_nav = main_content.find('div', class_='pagination')
        all_pages = page_nav.find_all('a')
        has_next = False
        for p in all_pages:
            if p.get_text() == 'Next ›':
                url = p['href']
                has_next = True
        if not has_next:
            break

'''get content for each article'''
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, 'html.parser')

    main_content = soup.find('div', id='mvp-post-main')

    # title
    title = main_content.find('h1', class_='mvp-post-title left entry-title').get_text()

    # content
    article = main_content.find('div', id='mvp-content-main')
    text = article.find_all('p', recursive=False)
    content = '\n'.join([i.get_text() for i in text])

    # publishedAt
    datetime = main_content.find('span', class_='mvp-post-date updated').time['datetime']

    with open(output_file, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'title': title, 'content': content, 'publishedAt': datetime, 'url': link}) 
