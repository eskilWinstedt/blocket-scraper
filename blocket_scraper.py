import urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import os
import pickle


def format2filename(filename):
    return ''.join([i for i in filename if not (i in ['.', '\\', '/', ':', '*', '?', '"', '<', '>', '|'])])


class Ad:
    def __init__(self, url):
        self.url = url
        print("I'm called")
        self.update()

    def fetch(self):
        '''Fetches the an Ad and creates a soup'''
        while True:
            try:
                request = urllib.request.Request(self.url)
                html = urllib.request.urlopen(request)
                self.soup =  BeautifulSoup(html, 'html.parser')
                break
            except Exception as e:
                print("An error occured during ad fetching. Retrying in 30 seconds")
                print("Exception: " + str(e))
                time.sleep(30)
    
    def soup_replace(self, soup, remove, replace = ''):
        return BeautifulSoup(str(soup).replace(remove, replace), 'html.parser')

    def set_timestamp(self,):
        # smalldatetime	YYYY-MM-DD hh:mm:ss
        '''raw_timestamp = self.soup.find('span', attrs={'class': 'PublishedTime__StyledTime-pjprkp-1'})
        raw_timestamp = self.soup_replace(raw_timestamp, 'Inlagd: <!-- -->')
        raw_timestamp = raw_timestamp.string'''
        raw_timestamp = 'idag 07:26'
        timestamp_split = raw_timestamp.split(' ') # Splits into ['21', 'okt', '04:39]
        clock = timestamp_split[-1].replace('0', '')  # Removes the zeros in '04:39' ---> '4:39'
        clock = clock.split(':')       # '4:39' ---> ['4', '39']
        clock = [int(i) for i in clock] # ['4', '39'] ---> [4, 39]
        time_in_seconds = time.time()   # Current time
        time_now = time.gmtime()   # Current time
        if 'idag' in  raw_timestamp:
            time_no_clock = time_in_seconds - time_now[3] * 3600 - time_now[4] * 60 - time_now[5]     # Removes the hours, minutes and seconds
            timestamp = time_no_clock + clock[0] * 3600 + clock[1] * 60  # Adding the hours and minutes
        elif 'igår' in raw_timestamp:
            time_no_clock = time_in_seconds - time_now[3] * 3600 - time_now[4] * 60 - time_now[5]     # Removes the hours, minutes and seconds
            timestamp = -3600 * 24 # Removes one day
            timestamp += time_no_clock + clock[0] * 3600 + clock[1] * 60
            '''year = str(local_time[0])
            month = str(local_time[1])
            day = str(local_time[2])
            hour = str(clock[0])
            minute = str(clock[1])
            print('Year: ' + year + '\tMonth: ' + month + '\tDay: ' + day + '\tHour: ' + hour + '\tMinute: ' + minute)'''
        elif 'i måndags' in raw_timestamp:
            pass
        elif 'i tisdags' in raw_timestamp:
            pass
        elif 'i onsdags' in raw_timestamp:
            pass
        elif 'i torsdags' in raw_timestamp:
            pass
        elif 'i fredags' in raw_timestamp:
            pass
        elif 'i lördags' in raw_timestamp:
            pass
        elif 'i söndags' in raw_timestamp:
            pass
        else:
            # The timestamp is in this format: day month clock
            pass

        self.timestamp = raw_timestamp

    def set_location(self):
        '''Sets the location of an ad'''
        self.location = self.soup.find('a', attrs={'class': 'LocationInfo__StyledMapLink-sc-1op511s-3'})
        if self.location:
            self.location = self.soup_replace(self.location,'<!-- --> (hitta.se)')    # .string doesn't work with HTML-comments
            self.location = self.location.string
    
    def set_title(self):
        '''Sets the title of an ad'''
        self.title = self.soup.find('div', attrs={'class': 'TextHeadline1__TextHeadline1Wrapper-sc-18mtyla-0'}).string
    
    def set_price(self):
        '''Sets the price of and ad if it's specified'''
        self.price = self.soup.find('div', attrs={'class': 'Price__StyledPrice-crp2x0-0'})
        if self.price:
            self.price = self.price.string

    def set_description(self):
        '''Sets the description of the ad'''
        self.description = self.soup.find('div', attrs={'class': 'BodyCard__DescriptionPart-sc-15r463q-2'})
        if self.description:
            self.description = self.description.string
    
    def update(self):
        '''Updates the ad'''
        self.fetch()
        self.set_timestamp()
        self.set_location()
        self.set_title()
        self.set_price()
        self.set_description()

    def archive(self):
        '''Records the remove timestamp to see when the ad was removed'''
        print("An ad has been removed!")

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
        print(self.printable_line('Inlagd: ' + str(self.timestamp), width))
        print('-' * width)
        print('\n')


class Vehicle_ad(Ad):
    def __init__(self):
        '''This class will extend the Ad class with properties like Year'''
        pass


class Monitored_category:
    def __init__(self, url):
        # This is used to download the website
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

    def new_ad(self, link):
        id = self.get_ad_id(link)
        if id in self.ads:    # Does the id exist?
            return True
        else:
            return False

    def update_ad_links(self): 
        '''Finds new ads and saves their links'''
        self.new_ad_links = []
        self.newly_removed_ad_links = self.active_ad_links.copy()        # Deleting all found links until only the removed ones remain
        for page_soup in self.page_soups:
            for ad in page_soup.findAll('div', attrs={'class': 'styled__Wrapper-sc-1kpvi4z-0 eDiSuB'}):     # Loop over every ad container
                if ad['to'] in self.active_ad_links:       # Attribute 'to' is the relative link to the ad
                    self.newly_removed_ad_links.remove(ad['to'])        
                else:   # The ad is new or has changed name
                    self.active_ad_links.append(ad['to'])
                    self.new_ad_links.append(ad['to'])
                    ad_id = self.get_ad_id(ad['to'])
                    if ad_id in self.ads:   # The ad already exists
                        # Update the ad so the new name will be saved!
                        print('THE NAME HAS BEEN CHANGED')
                        self.ads[ad_id].update()
                    else:
                        print('yes')
                        print('Ad id: ' + ad_id)
                        self.ads[ad_id] = self.ad_class(ad['to'])
                        print(str(self.ad_class(ad['to']).url))
                        print(len(self.ads))
        print('Nu är jag här')
        for key in self.ads:
            self.ads[key].__repr__()
        self.removed_ad_links += self.newly_removed_ad_links
        for removed_link in self.newly_removed_ad_links:        # Remove removed_links from active_links
            print('Removed ' + removed_link)
            self.active_ad_links.remove(removed_link)
            ad_id = self.get_ad_id(removed_link)
            self.ads[ad_id].archive()


    def save(self):
        '''Save active_ad_links and removed_ad_links'''
        file = open(self.filepath, 'wb')       # wb works for pickle.dump()
        file.seek(0)        # Clears
        file.truncate()     # the file
        
        print('Saving removed ads: ' + str(self.removed_ad_links))
        file_content = {
            'active_ad_links': self.active_ad_links,
            'removed_ad_links': self.removed_ad_links
        }

        pickle.dump(file_content, file)

    def load(self):
        '''Loads saved file'''
        if os.path.isfile(self.filepath):
            file = open(self.filepath, 'rb')
            file_content = pickle.load(file)
            self.active_ad_links = file_content['active_ad_links']
            self.removed_ad_links =  file_content['removed_ad_links']
            return True     # Successfully loaded
        else: 
            return False    # No file to load

    def get_ad_id(self, ad_link):
        '''Gets the unique ad id from the ad link '''
        return ad_link.split('/')[-1]

    def ad_class(self, link):
        '''Depending on the category this class is searching in, different classes will be used for the ads'''
        self.category = ['alla', 'fordon', 'bilar']     # This will be automaticaly detected later
        absolute_ad = 'https://beta.blocket.se' + link
        if False:
            pass
        else:
            print('det stämmer!')
            print('absolut ad: ' + absolute_ad)
            reference = Ad(absolute_ad)
            return reference
        

headers = {}
headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:48.0) Gecko/20100101 Firefox/48.0'
bugs = Monitored_category('https://www.blocket.se/annonser/hela_sverige/fordon/bilar?cb=40&cbl1=17&cg=1020&st=s')
update_delay = 7 * 60   # Seconds

while True:
    bugs.fetch_all()
    bugs.update_ad_links()

    for new_ad_link in bugs.new_ad_links:
        os.system('start chrome beta.blocket.se' + new_ad_link)
    bugs.save()

    '''
    for ad in bugs.active_ad_links:
        newAd = Ad('https://beta.blocket.se' + ad)
        newAd.fetch()
        newAd.set_location()
        newAd.set_price()
        newAd.set_title()
        newAd.set_description()
        newAd.set_timestamp()
        newAd.__repr__()
    '''
    '''
    print('\nLast updated ' + time.strftime('%H:%M:%S'))
    print('Removed ad links: ' + str(bugs.removed_ad_links))
    print('Number of ads: ' + str(len(bugs.active_ad_links)))
    print("Number pages = " + str(len(bugs.page_soups)))
    time.sleep(update_delay)'''
    time.sleep(update_delay)