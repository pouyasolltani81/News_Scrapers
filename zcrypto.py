import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime , timedelta

class ZycryptoScrapper(scraper):
    def __init__(self, mongo_uri, db_name, collection_name, base_url ='https://zycrypto.com/' , rss_url = "https://zycrypto.com/feed/"):
        super().__init__(mongo_uri, db_name, collection_name)
        self.base_url = base_url
        self.name = 'zycrypto'
        self.rss_url = rss_url
        self.unwanted_text = ['Disclaimer: This is a sponsored article, and views in it do not represent those of, nor should they be attributed to, ZyCrypto. Readers should conduct independent research before taking any actions related to the company, product, or project mentioned in this piece; nor can this article be regarded as investment advice. Please be aware that trading cryptocurrencies involve substantial risk as the volatility of the crypto market can lead to significant losses.',
                              'Join BlockDAG Presale Now:', 'Website: https://blockdag.network' , 'Presale: https://purchase.blockdag.network' , 'Telegram: https://t.me/blockDAGnetworkOfficial' ,
                               'Discord: https://discord.gg/Q7BxghMVyu', 'Learn more:' , 'Buy Presale' , 'Visit DTX Website' ,'Join The DTX Community'
        ]


    def clean_content(self, content):
      if self.unwanted_text in content:
          content = content.replace(self.unwanted_text, "").strip()
      return content






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


            description_text = soup_d.get_text()
            content_text = '\n'.join(p.get_text() for p in soup_c.find_all(['p', 'h2']))
            content_text = self.clean_content(content_text)
            news['summery'] = description_text.strip()
            news['content'] =  content_text.strip()


            images = [img['src'] for img in soup_c.find_all('img') if 'src' in img.attrs]
            news['images'] = images


            # news['thImage'] = item.find('enclosure')['url'] if item.find('enclosure') else (images[0] if images else '')
            news['thImage'] = soup_d.find('img')['src']

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


            item['title'] = newsItem.get('title', '')

            item['articleBody'] = newsItem.get('content', '')


            item['pubDate']  = newsItem.get('timestamp')


            category = newsItem.get('category', '')
            item['keywords'] = [keyword.lower() for keyword in category]


            item['link'] = newsItem.get('link', '')


            item['provider'] = 'zycrypto'


            item['summary'] = newsItem.get('summery', '')


            item['thImage'] = newsItem.get('thImage', ' ')


            item['images'] = newsItem.get('images', ' ')


            item['category'] = 'cryptocurrency'


            item['Negative'] = 0
            item['Neutral'] = 0
            item['Positive'] = 0


            creator = newsItem.get('author')
            if not creator:
                item['author'] = item['provider']
            


            item['scraped_date'] = int(datetime.now().timestamp())

            return item
        except errors.DataProvidingException as err:
            logger.error(f'{str(err)} from {self.name}Scraper')
            raise errors.DataProvidingException(f'{str(err)} from {self.name}Scraper')
        except Exception as err:
            logger.error(f'{str(err)} from {self.name}Scraper')
            raise errors.DataProvidingException(f'{str(err)} from {self.name}Scraper')

    def savegroupNews(self, newsItems):
        try:
            for item in newsItems:

                item = self.JsonItemStandard(item)
                self.saveInMongo(item)
        except requests.exceptions.ConnectionError as err:
            logger.error(f'{str(err)} from {self.name}Scraper')
            raise errors.DataProvidingException(f'{str(err)} from {self.name}Scraper')
        except Exception as err:
            logger.error(f'{str(err)} from {self.name}Scraper')
            raise errors.DataProvidingException(f'{str(err)} from {self.name}Scraper')


    def start_scraping(self):

        try:
          rss_content = self.loadPage(self.rss_url)
          if rss_content:
            news_items = self.parse_rss(rss_content)
            print(f'number of news fetched : {len(news_items)}')
            now = datetime.now()
            logger.info(f'Crawling of {self.name} Started at ' + now.strftime('%a, %d %b %Y %H:%M:%S Z') + '!!')
            logger.info('+---------------------------------------------+')
            self.savegroupNews(news_items)


        except errors.DataProvidingException as err:
            logger.error(f'{str(err)} from {self.name}Scraper')
        except Exception as err:
            logger.error(f'{str(err)} from {self.name}Scraper')

