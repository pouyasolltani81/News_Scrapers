
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from pymongo import MongoClient
import json
import os
import logging
from datetime import datetime
from html import unescape

logger = logging.getLogger('Rotating Log')


class CoinTelegraphScraper:
    def __init__(self, mongo_uri, db_name, collection_name):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.base_url = 'https://cointelegraph.com/'

    def get_soup(self, url):
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("user-agent=Mozilla/5.0")

            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            driver.get(url)

            if os.path.exists("cookies.json"):
                with open("cookies.json", "r") as f:
                    cookies = json.load(f)
                    for cookie in cookies:
                        driver.add_cookie(cookie)

                driver.get(url)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            driver.quit()
            return soup
        except Exception as err:
            logger.error(f"Error while getting soup for URL: {url}. Error: {str(err)}")
            raise

    def get_article_body(self, article_url):
        try:
            article = self.get_soup(article_url)
            if article:
                news = {}

                news['title'] = unescape(article.title.string.strip()) if article.title else 'No Title'

                summary = article.find("meta", attrs={"name": "description"})
                news['summary'] = summary["content"] if summary else 'No Summary'

                pub_date = article.find('time')
                news['pubDate'] = pub_date['datetime'] if pub_date else 'No Date'

                description = article.find('div', class_='post-content')
                if description:
                    paragraphs = description.find_all(['p', 'h2'], recursive=False)
                    news['description'] = ''.join([para.text for para in paragraphs])

                news['link'] = article_url

                tags_items = article.find_all('li', class_='tags-list__item')
                news['category'] = [item.get_text(strip=True).lower() for item in tags_items]

                img_thum_div = article.find("div", class_="post-cover__image")
                news['thImage'] = img_thum_div.find("img")["src"] if img_thum_div else None

                news['imgs'] = [img["src"] for img in description.find_all("img", attrs={"pinger-seen": "true"})] if description else []

                creator = article.find('div', class_='post-meta__author-name')
                news['creator'] = creator.text.strip().lower() if creator else 'No Author'

                return news
            else:
                return None
        except Exception as err:
            logger.error(f"Error while parsing article: {article_url}. Error: {str(err)}")
            raise

    def JsonItemStandard(self, newsItem):
        try:
            item = {}
            item['title'] = unescape(newsItem['title'])
            item['articleBody'] = unescape(newsItem['description'])

            # Convert publication date to timestamp
            currentDate = datetime.strptime(newsItem['pubDate'], '%Y-%m-%dT%H:%M:%SZ')
            item['pubDate'] = int(currentDate.timestamp())

            item['keywords'] = newsItem['category']
            item['link'] = newsItem['link']
            item['provider'] = 'cointelegraph'
            item['summary'] = newsItem['summary']
            item['thImage'] = newsItem.get('thImage', ' ')
            item['images'] = newsItem.get('imgs', [])
            item['category'] = 'cryptocurrency'
            item['Negative'] = 0
            item['Neutral'] = 0
            item['Positive'] = 0
            item['author'] = newsItem['creator'] if newsItem['creator'] else item['provider']
            return item
        except Exception as err:
            logger.error(f"Error in JsonItemStandard: {str(err)}")
            raise

    def savegroupNews(self, newsItem):
        try:
            for item in newsItem:
                item = self.JsonItemStandard(item)
                self.collection.insert_one(item)
                logger.info(f"Saved to MongoDB: {item['title']}")
        except Exception as err:
            logger.error(f"Error while saving group news: {str(err)}")
            raise

    def start_scraping(self):
        try:
            logger.info(f'Crawling of CoinTelegraph started at {datetime.now().strftime("%a, %d %b %Y %H:%M:%S %Z")}!!')
            logger.info('+---------------------------------------------+')
            soup = self.get_soup(self.base_url)
            if soup:
                articles = soup.find_all("article", class_="post-card__article")
                logger.info(f'Number of articles found: {len(articles)}')
                newsitems = []
                for article in articles:
                    link = article.find("a")["href"]
                    article_url = link if link.startswith("http") else self.base_url + link
                    article_data = self.get_article_body(article_url)
                    if article_data:
                        newsitems.append(article_data)
                self.savegroupNews(newsitems)
        except Exception as err:
            logger.error(f"Error in start_scraping: {str(err)}")
            raise


# if __name__ == "__main__":
#     scraper = CoinTelegraphScraper(
#         mongo_uri="mongodb://localhost:27017/",  # Update with local MongoDB URI
#         db_name="crypto_news",
#         collection_name="cointelegraph"
#     )
#     scraper.start_scraping()
