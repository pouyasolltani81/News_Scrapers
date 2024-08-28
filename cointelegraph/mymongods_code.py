from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from pymongo import MongoClient
import json
import time
import random
import os

class cointelegraphScraper:
    
    def __init__(self, mongo_uri, db_name, collection_name):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.base_url = 'https://cointelegraph.com/'
        
    def get_soup(self, url):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass WebDriver detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(url)

        # Load cookies if available
        if os.path.exists("cookies.json"):
            with open("cookies.json", "r") as f:
                cookies = json.load(f)
                for cookie in cookies:
                    driver.add_cookie(cookie)

            # Navigate to the website again with the loaded cookies
            driver.get(url)

        # Use BeautifulSoup to parse the page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        return soup
    
    def get_article_body(self, article_url):
        article = self.get_soup(article_url)
        if article:
            news = {}

            title = article.title.string
            if title:
                news['title'] = title.strip()

            summary = article.find("meta", attrs={"name": "description"})
            if summary:
                news['summary'] = summary["content"]

            pub_date = article.find('time')
            if pub_date:
                news['pubDate'] = pub_date['datetime']
            
            description = article.find('div', class_='post-content')
            if description:
                description_paragraphs = description.find_all(['p', 'h2'], recursive=False)
                description_text = ''.join([para.text for para in description_paragraphs])
                news['description'] = description_text

            news['link'] = article_url

            category_ul = article.find('ul', class_='tags-list__list')
            if category_ul:
                tags_items = category_ul.find_all('li', class_='tags-list__item')
                news['category'] = [item.get_text(strip=True) for item in tags_items]

            img_thum_div = article.find("div", class_="post-cover__image")
            img_thum = img_thum_div.find("img")["src"] if img_thum_div else None
            if img_thum:
                news['thImage'] = img_thum

            news['imgs'] = [img["src"] for img in description.find_all("img", attrs={"pinger-seen": "true"})]

            creator = article.find('div', class_='post-meta__author-name')
            if creator:
                news['creator'] = creator.text.strip()

            article_data = {
                "title": news['title'],
                "url": news['link'],
                "author": news.get('creator', 'N/A'),
                "publish_date": news.get('pubDate', 'N/A'),
                "tags": news.get('category', []),
                "img_thum": news.get('thImage', 'N/A'),
                "images": news.get('imgs', []),
                "summary": news.get('summary', 'N/A'),
                "content": news.get('description', 'N/A'),
            }

            return article_data
        else:
            return None
    
    def scrape_news(self):
        url = self.base_url
        soup = self.get_soup(url)
        if soup:
            articles = soup.find_all("article", class_="post-card__article")
            print(f'Number of articles found: {len(articles)}')
            for article in articles:
                link = article.find("a")["href"]
                article_url = link if link.startswith("http") else self.base_url + link
                article_data = self.get_article_body(article_url)
                if article_data:
                    self.collection.insert_one(article_data)
                    print(f"Saved to MongoDB: {article_data['title']}")

# Instantiate and run the scraper
scraper = cointelegraphScraper(
    mongo_uri="mongodb+srv://pouya:p44751sm@cluster0.hoskl3b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
    db_name="crypto_news",
    collection_name="cointelegraph"
)
scraper.scrape_news()
