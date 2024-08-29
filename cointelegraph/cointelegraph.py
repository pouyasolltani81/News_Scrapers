import json
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime

# Setup logger
logger = logging.getLogger('CoinTelegraphScraper')
logger.setLevel(logging.INFO)
fh = logging.FileHandler('cointelegraph_scraper.log')
fh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

class CoinTelegraphScraper:
    def __init__(self, mongo_uri, db_name, collection_name):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.base_url = 'https://cointelegraph.com/'

    def get_soup(self, url):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36")

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

    def parse_json_ld(self, soup):
        try:
            script_tag = soup.find('script', type='application/ld+json')
            if script_tag:
                json_data = json.loads(script_tag.string)
                return json_data
        except Exception as e:
            logger.error(f"Error parsing JSON-LD data: {e}")
#             print(f"Error parsing JSON-LD data: {e}")
        return None

    def get_article_body(self, article_url):
        try:
            article = self.get_soup(article_url)
            news = {}
            json_ld_data = self.parse_json_ld(article)
            if json_ld_data:
                news['title'] = json_ld_data.get('headline', '').strip()
                news['description'] = json_ld_data.get('description', '').strip()
                pub_date = json_ld_data.get('datePublished')
                
                if pub_date:
                    news['pubDate'] = int(datetime.strptime(pub_date, '%Y-%m-%dT%H:%M:%S.%fZ').timestamp())
                    news['N_pubDate'] = datetime.strptime(pub_date, '%Y-%m-%dT%H:%M:%S.%fZ')
                    
                news['link'] = article_url
                news['sub_category'] = json_ld_data.get('articleSection', 'cryptocurrency')
                news['author'] = json_ld_data.get('author', {}).get('name', '').strip().lower()
                news['thImage'] = json_ld_data.get('image', {}).get('url', '')
#                 news['imgs'] = [json_ld_data.get('image', {}).get('url', '')]
                news['provider'] = json_ld_data.get('publisher', {}).get('name', 'cointelegraph').strip().lower()
                
                body_contant = article.find('div', class_='post-content')
                if body_contant:
                    body_contant_paragraphs = body_contant.find_all(['p', 'h2'], recursive=False)
                    body_contant_text = '\n'.join([para.text for para in body_contant_paragraphs])
#                     print(body_contant_text[:100])
                    news['body_contant'] = body_contant_text
                    news['imgs'] = [img["src"] for img in body_contant.find_all("img", attrs={"pinger-seen": "true"})]
                    
                category_ul = article.find('ul', class_='tags-list__list')
                if category_ul:
                    tags_items = category_ul.find_all('li', class_='tags-list__item')
                    news['category'] = [item.get_text(strip=True) for item in tags_items]

            else:
                logger.info(f"No JSON-LD data found for {article_url}")
#                 print(f"No JSON-LD data found for {article_url}")

            return news

        except Exception as e:
            logger.error(f"Error processing article at {article_url}: {e}")
#             print(f"Error processing article at {article_url}: {e}")
            return None

    def save_news(self, news_item):
        try:
            item = self.json_item_standard(news_item)
            if item:
                self.collection.insert_one(item)
                logger.info(f"Saved to MongoDB: {item['title']}")
#                 print(f"Saved to MongoDB: {item['title']}")
        except Exception as e:
            logger.error(f"Error saving news item to MongoDB: {e}")
#             print(f"Error saving news item to MongoDB: {e}")

    def json_item_standard(self, news_item):
        try:
            item = {
                'title': news_item.get('title', ''),
                'articleBody': news_item.get('body_contant', ''),
#                 'articleBody': news_item.get('description', ''),
                'pubDate': news_item.get('pubDate', 0),
#                 'N_pubdate': news_item.get('N_pubDate' , ''),
                'keywords': [w.lower()[1:] for w in news_item.get('category', [])],
                'link': news_item.get('link', ''),
                'provider': news_item.get('provider', 'cointelegraph'),
                'summary': news_item.get('description', ''),
                'thImage': news_item.get('thImage', ''),
                'images': news_item.get('imgs', ''),
                'category': 'cryptocurrency',
                'sub_category': news_item.get('sub_category', ''),
                'Negative': 0,
                'Neutral': 0,
                'Positive': 0,
                'author': news_item.get('author', 'cointelegraph')
               
            }
            return item
        except Exception as e:
            logger.error(f"Error standardizing news item: {e}")
#             print(f"Error standardizing news item: {e}")
            return None

    def start_scraping(self):
        try:
            logger.info("Starting scraping...")
#             print("Starting scraping...")
            soup = self.get_soup(self.base_url)
            if soup:
                articles = soup.find_all("article", class_="post-card__article")
                logger.info(f"Number of articles found: {len(articles)}")
#                 print(f"Number of articles found: {len(articles)}")
                for article in articles:
                    link = article.find("a")["href"]
                    article_url = link if link.startswith("http") else self.base_url + link
                    news_item = self.get_article_body(article_url)
                    if news_item:
                        self.save_news(news_item)
            logger.info("Scraping completed.")
#             print("Scraping completed.")
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
#             print(f"Error during scraping: {e}")

# if __name__ == "__main__":
#     scraper = CoinTelegraphScraper(
#         mongo_uri="mongodb+srv://pouya:p44751sm@cluster0.hoskl3b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
#         db_name="crypto_news",
#         collection_name="cointelegraph"
#     )

#     while True:
#         i = 0 
#         scraper.start_scraping()
#         time.sleep(1800)  
#         print(f'It has been {i} Times and it has been running {i/2} hours')
#         i += 1
#         if i == 10 :
#             break
