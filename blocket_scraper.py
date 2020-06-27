# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import mysql.connector
import os
import time
import urllib.request
from urllib.parse import urlparse



'''
TO DO:
    Test timestamp method
    Fix preliminary update method
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
    def __init__(self, url, id):
        self.url = url
        self.id = id
        self.timestamp = None
        self.removed_timestamp = None
        self.location = None
        self.title = None
        self.price = None
        self.description = None
        self.picture_links = {}

        debug("An Ad instance is initialised")
        #self.update()

    def archive(self):
        '''Records the remove timestamp to see when the ad was removed'''
        print("An ad has been removed!")
        self.removed_timestamp = time.localtime()

    def _fetch(self):
        '''Fetches the an Ad and creates a soup'''
        while True:
            try:
                request = urllib.request.Request(self.url)
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
            self.description = description.string  

    def _get_location(self):
        '''Sets the location of an ad if it's identified'''
        location = self.soup.find('a', attrs={'class': 'LocationInfo__StyledMapLink-sc-1op511s-3'})
        if location:
            location = self._soup_replace(location,'<!-- --> (hitta.se)')    # .string doesn't work with HTML-comments
            self.location = location.string 

    def _get_pictures(self):
        '''Gets all pictures from one ad and saves them in pictures/ under the name AD-ID_PICTURE-ID.jpg.
        If picture already exists, it's not downloaded again'''

        pictureboxes = self.soup.findAll('div', attrs={'class': 'LoadingAnimationStyles__PlaceholderWrapper-c75se8-0 jkleoR'}) # There are 4
        pictureboxes = pictureboxes[2]
        debug(pictureboxes)
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
            self.picture_links[link] = filepath
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
        debug(self.picture_links)

    def _get_price(self):
        '''Sets the price of and ad if it's specified'''
        price = self.soup.find('div', attrs={'class': 'Price__StyledPrice-crp2x0-0'})
        if price:
            self.price = price.string

    def _get_title(self):
        '''Sets the title of the ad if it's identified'''
        title = self.soup.find('h1', attrs={'class': 'Hero__StyledSubject-sc-1mjgwl-4'})
        if title:
            self.title = title.string

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
        print(self.printable_line('Inlagd: ' + str(time.ctime(self.timestamp)), width))
        print('-' * width)
        print('\n')

    def _set_timestamp(self):
            '''Takes a timestamp from blocket in these formats: Idag 13:57 / Igår 03:34 / 
            I måndags hh:mm / 31 maj hh::m / 9 nov. 14:57.  Converts to time in seconds if a timestamp is identified'''

            # Fetch the timestamp and convert to string
            raw_timestamp = self.soup.find('span', attrs={'class': 'PublishedTime__StyledTime-pjprkp-1'})
            raw_timestamp = self._soup_replace(raw_timestamp, 'Inlagd: <!-- -->')
            raw_timestamp = raw_timestamp.string

            timestamp_parts = raw_timestamp.split(' ')      # example: ['21', 'okt', '04:39]
            # Clock (hh:mm)
            clock = timestamp_parts[-1]     # '04:39'
            clock = clock.split(':')    # ['04', '39']
            clock = list(map(int, clock))   # [4, 39]
            debug("clock: " + str(clock))

            # Current times
            seconds_now = time.time()  # Tinme since beginning of time in seconds
            time_now = time.localtime()   # A tuple with year, month, day, weekday etc.
            clock_now_seconds = time_now[3] * 3600 + time_now[4] * 60 + time_now[5]
            weekday_now = time_now[6]   # Weekday in numbers. Monday is 0
            
            seconds_now_no_clock = seconds_now - clock_now_seconds
            timestamp = seconds_now_no_clock + clock[0] * 3600 + clock[1] * 60 # Adding the hours and minutes from the ad
            
            blocket_days = ['i måndags', 'i tisdags', 'i onsdags', 'i torsdags', 'i fredags', 'i lördags', 'i söndags']
            blocket_months = ['jan.', 'feb.', 'mars', 'apr.', 'maj', 'juni', 'juli', 'aug.', 'sep.', 'okt.', 'nov.', 'dec.']
            
            if 'idag' in  raw_timestamp:    
                self.timestamp = timestamp
            elif 'igår' in raw_timestamp:
                self.timestamp = timestamp - 3600 * 24
            else:
                # Check for day
                for weekday_then, blocket_day in enumerate(blocket_days):
                    if blocket_day in raw_timestamp:
                        if weekday_now > weekday_then:
                            days_since = weekday_now - weekday_then
                        else:
                            days_since = weekday_now - weekday_then + 7  
                                              
                        seconds_since = 3600 * 24 * days_since
                        self.timestamp = timestamp - seconds_since
                        debug("Blocket timestamp: {0}. Converted timestamp: {1}".format(raw_timestamp, str(time.ctime(self.timestamp))))
                        return
                
                # Check for month
                for month_index, blocket_month in enumerate(blocket_months):
                    debug("Month index: " + str(month_index))
                    debug("Blocket index: " + blocket_month)
                    if blocket_month in raw_timestamp:
                        month_number = month_index + 1
                        timestamp_parts[0] = int(timestamp_parts[0])
                        year = time_now.tm_year
                        debug("Month number now: " + str(time_now.tm_mon))
                        debug("Blocket time month number: " + str(month_number))
                        if month_number > time_now.tm_mon:
                            year -= 1
                        elif timestamp_parts[0] > time_now.tm_mday:
                            year -= 1
                            # There are no blocket ads close to one year old!
                            print('WARNING!')
                            print('This blocket date was older than expected: ' + raw_timestamp)
                        
                        month_day = timestamp_parts[0]
                        time_tuple = (year, month_number, month_day, clock[0], clock[1], 0, 0, 1, -1) # year, month, month_day, hours, minutes, seconds, week_day, year_day, daylight_savings (-1=auto).  Week_day and year_day doesn't make any difference 
                        self.timestamp = time.mktime(time_tuple)
                        debug("Blocket timestamp: {0}. Converted timestamp: {1}".format(raw_timestamp, str(time.ctime(self.timestamp))))
                        return
                
                # The timestamp could not be set
                print('AN error has occurred.')
                print('This blocket date was not recognized: ' + raw_timestamp)

    def _soup_replace(self, soup, remove, replace = ''):
        '''Removes and replaces a given combination of characters in a soup'''
        return BeautifulSoup(str(soup).replace(remove, replace), 'html.parser')       

    def update(self):
        '''Updates the ads data'''
        self._fetch()
        #self._set_timestamp()
        #self._get_location()
        self._get_title()
        self._get_price()
        self._get_description()
        self._get_pictures()
        self.__repr__()
        debug(self.url)
        debug(self.id)
        db_cursor.execute("UPDATE `blocket_scraper`.`fordon_bilar_volkswagen_bubbla` SET `url` = \"{0}\" WHERE `ad_id` = {1};".format(self.url, self.id))
        for data in db_cursor:
            debug(data)


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
        absolute_ad_link = 'https://beta.blocket.se' + link
        if False:
            pass
        else:
            print('absolute ad link: ' + absolute_ad_link)
            return Ad(absolute_ad_link, id)     # Returns the instance reference

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
            for ad in page_soup.findAll("div", attrs={"class": "styled__Wrapper-sc-1kpvi4z-0"}):                    # Loop over every ad container
                ad_link = ad["to"]
                debug("Currently processing: " + ad_link)
                if ad_link in self.active_ad_links:       # Attribute 'to' is the relative link to the ad
                    debug("Removing already found ad " + ad_link)
                    removed_ad_links.remove(ad_link)
                else:   # The ad is new or has changed name
                    self.active_ad_links.append(ad_link)
                    new_ad_links.append(ad_link)
                    ad_id = get_ad_id(ad_link)
                    if ad_id in self.ad_ids:   # The ads titel (and maybe more) has been changed
                        debug("THE AD NAME HAS BEEN CHANGED")
                        warning("UPDATE THE AD IN THE DATABASE")
                        ad_instance = self._ad_class(ad_link, ad_id)
                        ad_instance.update()
                        #self.ad_ids[ad_id].update()
                    else:
                        debug("New ad's id: " + str(ad_id))
                        self.active_ad_links.append(ad_link)
                        self.ad_ids.append(int(ad_id))
                        warning("INSERT THE AD INTO THE DATABASE")
                        #self.ad_ids[ad_id] = self._ad_class(ad_link)  # Using different classes for the ads depending on their categories
                        debug("Active ad ids: {0}".format(len(self.ad_ids)))
        
        debug("\n\nAll ads have been fetched\n\n")
        
        for removed_ad_link in removed_ad_links:        # Remove removed_links from active_links
            debug('Removed ' + removed_ad_link)
            self.active_ad_links.remove(removed_ad_link)
            ad_id = get_ad_id(removed_ad_link)
            debug('Removed ad id: ' + str(ad_id))
            self.ad_ids.remove(ad_id)
            warning("UPDATE THE AD IN THE DATABASE SO ARCHIVED = true")

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
            db_cursor.execute("CREATE TABLE {0} (url VARCHAR(255), ad_id INTEGER(15) AUTO_INCREMENT PRIMARY KEY, archived BOOLEAN)".format(self.db_table))
        else:
            # TRY TO LOAD DATA FROM IT!!!
            db_cursor.execute("SELECT url, ad_id FROM {0} WHERE archived = false".format(self.db_table))
            for data in db_cursor:
                self.active_ad_links.append(data[0])
                self.ad_ids.append(data[1])
            debug(self.active_ad_links)
            debug(self.ad_ids)

    '''def _save_ad(self, url):
        ''''''Saves an ad from its URL in the table located by the ads categories''''''
        pass
        # 1. Fetch all standard data

        # Set class.
        # Run methods inside class depending on operation
        # Destroy instance 



        # 2. Fetch other data depending on the ads table/categories (same result)
        # 3. See if the ad has an earlier record. Update or insert?'''


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