# -*- coding: utf-8 -*-
import urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import mysql.connector

'''
TO DO:
    Ad fetching
'''


# --- OPTIONS ---------------------
DEBUG_MODE = True


# --- ADDITIONAL IMPORTS ------------------
if DEBUG_MODE:
    from inspect import currentframe, getframeinfo


# --- DATABASE CONFIGURATION CONSTANTS --------------------
DB_NAME = "blocket_scraper"
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWD = "ANC:s viktiga partikongress"


# --- FUNCTIONS ------------------
def debug(msg, display_line_nr = False):
    global DEBUG_MODE
    if not DEBUG_MODE: return
    if display_line_nr:
        line_nr = getframeinfo(currentframe()).lineno
        print("{0}: {1}".format(line_nr, msg))
    else:
        print(msg)

def warning(msg):
    global DEBUG_MODE
    if not DEBUG_MODE: return
    line_nr = getframeinfo(currentframe()).lineno
    print("A WARNING HAS BEEN RAISED ON LINE {0} WITH THE MESSAGE: {1}".format(line_nr, msg))

def get_ad_id(ad_link):
    '''Gets the unique ad id from the ad link '''
    return int(ad_link.split('/')[-1].split('.')[0])


# --- CLASSES -------------
class MonitoredCategory:
    def __init__(self, url):
        # All properties are defined here to make them easier to locate
        self.url = url
        self.headers = {}
        self.categories = []
        self.db_table = ""     # The name of the SQL table
        self.ad_ids = []
        self.active_ad_links = []

        self._fetch_all()
        self._get_categories()
        self._get_table_name()
        self._load_active_ads()
        self.refresh_ads(False) # false = don't fetch again

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
        page_nav_div = self.page_soups[0].find("div", attrs={"class": "Pagination__Buttons-uamu6s-5"})      # Get the div with the page-nav buttons
        number_pages = 1
        if page_nav_div:
            number_pages = int(page_nav_div.find_all('a')[-1].string)       # Gets the last page number

        for page_number in range(1, number_pages):
            page_link = self.url + "&page=" + str(page_number)
            self.page_soups.append(self._fetch(page_link))
        debug("{0} pages were fetched".format(len(self.page_soups)))

    def _get_categories(self):
        '''Gets the categories from blocket'''
        nav_list = self.page_soups[0].find("ol", attrs={"class": "ljRioT"})
        nav_list_items = nav_list.find_all("li", attrs={"class": "swInF"})
        for nav_list_item in nav_list_items:
            self.categories.append(nav_list_item.find("div").string.lower())
        debug(self.categories)

    def _get_table_name(self):
        '''Gets the MySQL table from the categories'''
        self.db_table = self.categories[1]
        for i in range(2, len(self.categories)):
            self.db_table += "_" + self.categories[i]
        debug(self.db_table)

    def _load_active_ads(self):
        '''Tries to locate the category's table if it exists to load the ads'''
        db_cursor.execute("SHOW TABLES")

        missing = True
        for table in db_cursor:
            if table[0] == self.db_table:
                missing = False
                break

        if missing:
            debug("Created table " + self.db_table)
            db_cursor.execute("CREATE TABLE {0} (url VARCHAR(255), ad_id INTEGER(15), archived BOOLEAN, unique_id INTEGER AUTO_INCREMENT PRIMARY KEY)".format(self.db_table))
        else:
            # TRY TO LOAD DATA FROM IT!!!
            db_cursor.execute("SELECT url, ad_id FROM {0} WHERE archived = false".format(self.db_table))
            for data in db_cursor:
                self.active_ad_links.append(data[0])
                self.ad_ids.append(data[1])
            debug(self.active_ad_links)
            debug(self.ad_ids)

    def refresh_ads(self, fetch=True):
        '''Finds new ads and saves them to the DB and updates newly archived ads'''
        if fetch:
            self._fetch_all()
        
        new_ad_links = []
        removed_ad_links = self.active_ad_links.copy()       # Deleting all found links until only the removed ones remain


        for page_soup in self.page_soups:
            for ad in page_soup.findAll("div", attrs={"class": "styled__Wrapper-sc-1kpvi4z-0"}):                    # Loop over every ad container
                debug("Currently processing: " + ad["to"])
                if ad["to"] in self.active_ad_links:       # Attribute 'to' is the relative link to the ad
                    debug("Removing already found ad" + ad["to"])
                    removed_ad_links.remove(ad["to"])
                else:   # The ad is new or has changed name
                    self.active_ad_links.append(ad["to"])
                    new_ad_links.append(ad["to"])
                    ad_id = get_ad_id(ad["to"])
                    if ad_id in self.ad_ids:   # The ads titel (and maybe more) has been changed
                        debug("THE AD NAME HAS BEEN CHANGED")
                        warning("UPDATE THE AD IN THE DATABASE")
                        #self.ad_ids[ad_id].update()
                    else:
                        debug("New ad's id: " + str(ad_id))
                        self.active_ad_links.append(ad["to"])
                        self.ad_ids.append(int(ad_id))
                        warning("INSERT THE AD INTO THE DATABASE")
                        #self.ad_ids[ad_id] = self.ad_class(ad["to"])  # Using different classes for the ads depending on their categories
                        debug("Active ad ids: {0}".format(len(self.ad_ids)))
        
        debug("\n\nAll ads have been fetched\n\n")
        
        for removed_ad_link in removed_ad_links:        # Remove removed_links from active_links
            debug('Removed ' + removed_ad_link)
            self.active_ad_links.remove(removed_ad_link)
            ad_id = get_ad_id(removed_ad_link)
            debug('Removed ad id: ' + str(ad_id))
            self.ad_ids.remove(ad_id)
            warning("UPDATE THE AD IN THE DATABASE SO ARCHIVED = true")

    def _save_ad(self, url):
        '''Saves an ad from its URL in the table located by the ads categories'''
        pass
        # 1. Fetch all standard data
        # 2. Fetch other data depending on the ads table/categories (same result)
        # 3. See if the ad has an earlier record. Update or insert?


# --- MAIN ---------------

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

input('exit')