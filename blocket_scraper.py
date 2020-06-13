# -*- coding: utf-8 -*-
import urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import mysql.connector

# --- OPTIONS ---------------------
DEBUG_MODE = True

# ------ DATABASE CONFIGURATION CONSTANTS --------------------
DB_NAME = "blocket_scraper"
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWD = "ANC:s viktiga partikongress"

def debug(msg):
    global DEBUG_MODE
    if DEBUG_MODE:
        print(msg)

class MonitoredCategory:
    def __init__(self, url):
        # All properties are defined here to make them easier to locate
        self.url = url
        self.headers = {}
        self.categories = []
        self.table = ""     # The name of the SQL table
        self.ads = {}

        self._fetch_all()
        self._get_categories()
        self._get_table_name()
        self._load_active_ads()
        self.refresh_ads(False)

    def _fetch(self, url):
        '''Takes an url to a page as the argument, fetches the page and returns it as a soup'''
        while True:
            request = urllib.request.Request(url, headers = self.headers)
            try:
                html = urllib.request.urlopen(request)
                return BeautifulSoup(html, "html.parser")
            except urllib.error.URLError as e:
                print("An error occured during fetching. Please check your internet connection. Retrying in 30 seconds")
                debug("Exception: " + str(type(e)))
                time.sleep(30)

    def _fetch_all(self):
        '''Fetches all pages in one category and saves them as soups in a list where every element is one page'''
        self.page_soups = [self._fetch(self.url + '&page=100')]
        page_nav_div = self.page_soups[0].find("div", attrs={"class": "Pagination__Buttons-uamu6s-3"})      # Get the div with the page-nav buttons
        number_pages = 1
        if page_nav_div:
            number_pages = int(page_nav_div.find_all('a')[-1].string)       # Gets the last page number
        
        for page_number in range(1, number_pages):
            page_link = self.url + "&page=" + str(page_number)
            self.page_soups.append(self._fetch(page_link))
            debug("sidnummer: " + page_number)

    def _get_categories(self):
        '''Gets the categories from blocket'''
        nav_list = self.page_soups[0].find("ol", attrs={"class": "ljRioT"})
        nav_list_items = nav_list.find_all("li", attrs={"class": "swInF"})
        for nav_list_item in nav_list_items:
            self.categories.append(nav_list_item.find("div").string.lower())
        debug(self.categories)

    def _get_table_name(self):
        '''Gets the MySQL table from the categories'''
        self.table = self.categories[1]
        for i in range(2, len(self.categories)):
            self.table += "_" + self.categories[i]
        debug(self.table)

    def _load_active_ads(self):
        '''Tries to locate the category's table if it exists to load the ads'''
        db_cursor.execute("SHOW TABLES")

        missing = True
        for table in db_cursor:
            if table[0] == self.table:
                missing = False
                break

        if missing:
            debug("Created table " + self.table)
            db_cursor.execute("CREATE TABLE {0} (url VARCHAR(255), ad_id INTEGER(15), archived BOOLEAN, unique_id INTEGER AUTO_INCREMENT PRIMARY KEY)".format(self.table))
        else:
            # TRY TO LOAD DATA FROM IT!!!
            db_cursor.execute("SELECT url, ad_id FROM {0} WHERE archived = false".format(self.table))
            debug(db_cursor)
            for data in db_cursor:
                debug(data)

    def refresh_ads(self, fetch=True):
        '''Finds new ads and saves them to the DB and updates newly archived ads'''
        '''self.new_ad_links = []
        self.newly_removed_ad_links = self.active_ad_links.copy()        # Deleting all found links until only the removed ones remain
        for page_soup in self.page_soups:
            # Loop over every ad container
            for ad in page_soup.findAll('div', attrs={'class': 'styled__Wrapper-sc-1kpvi4z-0'}):
                if ad['to'] in self.active_ad_links:       # Attribute 'to' is the relative link to the ad
                    self.newly_removed_ad_links.remove(ad['to'])        
                else:   # The ad is new or has changed name
                    self.active_ad_links.append(ad['to'])
                    self.new_ad_links.append(ad['to'])
                    ad_id = get_ad_id(ad['to'])
                    if ad_id in selgit f.ads:   # The ad already exists?
                        # Update the ad so the new name will be saved!
                        print('THE AD NAME HAS BEEN CHANGED')
                        self.ads[ad_id].update()
                    else:
                        print('This ad is new')
                        print('Ad id: ' + ad_id)
                        self.ads[ad_id] = self.ad_class(ad['to'])  # Using different classes for the ads depending on their categories
                        print(str(self.ad_class(ad['to']).url))
                        print(len(self.ads))
        print('Nu är jag här')
        for key in self.ads:
            self.ads[key].__repr__()
        self.removed_ad_links += self.newly_removed_ad_links
        for removed_link in self.newly_removed_ad_links:        # Remove removed_links from active_links
            print('Removed ' + removed_link)
            self.active_ad_links.remove(removed_link)
            ad_id = get_ad_id(removed_link)
            try:
                self.ads[ad_id].archive()
            except KeyError:
                print("This ad was removed during this and the most recent session. No data has been saved and, therefore, the ad can not be archived.")'''
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