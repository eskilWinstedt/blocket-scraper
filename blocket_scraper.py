# -*- coding: utf-8 -*-
import urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import mysql.connector

# ------ DATABASE CONFIGURATION CONSTANTS --------------------
DB_NAME = "blocket_scraper"
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWD = "ANC:s viktiga partikongress"

class MonitoredCategory:
    def __init__(self, url):
        # All properties are defined here to make them easier to locate
        self.url = url
        self.categories = []
        self.table = ""     # The name of the SQL table
        self.ads = {}

        self._fetch_all()
        self._get_categories()
        self._get_table()
        self._load_active_ads()
        self.refresh_ads(False)

    def _fetch(self, url):
        '''Takes an url to a page as the argument, fetches the page and returns it as a soup'''
        return soup

    def _fetch_all(self):
        '''Fetches all pages in one category and saves them as soups in a list where every element is one page'''
        pass

    def _get_categories(self):
        '''Gets the categories from blocket'''
        pass # category     # In list form with the first category first example ['alla', 'fordon', 'bilar', 'Volkswagen', 'Bubbla']
    
    def _get_table(self):
        '''Gets the MySQL table from the categories'''
        pass
    
    def _load_active_ads(self):
        '''Tries to locate the category's table if it exists to load the ads'''
        pass
        # CREATE THE TABLE NAME

        # LOOK FOR IT

        # 1: LOAD FROM IT. LOAD URL AND ID

        # 2: CREATE IT

    def refresh_ads(self, fetch=True):
        '''Finds new ads and saves them to the DB and updates newly archived ads'''
        pass

    def _save_ad(self, url):
        '''Saves an ad from its URL in the table located by the ads categories'''
        pass
        # 1. Fetch all standard data
        # 2. Fetch other data depending on the ads table/categories (same result)
        # 3. See if the ad has an earlier record. Update or insert?

# Connnect to MySQL
db = mysql.connector.connect(
    host = DB_HOST,
    user = DB_USER,
    passwd = DB_PASSWD
)

db_cursor = db.cursor(buffered=True)

db_cursor.execute("SHOW DATABASES")
exists = False

for database in db_cursor:
    if database[0] == DB_NAME:
        exists = True
        break

if not exists:
    db_cursor.execute("CREATE DATABASE {0}".format(DB_NAME))

db_cursor.execute("USE {0}".format(DB_NAME))

headers = {}
headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:48.0) Gecko/20100101 Firefox/48.0'
bugs = MonitoredCategory('https://www.blocket.se/annonser/hela_sverige/fordon/bilar?cb=40&cbl1=17&cg=1020')