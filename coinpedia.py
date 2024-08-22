import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup


class CoinpediaScrapper(Scraper):

    def __init__(self):
        super().__init__('https://coinpedia.com/')
        self.rss_url = "https://coinpedia.com/feed/"
        self.unwanted_text = ()
        self.website_name = 'coinpedia'

    def clean_content(self, content):
      if self.unwanted_text in content:
          content = content.replace(self.unwanted_text, "").strip()
      return content



    def fetch_rss(self):
        try:
            response = requests.get(self.rss_url)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f"Error fetching RSS feed: {e}")
            return None


    def parse_rss(self, rss_content):
        news_items = []
        root = ET.fromstring(rss_content)

        for item in root.findall(".//item"):
            news = {}
            news['title'] = item.find('title').text
            news['link'] = item.find('link').text
            news['pubDate'] = item.find('pubDate').text


            pub_date = datetime.strptime(news['pubDate'], "%a, %d %b %Y %H:%M:%S %z")
            news['timestamp'] = int(pub_date.timestamp())


            description_html = item.find('description').text
            soup_d = BeautifulSoup(description_html, 'html.parser')



            content_encoded = item.find('{http://purl.org/rss/1.0/modules/content/}encoded').text
            soup_c = BeautifulSoup(content_encoded, 'html.parser')


            description_text = ' '.join(p.get_text() for p in soup_d.find_all(['p', 'h2']))
            content_text = ' '.join(p.get_text() for p in soup_c.find_all(['p', 'h2'])[:-3])
            content_text = self.clean_content(content_text)
            news['summery'] = description_text.strip()
            news['content'] =  content_text.strip()


            images = [img['src'] for img in soup_c.find_all('img') if 'src' in img.attrs]
            news['images'] = images


            news['thImage'] = item.find('enclosure')['url'] if item.find('enclosure') else (images[0] if images else '')


            categories = [category.text for category in item.findall('category')]
            news['category'] = categories
            news['keywords'] = categories


            author_encoded = item.find('{http://purl.org/dc/elements/1.1/}creator').text
            soup_a = BeautifulSoup( author_encoded, 'html.parser')

            author = soup_a.get_text()
            news['author'] = author.strip()


            news_items.append(news)

        return news_items

    def JsonItemStandard(self, newsItem):
        try:
            item = {}


            item['title'] = unescape(newsItem.get('title', ''))

            item['articleBody'] = unescape(newsItem.get('content', ''))


            item['pubDate']  = newsItem.get('timestamp')


            category = newsItem.get('category', '')
            item['keywords'] = [category.lower()]


            item['link'] = newsItem.get('link', '')


            item['provider'] = 'coinpedia'


            item['summary'] = newsItem.get('summery', '')


            item['thImage'] = newsItem.get('thImage', ' ')


            item['images'] = newsItem.get('images', ' ')


            item['category'] =  newsItem.get('category', '')


            item['Negative'] = 0
            item['Neutral'] = 0
            item['Positive'] = 0


            creator = newsItem.get('author')
            if not creator:
                item['author'] = item['provider']
            else:
                item['author'] = unescape(creator).strip().lower()


            item['scraped_date'] = int(datetime.now().timestamp())

            return item
        except errors.DataProvidingException as err:
            logger.error(f'{str(err)} from SpecificSiteScraper')
            raise errors.DataProvidingException(f'{str(err)} from {self.website_name}')
        except Exception as err:
            logger.error(f'{str(err)} from {self.website_name}')
            raise errors.DataProvidingException(f'{str(err)} from {self.website_name}')

    def savegroupNews(self, newsItems):
        try:
            for item in newsItems:

                item = self.JsonItemStandard(item)
                self.saveInMongo(item)
        except requests.exceptions.ConnectionError as err:
            logger.error(f'{str(err)} from {self.website_name}')
            raise errors.DataProvidingException(f'{str(err)} from {self.website_name}')
        except Exception as err:
            logger.error(f'{str(err)} from {self.website_name}')
            raise errors.DataProvidingException(f'{str(err)} from {self.website_name}')


    def start_scraping(self):

        try:
          rss_content = self.fetch_rss()
          if rss_content:
            news_items = self.parse_rss(rss_content)
            print(f'number of news fetched : {len(news_items)}')
            now = datetime.now()
            logger.info(f'Crawling of {self.website_name} Started at ' + now.strftime('%a, %d %b %Y %H:%M:%S Z') + '!!')
            logger.info('+---------------------------------------------+')
            self.savegroupNews(news_items)


        except errors.DataProvidingException as err:
            logger.error(f'{str(err)} from {self.website_name}')
        except Exception as err:
            logger.error(f'{str(err)} from {self.website_name}')


