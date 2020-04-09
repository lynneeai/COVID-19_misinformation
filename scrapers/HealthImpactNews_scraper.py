import csv
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

output_file = '../articles/HealthImpactNews.csv'
fieldnames = ['title', 'content', 'publishedAt', 'url']
with open(output_file, 'w') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

'''get all article urls'''
article_urls = set()
url1 = 'https://healthimpactnews.com/?find=coronavirus'
url2 = 'https://healthimpactnews.com/?find=covid-19'
url3 = 'https://healthimpactnews.com/?find=covid'

driver = webdriver.Chrome('/Users/lynnee/Tools/chromedriver')
SCROLL_PAUSE_TIME = 2

for url in [url1, url3]:
    driver.get(url)
    time.sleep(SCROLL_PAUSE_TIME)
    # keep loading more until end
    while driver.find_element_by_class_name('load_more').get_attribute('style') == 'visibility: visible;':
        driver.find_element_by_class_name('load_more').click()
        time.sleep(SCROLL_PAUSE_TIME)

    soup = BeautifulSoup(driver.page_source,'html.parser')
    main_container = soup.find('div', class_='acs_search_results_items')
    articles = main_container.find_all('div', class_='entry-permalink')
    for entry in articles:
        article_urls.add(entry.a['href'])

driver.quit()

'''get content for each article'''
for link in article_urls:
    req = requests.get(link)
    page = req.content
    soup = BeautifulSoup(page, 'html.parser')

    main_content = soup.find('div', id='content')

    # title
    title = main_content.find('h2', class_='entry-title').get_text()

    # content
    article = main_content.find('div', class_='post-content')
    text = article.find_all(['p', 'li', 'h1', 'h2', 'h3'])
    content = '\n'.join([i.get_text() for i in text])

    # publishedAt
    datetime = article.find('div', class_='entry-date').get_text()
    datetime = datetime.split('on ')[1]

    with open(output_file, 'a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'title': title, 'content': content, 'publishedAt': datetime, 'url': link}) 