import requests
import logging
from utils import errors
from datetime import datetime
from abc import ABC, abstractmethod
from NewsAppModel.models import NewsModel
from html import unescape
from bs4 import BeautifulSoup

logger = logging.getLogger('Rotating Log')

class Scraper(ABC):
    def __init__(self, url):
        self.ProviderUrl = url
        self.xmlData = None
        self.newsOBJ = NewsModel()

    def loadPage(self, url):
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
            }
            resp = requests.get(url, timeout=3, headers=headers)
            if resp.status_code == 200:
                # Parse the content with BeautifulSoup
                self.soup = BeautifulSoup(resp.content, 'html.parser')
                return self.soup
            else:
                logger.error('Failed to retrieve page. Status code: %d', resp.status_code)
                return -1

        except requests.exceptions.HTTPError as htError:
            logger.error('Http Error: %s', str(htError))
            raise errors.DataProvidingException(f'Http Error: {str(htError)}')

        except requests.exceptions.ConnectionError as coError:
            logger.error('Connection Error: %s', str(coError))
            raise errors.DataProvidingException(f'Connection Error: {str(coError)}')

        except requests.exceptions.Timeout as timeOutError:
            logger.error('TimeOut Error: %s', str(timeOutError))
            raise errors.DataProvidingException(f'TimeOut Error: {str(timeOutError)}')

        except requests.exceptions.RequestException as ReError:
            logger.error('Something went wrong: %s', str(ReError))
            raise errors.DataProvidingException(f'Something went wrong: {str(ReError)}')


    
    def saveInMongo(self, item):
        try:
            resp = self.newsOBJ.save_to_DB(item)
            dt = datetime.now()
            logger.info(f"Save in MongoDB done {resp} from source at {dt}")
            return resp
        except requests.exceptions.ConnectionError as er:
            raise errors.DataProvidingException(f'Database error: {str(er)}')
        except Exception as err:
            raise errors.DataProvidingException(str(err))

    def checkForExist(self, link, title, author):
        try:
            return self.newsOBJ.find_by_Link(link, title, author)
        except requests.exceptions.ConnectionError as err:
            raise errors.DataProvidingException(str(err))
        except Exception as err:
            raise errors.DataProvidingException(str(err))

    @abstractmethod
    def JsonItemStandard(self, newsItem):
        pass



