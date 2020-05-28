# -*- coding: utf-8 -*-
import urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import os
import pickle


def format2filename(filename):
    return ''.join([i for i in filename if not (i in ['.', '\\', '/', ':', '*', '?', '"', '<', '>', '|'])])

def get_ad_id(ad_link):
    '''Gets the unique ad id from the ad link '''
    return ad_link.split('/')[-1].split('.')[0]


class Ad:
    def __init__(self, url):
        self.url = url
        self.id = get_ad_id(url)
        self.timestamp = None
        self.removed_timestamp = None
        self.location = None
        self.title = None
        self.price = None
        self.description = None
        self.picture_links = {}

        print("I'm called")
        self.update()

    def fetch(self):
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
    
    def soup_replace(self, soup, remove, replace = ''):
        '''Removes and replaces a given combination of characters in a soup'''
        return BeautifulSoup(str(soup).replace(remove, replace), 'html.parser')

    def set_timestamp(self):
            '''Takes a timestamp from blocket in these formats: Idag 13:57 / Igår 03:34 / 
            I måndags hh:mm / 31 maj hh::m / 9 nov. 14:57.  Converts to time in seconds if a timestamp is identified'''

            # Fetch the timestamp and convert to string
            raw_timestamp = self.soup.find('span', attrs={'class': 'PublishedTime__StyledTime-pjprkp-1'})
            raw_timestamp = self.soup_replace(raw_timestamp, 'Inlagd: <!-- -->')
            raw_timestamp = raw_timestamp.string

            timestamp_parts = raw_timestamp.split(' ')      # example: ['21', 'okt', '04:39]

            # Clock (hh:mm)
            clock = timestamp_parts[-1]     # '04:39'
            clock = clock.split(':')    # ['04', '39']
            clock = list(map(int, clock))   # [4, 39]
            print("clock: " + str(clock))

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
                        return
                
                # Check for month
                for month_index, blocket_month in enumerate(blocket_months):
                    if blocket_month in raw_timestamp:
                        month_number = month_index + 1
                        if month_number > time_now.tm_mon:
                            year = time_now.tm_year - 1
                        elif month_number < time_now.tm_mon:
                            year = time_now.tm_year
                        elif timestamp_parts[0] < time_now.tm_mday:     # ad_mday < mday_now ?
                            year = time_now.tm_year
                            # There are no blocket ads near one year old
                            print('WARNING!')
                            print('This blocket date was older than expected: raw_timestamp')
                        else:
                            year = time_now.tm_year - 1
                            # There are no blocket ads near one year old
                            print('WARNING!')
                            print('This blocket date was older than expected: raw_timestamp')
                        
                        month_day = int(timestamp_parts[0])
                        time_tuple = (year, month_number, month_day, clock[0], clock[1], 0, 0, 1, -1) # year, month, month_day, hours, minutes, seconds, week_day, year_day, daylight_savings (-1=auto).  Week_day and year_day doesn't make any difference 
                        self.timestamp = time.mktime(time_tuple)
                        return
                
                # The timestamp could not be set
                print('AN error has occurred.')
                print('This blocket date was not recognized: ' + raw_timestamp)

    def set_location(self):
        '''Sets the location of an ad if it's identified'''
        location = self.soup.find('a', attrs={'class': 'LocationInfo__StyledMapLink-sc-1op511s-3'})
        if location:
            location = self.soup_replace(location,'<!-- --> (hitta.se)')    # .string doesn't work with HTML-comments
            self.location = location.string 
    
    def set_title(self):
        '''Sets the title of the ad if it's identified'''
        title = self.soup.find('div', attrs={'class': 'TextHeadline1__TextHeadline1Wrapper-sc-18mtyla-0'})
        if title:
            self.title = title.string
    
    def set_price(self):
        '''Sets the price of and ad if it's specified'''
        price = self.soup.find('div', attrs={'class': 'Price__StyledPrice-crp2x0-0'})
        if price:
            self.price = price.string

    def set_description(self):
        '''Sets the description of the ad'''
        description = self.soup.find('div', attrs={'class': 'BodyCard__DescriptionPart-sc-15r463q-2'})
        if description:
            self.description = description.string         
    
    def get_pictures(self):
        '''Gets all pictures from one ad and saves them in pictures/ under the name AD-ID_PICTURE-ID.jpg.
        If picture already exists, it's not downloaded again'''

        pictureboxes = self.soup.findAll('div', attrs={'class': 'LoadingAnimationStyles__PlaceholderWrapper-c75se8-0 jkleoR'}) # There are 4
        pictureboxes = pictureboxes[3]
        pictureboxes = pictureboxes.findChild()
        pictureboxes = pictureboxes.findChild()
        pictureboxes = pictureboxes.findChild()
        pictureboxes = pictureboxes.findChildren()

        start = "background-image:url("
        folder = 'pictures/'
        if not os.path.isdir(folder):
            os.mkdir(folder)
        for picturebox in pictureboxes:
            print(picturebox)
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
            filepath = folder + self.id + '_' + picture_id + '.jpg'
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
        print(self.picture_links)

    def update(self):
        '''Updates the ads data'''
        self.fetch()
        self.set_timestamp()
        self.set_location()
        self.set_title()
        self.set_price()
        self.set_description()
        self.get_pictures()

    def archive(self):
        '''Records the remove timestamp to see when the ad was removed'''
        print("An ad has been removed!")
        self.removed_timestamp = time.localtime()

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
        print('----' + self.title + '-' * (width - 4 - len(self.title)))
        print(self.printable_line('Price: ' + str(self.price), width))
        print(self.printable_line('Description: ' + str(self.description), width))
        print(self.printable_line('Location: ' + str(self.location), width))
        print(self.printable_line('Inlagd: ' + str(time.ctime(self.timestamp)), width))
        print('-' * width)
        print('\n')


class Car_ad(Ad):
    def __init__(self):
        '''This class will extend the Ad class with properties like Year'''
        pass
        '''
        Things to implement
        Fueltype
        transmission
        mileage
        modelyear
        bodytype
        drive
        horsepower
        color
        enginesize
        date in traffic
        make
        modell

        utrustning

        '''


class Monitored_category:
    def __init__(self, url):
        self.url = url
        self.headers = {}
        self.filepath = 'resources/monitored_category_{}.txt'.format(format2filename(url))

        self.ads = {}   # Key: ad ID value: ad class
        self.active_ad_links = []
        self.removed_ad_links = []
        if not self.load():         # Fetch from the internet if no save is found
            self.fetch_all()
            self.update_ad_links() 

    def fetch(self, url):
        '''Takes an url to a page as the argument, fetches the page and returns it as a soup'''
        while True:
            try:
                request = urllib.request.Request(url, headers = self.headers)
                html = urllib.request.urlopen(request)
                return BeautifulSoup(html, 'html.parser')
            except Exception as e:
                print("An error occured during fetching. Retrying in 30 seconds")
                print("Exception: " + str(e))
                time.sleep(30)

    def fetch_all(self):
        '''Fetches all pages in one category and saves them as soups in a list where every element is one page'''
        self.page_soups = [self.fetch(self.url + '&page=100')]      # Change this if you want to fetch 
        page_nav_div = self.page_soups[0].find('div', attrs={'class': 'Pagination__Buttons-uamu6s-3'})      # Get the div with the page-nav buttons
        if page_nav_div:
            number_pages = int(page_nav_div.find_all('a')[-1].string)       # Gets the last page number
        else:
            number_pages = 1
        
        for page_number in range(1, number_pages):
            page_link = self.url + '&page=' + str(page_number)
            self.page_soups.append(self.fetch(page_link))
            print("sidnummer: " + page_number)

    def new_ad(self, link):
        id = get_ad_id(link)
        True if id in self.ads else False # Does the id exist?

    def update_ad_links(self): 
        '''Finds new ads and saves their links'''
        self.new_ad_links = []
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
                    if ad_id in self.ads:   # The ad already exists?
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
                print("This ad was removed during this and the most recent session. No data has been saved and, therefore, the ad can not be archived.")


    def save(self):
        '''Save active_ad_links and removed_ad_links. It does not save the actuall ads'''
        folder = self.filepath.split('/')[0] 
        if not os.path.isdir(folder):
            os.mkdir(folder)
        
        file = open(self.filepath, 'wb')       # wb works for pickle.dump()
        file.seek(0)        # Clears
        file.truncate()
        
        print('Saving removed ads: ' + str(self.removed_ad_links))
        file_content = {
            'active_ad_links': self.active_ad_links,
            'removed_ad_links': self.removed_ad_links
        }

        pickle.dump(file_content, file)

    def load(self):
        '''Loads saved file'''
        if os.path.isfile(self.filepath):
            print("Loading save")
            file = open(self.filepath, 'rb')
            file_content = pickle.load(file)
            self.active_ad_links = file_content['active_ad_links']
            self.removed_ad_links =  file_content['removed_ad_links']
            return True     # Successfully loaded
        else:
            print("No save to load")
            return False    # No file to load

    def ad_class(self, link):
        '''Depending on the category this class is searching in, different classes will be used for the ads'''
        self.category = ['alla', 'fordon', 'bilar']     # This will be automaticaly detected later
        absolute_ad = 'https://beta.blocket.se' + link
        if False:
            pass
        else:
            print('absolut ad: ' + absolute_ad)
            instance = Ad(absolute_ad)
            return instance
        

headers = {}
headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:48.0) Gecko/20100101 Firefox/48.0'
bugs = Monitored_category('https://www.blocket.se/annonser/hela_sverige/fordon/bilar?cb=40&cbl1=17&cg=1020')
update_delay = 7 * 60   # Seconds

while True:
    bugs.fetch_all()
    bugs.update_ad_links()

    for new_ad_link in bugs.new_ad_links:
        print(new_ad_link)
        os.system('start chrome beta.blocket.se' + new_ad_link)
    bugs.save()

    '''
    print('\nLast updated ' + time.strftime('%H:%M:%S'))
    print('Removed ad links: ' + str(bugs.removed_ad_links))
    print('Number of ads: ' + str(len(bugs.active_ad_links)))
    print("Number pages = " + str(len(bugs.page_soups)))
    time.sleep(update_delay)'''

    time.sleep(update_delay)