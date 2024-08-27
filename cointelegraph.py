import requests
from bs4 import BeautifulSoup
from datetime import datetime , timedelta
from html import unescape

class cointelegraphScraper(Scraper):

    def __init__(self):
        self.url = 'https://cointelegraph.com/'  
        self.name = 'cointelegraph'

    def getnews(self):
        newsItem = []
        self.soup = BeautifulSoup(self.soup, 'html.parser')
        if self.soup:
            
            articles = self.soup.find_all("article", class_="post-card__article rounded-lg")
            print(f'number  of articles found : {len(articles)}')
            for article in articles:
                link = article.find("a")["href"]
                article_url = link if link.startswith("http") else self.url + link
                article = self.loadPage(article_url)
                article = BeautifulSoup(article, "html.parser")
                
                news = {}
                
                title = article.title.string
                if title:
                    news['title'] = title.text.strip()
                

                summery = article.find("meta", attrs={"name": "description"})
                if summery:
                    news['summery'] = summery["content"]
    
                pub_date = article.find('time')
                if pub_date:
                    news['pubDate'] = pub_date['datetime']
                description = article.find('div', class_='post-content')
                if description:
                   
                    description_paragraphs = description.find_all(['p', 'h2']  , recursive=False)
                    description_text = ''.join([para.text for para in description_paragraphs])
                    news['description'] = description_text
                
                news['link'] = article_url
                
                
                category_ul = article.find('ul', class_='tags-list__list')

                
                tags_items = category_ul.find_all('li', class_='tags-list__item')

                
                news['category'] = [item.get_text(strip=True) for item in tags_items]
              
               

                img_thum_div = article.find("div", class_="post-cover__image")
                img_thum = img_thum_div.find("img" , )["src"] if img_thum_div else None
               
                if img_thum:
                    news['thImage'] = img_thum

                news['imgs'] = [img["src"] for img in description.find_all("img", attrs={"pinger-seen": "true"}, recursive=False)]

                creator = article.find('div', class_='post-meta__author-name')
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
            
            
            item['provider'] = 'cointelegraph'  
            
            
            item['summary'] = unscape(newsItem.get('summery', ''))
            
            
            item['thImage'] = newsItem.get('thImage', ' ')
            
           
            item['images'] = newsItem.get('imgs', ' ')
            
           
            item['category'] = 'cryptocurrencies'
            
            
            item['Negative'] = 0
            item['Neutral'] = 0
            item['Positive'] = 0
            
           
            creator = newsItem.get('creator')
            if not creator:
                item['author'] = item['provider']
            else:
                item['author'] = unescape(creator).strip().lower()
            
           
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

