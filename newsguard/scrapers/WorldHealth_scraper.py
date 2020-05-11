import csv
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

output_file = '../articles/WorldHealth.csv'
fieldnames = ['title', 'content', 'publishedAt', 'url']
with open(output_file, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

'''get all article urls'''
url_root = 'https://worldhealth.net'

article_urls = set()
url1 = 'https://worldhealth.net/search/?q=coronavirus'
url2 = 'https://worldhealth.net/search/?q=covid-19'
url3 = 'https://worldhealth.net/search/?q=covid'

driver = webdriver.Chrome('/Users/lynnee/Tools/chromedriver')
SCROLL_PAUSE_TIME = 2

for url in [url1, url2, url3]:
    driver.get(url)
    time.sleep(SCROLL_PAUSE_TIME)
    # keep loading more until end
    while driver.find_elements_by_xpath('.//span[@class = "btn bigBtn load-more"]')[0].get_attribute('style') != 'display: none;':
        driver.find_elements_by_xpath('.//span[@class = "btn bigBtn load-more"]')[0].click()
        time.sleep(SCROLL_PAUSE_TIME)

    soup = BeautifulSoup(driver.page_source,'html.parser')
    main_content = soup.find('div', id='result_tile_list')
    articles = main_content.find_all('ul', class_='item card result-item')
    for entry in articles:
        item = entry.find('li', class_='titleItem')
        url_article = item.a['href']
        article_urls.add(f'{url_root}{url_article}')

driver.quit()

'''get content for each article'''
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, 'html.parser')

    main_content = soup.find('div', id='ArticleContent')

    # title
    header = main_content.find('div', class_='wrapper')
    title = header.find('h1').get_text()

    # content
    article = main_content.find('div', class_='oneNesBox')
    text = article.find_all(['p', 'li', 'h1', 'h2', 'h3'])
    content = '\n'.join([i.get_text() for i in text])

    # publishedAt
    datetime = article.h5.get_text().split('Posted on ')[1].strip()

    with open(output_file, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'title': title, 'content': content, 'publishedAt': datetime, 'url': link}) 