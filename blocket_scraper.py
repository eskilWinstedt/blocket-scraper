# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import mysql.connector
import os
import time
import urllib.request
from urllib.parse import urlparse


'''
TO DO:
    Add varchar in db for fact-window information
    Add a smart table creator depending on the search querys category
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
class Ad:
    def __init__(self, url, id, db_table):
        self.url = url
        self.id = id
        self.db_table = db_table
        self.timestamp = None
        self.location = None
        self.title = None
        self.price = None
        self.description = None

        debug("An Ad instance is initialised")

    def archive(self):
        '''Records the remove timestamp to see when the ad was removed'''
        debug("An ad has been archived in db!")
        removed_timestamp = time.localtime()

        # The archived time is inserted
        sql = "UPDATE {0} SET archived = %s WHERE ad_id = %s;".format(self.db_table)
        values = (removed_timestamp, self.id)
        db_cursor.execute(sql, values)
        db.commit()

    def _fetch(self):
        '''Fetches the an Ad and creates a soup'''
        while True:
            try:
                absolute_ad_link = 'https://beta.blocket.se' + self.url
                request = urllib.request.Request(absolute_ad_link)
                html = urllib.request.urlopen(request)
                self.soup = BeautifulSoup(html, 'html.parser')
                break
            except Exception as e:
                print("An error occured during ad fetching. Retrying in 30 seconds")
                print("Exception: " + str(e))
                time.sleep(30)

    def _get_description(self):
        '''Sets the description of the ad'''
        description = self.soup.find('div', attrs={'class': 'BodyCard__DescriptionPart-sc-15r463q-2'})
        if description:
            self.description = str(description.string)

    def _get_location(self):
        '''Sets the location of an ad if it's identified'''
        location = self.soup.find('a', attrs={'class': 'LocationInfo__StyledMapLink-sc-1op511s-3'})
        if location:
            location = self._soup_replace(location,'<!-- --> (hitta.se)')    # .string doesn't work with HTML-comments
            self.location = str(location.string)

    def _get_pictures(self):
        '''Gets all pictures from one ad and saves them in pictures/ under the name AD-ID_PICTURE-ID.jpg.
        If picture already exists, it's not downloaded again'''

        pictureboxes = self.soup.findAll('div', attrs={'class': 'LoadingAnimationStyles__PlaceholderWrapper-c75se8-0 jkleoR'}) # There are 4
        pictureboxes = pictureboxes[2]
        pictureboxes = pictureboxes.findChild()
        pictureboxes = pictureboxes.findChild()
        pictureboxes = pictureboxes.findChild()
        pictureboxes = pictureboxes.findChildren()

        start = "background-image:url("
        folder = 'pictures/'
        if not os.path.isdir(folder):
            os.mkdir(folder)
        for picturebox in pictureboxes:
            try:
                style_value = picturebox.attrs['style']     #The link is found here
            except:
                break   # If there are no pictures

            # Get the link
            start_index = style_value.find(start) + len(start)
            link = style_value[start_index:]
            end_index = link.find(")")
            link = link[:end_index]

            picture_id = get_ad_id(link)
            filepath = folder + str(self.id) + '_' + str(picture_id) + '.jpg'
            if os.path.isfile(filepath): continue   # The picture is already downloaded
            while True:
                try:
                    f = open(filepath, 'wb')
                    f.write(urllib.request.urlopen(link).read())
                    f.close()
                    break
                except Exception as e:
                    if str(e) == 'HTTP Error 404: Not Found':
                        print("404 for this link: " + link)
                        break
                    print("An error occured during ad fetching and filesaving. Retrying in 30 seconds")
                    print("Exception: " + str(e))
                    time.sleep(30)

    def _get_price(self):
        '''Sets the price of and ad if it's specified'''
        price = self.soup.find('div', attrs={'class': 'Price__StyledPrice-crp2x0-0'})
        if price:
            self.price = int("".join(c for c in str(price.string) if c in "1234567890"))

    def _get_title(self):
        '''Sets the title of the ad if it's identified'''
        title = self.soup.find('h1', attrs={'class': 'Hero__StyledSubject-sc-1mjgwl-4'})
        if title:
            self.title = str(title.string)

    def printable_line(self, data, row_length):
        data = data.replace('\n', '')
        prefix = ' |'
        data = data[: row_length - len(prefix)]
        data_length = len(' |' + data)
        number_spaces = row_length - data_length
        return ' ' + data + (' ' * number_spaces) + '|'

    def __repr__(self):
        width = 100
        print('\n')
        title = str(self.title)
        print('----' + title + '-' * (width - 4 - len(title)))
        print(self.printable_line('Price: ' + str(self.price), width))
        print(self.printable_line('Description: ' + str(self.description), width))
        print(self.printable_line('Location: ' + str(self.location), width))
        print(self.printable_line('Inlagd: ' + str(time.asctime(self.timestamp)), width))
        print('-' * width)
        print('\n')

    def _set_timestamp(self):
            '''Takes a timestamp from blocket in these formats: Idag 13:57 / Igår 03:34 / 
            I måndags hh:mm / 31 maj hh::m / 9 nov. 14:57.  Converts to a timestruct'''
            now = time.localtime()
            weekday_now = now.tm_wday

            blocket_days = ('i måndags', 'i tisdags', 'i onsdags', 'i torsdags', 'i fredags', 'i lördags', 'i söndags')
            blocket_months = ('jan.', 'feb.', 'mars', 'apr.', 'maj', 'juni', 'juli', 'aug.', 'sep.', 'okt.', 'nov.', 'dec.')

            # Fetch the timestamp and convert to string
            timestamp_raw = self.soup.find('span', attrs={'class': 'PublishedTime__StyledTime-pjprkp-1'})
            timestamp_raw = self._soup_replace(timestamp_raw, 'Inlagd: <!-- -->')
            timestamp_raw = timestamp_raw.string

            timestamp_split = timestamp_raw.split(" ")
            clock = timestamp_split[-1]
            clock = clock.split(":")
            hour = int(clock[0])
            minute = int(clock[1])
            year_day = now.tm_yday
            year = now.tm_year 
            
            if "idag" in timestamp_split or "igår" in timestamp_split:
                if "igår" in timestamp_split:
                    year_day -= 1
                    if year_day <= 0:   # year_day = 0 => last day of previous year
                        year -= 1
                        year_days = 365
                        if year % 4 == 0:   # Leap year?
                            year_days += 1
                        year_day += year_days
                self.timestamp = time.strptime("{0}:{1} {2} {3}".format(hour, minute, year_day, year), "%H:%M %j %Y")
                return

            # Weekday
            for weekday_then, blocket_day in enumerate(blocket_days):
                if blocket_day not in timestamp_raw: continue
                
                delta_days = weekday_then - weekday_now
                if delta_days >= 0:
                    delta_days -= 7

                year_day += delta_days
                if year_day <= 0:      
                    year -= 1
                    year_days = 365
                    if year % 4 == 0:
                        year_days += 1
                    year_day += year_days
                self.timestamp = time.strptime("{0}:{1} {2} {3}".format(hour, minute, year_day, year), "%H:%M %j %Y")
                return
            
            # Month day and month
            month_day = int(timestamp_split[0])
            month = timestamp_split[1]
            month_number = blocket_months.index(month) + 1

            # Has the datetime not occured yet this year? 
            if month_number > now.tm_mon:
                year -= 1
            elif month_number == now.tm_mon:
                if month_day > now.tm_mday:
                    year -= 1
                elif month_day == now.tm_mday:
                    if hour > now.tm_hour:
                        year -= 1
                    elif hour == now.tm_hour and minute > (now.tm_min + 3):     # Adding a bit of margin in case the system clock is out of tune with Blockets' servers
                        year -= 1


            self.timestamp = time.strptime("{0}:{1} {2} {3} {4}".format(hour, minute, month_day, month_number, year), "%H:%M %d %m %Y")
            return

    def _soup_replace(self, soup, remove, replace = ''):
        '''Removes and replaces a given combination of characters in a soup'''
        return BeautifulSoup(str(soup).replace(remove, replace), 'html.parser')       

    def update(self):
        '''Updates the ads db entry'''
        self._fetch()
        self._set_timestamp()
        self._get_location()
        self._get_title()
        self._get_price()
        self._get_description()
        self._get_pictures()
        self.__repr__()
        debug(self.url)
        debug(self.id)

        #Check existance
        sql = "SELECT COUNT(1) FROM {0} WHERE ad_id=%s;".format(self.db_table)
        value = (self.id,)
        db_cursor.execute(sql, value)

        for data in db_cursor:
            if data[0] == True: break
            # The data is new
            sql = "INSERT INTO {0} (url, ad_id, title, timestamp, location, price, description) VALUES (%s,%s,%s,%s,%s,%s,%s)".format(self.db_table)
            values = (self.url, self.id, self.title, self.timestamp, self.location, self.price, self.description)
            
            db_cursor.execute(sql, values)
            db.commit()
            return

        #The data needs to be updated
        sql = "UPDATE {0} SET url = %s, title = %s, location = %s, price = %s, description = %s WHERE ad_id = %s;".format(self.db_table)
        values = (self.url, self.title, self.location, self.price, self.description, self.id)
        db_cursor.execute(sql, values)
        db.commit()


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
        self._set_table_name()
        self._load_active_ads()
        self.refresh_ads(False) # false = don't fetch again

    def _ad_class(self, link, id):
        '''Depending on the category this class is searching in, different classes will be used for the ads'''
        #absolute_ad_link = 'https://beta.blocket.se' + link
        if False:
            pass
        else:
            #print('absolute ad link: ' + absolute_ad_link)
            return Ad(link, id, self.db_table)     # Returns the instance reference

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

    def refresh_ads(self, fetch=True):
        '''Finds new ads and saves them to the DB and updates newly archived ads'''
        if fetch:
            self._fetch_all()
        
        new_ad_links = []
        removed_ad_links = self.active_ad_links.copy()       # Deleting all found links until only the removed ones remain


        for page_soup in self.page_soups:
            for ad in page_soup.findAll("div", attrs={"class": "styled__Wrapper-sc-1kpvi4z-0"}):      # Loop over every ad container
                ad_link = ad["to"]
                debug("Currently processing: " + ad_link)
                
                if ad_link in self.active_ad_links:       # Attribute 'to' is the relative link to the ad
                    debug("Removing already found ad " + ad_link)
                    removed_ad_links.remove(ad_link)
                else:   # The ad is new or has changed name
                    self.active_ad_links.append(ad_link)
                    new_ad_links.append(ad_link)
                    ad_id = get_ad_id(ad_link)
                    if ad_id in self.ad_ids:   # The ads title (and likely more) has been changed
                        debug("THE AD NAME HAS BEEN CHANGED")
                        warning("UPDATE THE AD IN THE DATABASE")
                        ad_instance = self._ad_class(ad_link, ad_id)
                        ad_instance.update()
                    else:
                        debug("New ad's id: " + str(ad_id))
                        self.active_ad_links.append(ad_link)
                        self.ad_ids.append(int(ad_id))
                        ad_instance = self._ad_class(ad_link, ad_id)
                        ad_instance.update()
                        debug("Active ad ids: {0}".format(len(self.ad_ids)))
        
        debug("\n\nAll ads have been fetched\n\n")
        
        for removed_ad_link in removed_ad_links:        # Remove removed_links from active_links
            debug('Removed ' + removed_ad_link)
            self.active_ad_links.remove(removed_ad_link)
            ad_id = get_ad_id(removed_ad_link)
            debug('Removed ad id: ' + str(ad_id))
            self.ad_ids.remove(ad_id)
            ad_instance = self._ad_class(removed_ad_link, ad_id)
            ad_instance.archive()

    def _set_table_name(self):
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
            # All columns are based on blocket's limits plus extra bytes for >1 byte chars
            columns = "url VARCHAR(255), ad_id INT PRIMARY KEY, title VARCHAR(70), timestamp DATETIME(0), archived DATETIME(0), location VARCHAR(80), price INT, description VARCHAR(4000)"
            db_cursor.execute("CREATE TABLE {0} ({1})".format(self.db_table, columns))
        else:
            # Load data from it
            db_cursor.execute("SELECT url, ad_id FROM {0} WHERE archived IS NULL".format(self.db_table))
            for data in db_cursor:
                self.active_ad_links.append(data[0])
                self.ad_ids.append(data[1])
            debug(self.active_ad_links)
            debug(self.ad_ids)


# --- MAIN ---------------

# Connnect to MySQL
db = mysql.connector.connect(
    host = DB_HOST,
    user = DB_USER,
    passwd = DB_PASSWD
)

db_cursor = db.cursor(buffered=True)
db_cursor.execute("CREATE DATABASE IF NOT EXISTS {0}".format(DB_NAME))
db_cursor.execute("USE {0}".format(DB_NAME))

bugs = MonitoredCategory('https://www.blocket.se/annonser/hela_sverige/fordon/bilar?cb=40&cbl1=17&cg=1020')

update_timer = 60 * 7
while True:
    bugs.refresh_ads()
    time.sleep(update_timer)