class FinboldScraper(Scraper):

    def __init__(self, page = '1' ,back_to_back = False):
        super().__init__(f'https://finbold.com/category/cryptocurrency-news/')  
        self.page = page
        back_to_back = back_to_back

    def getnews(self):
        newsItem = []
        if self.soup:
            
            articles = self.soup.find_all("div", class_="py-5")

            for article in articles:
                link = article.find("a")["href"]
                article_url = link if link.startswith("http") else self.ProviderUrl + link
                article = self.loadPage(article_url)
                
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
                    news['pubDate'] = datetime_str = soup.find('time')['datetime']
                
                
                news['link'] = article_url
                
                
                category = article.find('a', class_='block text-blue-500 text-xs font-extrabold uppercase')
                if category:
                    news['category'] = category.text.strip()

                img_thum_div = soup.find("div", class_="main-image")
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
            item['keywords'] = [category.lower()]
            
            
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
            else:
                item['author'] = unescape(creator).strip().lower()
            
           
            item['scraped_date'] = int(datetime.now().timestamp())
            
            return item
        except errors.DataProvidingException as err:
            logger.error(f'{str(err)} from SpecificSiteScraper')
            raise errors.DataProvidingException(f'{str(err)} from SpecificSiteScraper')
        except Exception as err:
            logger.error(f'{str(err)} from SpecificSiteScraper')
            raise errors.DataProvidingException(f'{str(err)} from SpecificSiteScraper')

    def savegroupNews(self, newsItems):
        try:
            for item in newsItems:
               
                item = self.JsonItemStandard(item)
                self.saveInMongo(item)
        except requests.exceptions.ConnectionError as err:
            logger.error(f'{str(err)} from SpecificSiteScraper')
            raise errors.DataProvidingException(f'{str(err)} from SpecificSiteScraper')
        except Exception as err:
            logger.error(f'{str(err)} from SpecificSiteScraper')
            raise errors.DataProvidingException(f'{str(err)} from SpecificSiteScraper')

    
    def start_scraping(self):

        try:
            if self.back_to_back == True :
                for page in range(1,self.page):
                  
                    page = f'page/{str(page)}/'
                    self.soup = self.loadPage(self.ProviderUrl)
                    now = datetime.now()
                    logger.info('Crawling of SpecificSite Started at ' + now.strftime('%a, %d %b %Y %H:%M:%S Z') + '!!')
                    logger.info('+---------------------------------------------+')
                    if self.soup:
                        newsItems = self.getnews()
                        self.savegroupNews(newsItems)

            else:

                    page = f'page/{str(page)}/'
                    self.soup = self.loadPage(self.ProviderUrl)
                    now = datetime.now()
                    logger.info('Crawling of SpecificSite Started at ' + now.strftime('%a, %d %b %Y %H:%M:%S Z') + '!!')
                    logger.info('+---------------------------------------------+')
                    if self.soup:
                        newsItems = self.getnews()
                        self.savegroupNews(newsItems)

        except errors.DataProvidingException as err:
            logger.error(f'{str(err)} from SpecificSiteScraper')
        except Exception as err:
            logger.error(f'{str(err)} from SpecificSiteScraper')

