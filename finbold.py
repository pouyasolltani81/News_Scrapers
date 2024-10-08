import requests
from bs4 import BeautifulSoup
from datetime import datetime , timedelta
from html import unescape

class FinboldScraper(Scraper):

    def __init__(self, page = '1' ,back_to_back = False):
        self.url = 'https://finbold.com/category/cryptocurrency-news/'  
        self.page = page
        self.name = 'finbold'
        back_to_back = back_to_back

    def getnews(self):
        newsItem = []
        self.soup = BeautifulSoup(self.soup, 'html.parser')
        if self.soup:
            
            articles = self.soup.find_all("div", class_="py-5")

            for article in articles:
                link = article.find("a")["href"]
                article_url = link if link.startswith("http") else self.url + link
                article = self.loadPage(article_url)
                article = BeautifulSoup(response.content, "html.parser")
                
                news = {}
                
                title = article.find('h1', class_ = 'entry-title')
                if title:
                    news['title'] = title.text.strip()
                
                description = article.find('article', class_='status-publish')
                if description:
                   
                    description_paragraphs = description.find_all(['p', 'h2'])
                    description_text = ''.join([para.text for para in description_paragraphs])
                    news['description'] = description_text
    
                pub_date = article.find('time')
                if pub_date:
                    news['pubDate'] = pub_date['datetime']
                
                
                news['link'] = article_url
                
                
                category = article.find('a', class_='block text-blue-500 text-xs font-extrabold uppercase')
                if category:
                    news['category'] = category.text.strip()

                img_thum_div = article.find("div", class_="main-image")
                img_thum = img_thum_div.find("img")["src"] if img_thum_div else None
               
                if img_thum:
                    news['thImage'] = img_thum

                news['imgs'] = [img["src"] for img in description.find_all("img")]

                creator = article.find('span', class_='author')
                if creator:
                    news['creator'] = creator.text.strip()

                newsItem.append(news)
        
        return newsItem

    def JsonItemStandard(self, newsItem):
        try:
            item = {}
            
            
            item['title'] = unescape(newsItem.get('title', ''))
            
            item['articleBody'] = unescape(newsItem.get('description', ''))
            
            
            pubDate = newsItem.get('pubDate')
            if pubDate:
                currentDate = datetime.strptime(pubDate, '%Y-%m-%dT%H:%M:%S%z')  
                item['pubDate'] = int(currentDate.timestamp())
            else:
                item['pubDate'] = int(datetime.now().timestamp())
            
            
            category = newsItem.get('category', '')
            item['keywords'] = [keyword.lower() for keyword in category]
            
            
            item['link'] = newsItem.get('link', '')
            
            
            item['provider'] = 'finbold'  
            
            
            item['summary'] = ''
            
            
            item['thImage'] = newsItem.get('thImage', ' ')
            
           
            item['images'] = newsItem.get('imgs', ' ')
            
           
            item['category'] = 'cryptocurrencies'
            
            
            item['Negative'] = 0
            item['Neutral'] = 0
            item['Positive'] = 0
            
           
            creator = newsItem.get('creator')
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
            if self.back_to_back == True :
                for page in range(1,self.page):
                  
                    page = f'page/{str(page)}/'
                    self.soup = self.loadPage(self.url)
                    now = datetime.now()
                    logger.info(f'Crawling of {self.name} Started at ' + now.strftime('%a, %d %b %Y %H:%M:%S Z') + '!!')
                    logger.info('+---------------------------------------------+')
                    if self.soup:
                        newsItems = self.getnews()
                        self.savegroupNews(newsItems)

            else:

                    page = f'page/{str(page)}/'
                    self.soup = self.loadPage(self.url)
                    now = datetime.now()
                    logger.info(f'Crawling of {self.name} Started at ' + now.strftime('%a, %d %b %Y %H:%M:%S Z') + '!!')
                    logger.info('+---------------------------------------------+')
                    if self.soup:
                        newsItems = self.getnews()
                        self.savegroupNews(newsItems)

        except errors.DataProvidingException as err:
            logger.error(f'{str(err)} from {self.name}Scraper')
        except Exception as err:
            logger.error(f'{str(err)} from {self.name}Scraper')

