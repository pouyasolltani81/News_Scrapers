import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
import logging
from pymongo import MongoClient
from html import unescape


logger = logging.getLogger('BitcoinistScraperLog')
logger.setLevel(logging.INFO)
handler = logging.FileHandler('bitcoinist_scraper.log')
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class BitcoinistScraper:
    def __init__(self, mongo_uri, db_name, collection_name, base_url='https://bitcoinist.com', rss_url="https://bitcoinist.com/feed/"):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.base_url = base_url
        self.rss_url = rss_url

       
        self.client = MongoClient(self.mongo_uri)
        self.db = self.client[self.db_name]
        self.collection = self.db[self.collection_name]

       

    def clean_content(self, content):
        try:
            for text in self.unwanted_text:
                content = content.replace(text, "").strip()
            return content
        except Exception as err:
            logger.error(f"Error cleaning content: {err}")
#             print(f"Error cleaning content: {err}")
            raise

    def loadPage(self,url):
    
        try:
           
            headers = {
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'}
            resp = requests.get(url, timeout=3, headers=headers)
            if resp.status_code == 200:

                self.xmlData = resp.content
                return self.xmlData
            else:
                return -1

        except requests.exceptions.HTTPError as htError:
            logger.error('Http Error: %s', str(htError))
            raise errors.DataProvidingException(''.format('  {message}' ,message=str(htError)))

        except requests.exceptions.ConnectionError as coError:
            logger.error('Connection Error: %s',str( coError))
            raise errors.DataProvidingException(str(coError))

        except requests.exceptions.Timeout as timeOutError:
            logger.error('TimeOut Error: %s', str(timeOutError))
            raise errors.DataProvidingException (str(timeOutError))

        except requests.exceptions.RequestException as ReError:
            logger.error('Something was wrong: %s', str(ReError))
            raise errors.DataProvidingException(str(ReError))


    def parse_rss(self, rss_content):
        try:
            root = ET.fromstring(rss_content)
            news_items = []

            for item in root.findall(".//item"):
                news = {}
                news['title'] = item.find('title').text
                news['link'] = item.find('link').text
                pub_date = item.find('pubDate').text
                news['pubDate'] = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
                news['timestamp'] = int(news['pubDate'].timestamp())

                description_html = item.find('description').text
                soup_d = BeautifulSoup(description_html, 'html.parser')
                content_encoded = item.find('{http://purl.org/rss/1.0/modules/content/}encoded').text
                soup_c = BeautifulSoup(content_encoded, 'html.parser')

                news['summary'] = soup_d.get_text().strip()
                news['content'] = ' '.join(p.get_text() for p in soup_c.find_all(['p', 'h2']))
                news['images'] = [img['src'] for img in soup_c.find_all('img') if 'src' in img.attrs]
                news['thImage'] = item.find('enclosure')['url'] if item.find('enclosure') else (news['images'][0] if news['images'] else '')
                news['category'] = [category.text.lower() for category in item.findall('category')]
                news['keywords'] = news['category']
                author_encoded = item.find('{http://purl.org/dc/elements/1.1/}creator').text
                news['author'] = BeautifulSoup(author_encoded, 'html.parser').get_text().strip().lower()

                news_items.append(news)
            return news_items
        except ET.ParseError as err:
            logger.error(f"Error parsing RSS feed: {err}")
#             print(f"Error parsing RSS feed: {err}")
            raise
        except Exception as err:
            logger.error(f"General error in parsing RSS: {err}")
#             print(f"General error in parsing RSS: {err}")
            raise

    def JsonItemStandard(self, news_item):
        try:
            item = {
                'title': unescape(news_item['title']),
                'articleBody': unescape(news_item['content']),
                'pubDate': news_item['timestamp'],
                'keywords': news_item['keywords'],
                'link': news_item['link'],
                'provider': 'bitcoinist',
                'summary': news_item['summary'],
                'thImage': news_item['thImage'] if 'thImage' in news_item else ' ',
                'images': news_item['images'],
                'category': 'cryptocurrency',
                'Negative': 0,
                'Neutral': 0,
                'Positive': 0,
                'author': news_item['author'] if news_item['author'] else 'bitcoinist'
            }
            return item
        except Exception as err:
            logger.error(f"Error standardizing item: {err}")
#             print(f"Error standardizing item: {err}")
            raise

    def savegroupNews(self, news_items):
        try:
            for news_item in news_items:
                standardized_item = self.JsonItemStandard(news_item)
                self.collection.insert_one(standardized_item)
                logger.info(f"Saved to MongoDB: {standardized_item['title']}")
#                 print(f"Saved to MongoDB: {standardized_item['title']}")
        except Exception as err:
            logger.error(f"Error saving news items: {err}")
#             print(f"Error saving news items: {err}")
            raise

    def start_scraping(self):
        try:
            rss_content = self.loadPage(self.rss_url)
            if rss_content:
                news_items = self.parse_rss(rss_content)
                self.savegroupNews(news_items)
        except Exception as err:
            logger.error(f"General error during scraping: {err}")
#             print(f"General error during scraping: {err}")
            raise


# # Instantiate and run the scraper
# scraper = BitcoinistScraper(
#     mongo_uri="mongodb+srv://pouya:p44751sm@cluster0.hoskl3b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0",
#     db_name="crypto_news",
#     collection_name="bitcoinist"
# )
# scraper.start_scraping()
