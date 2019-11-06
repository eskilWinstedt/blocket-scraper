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
        
        self.upload_time = 0
        self.relative_url = 0
        self.location = 0
        self.price = None
        self.titel = 0
        self.description = 0

    def fetch(self):
        '''Fetches the an Ad and creates a soup'''
        while True:
            try:
                request = urllib.request.Request(self.url)
                html = urllib.request.urlopen(request)
                self.soup =  BeautifulSoup(html)
                break
            except Exception as e:
                print("An error occured during ad fetching. Retrying in 30 seconds")
                print("Exception: " + str(e))
                time.sleep(30)
    
    def set_price(self):
        '''Sets the price of and ad if it's specified'''
        self.price = self.soup.find('div', attrs={'class': 'Price__StyledPrice-crp2x0-0'})
        if self.price:
            self.price = self.price.string
        print(self.price)
    
    def set_title(self):
        '''Sets the title of an ad'''
        self.titel = self.soup.find('div', attrs={'class': 'TextHeadline1__TextHeadline1Wrapper-sc-18mtyla-0'}).string
        print(self.titel)


class Monitored_category:
    def __init__(self, url):
        # This is used to download the website
        self.url = url
        self.headers = {}
        self.filepath = 'resources/monitored_category_{}.txt'.format(format2filename(url))

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
                return BeautifulSoup(html)
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

    def update_ad_links(self): 
        '''Finds new ads and saves their links'''
        self.new_ad_links = []
        self.newly_removed_ad_links = self.active_ad_links.copy()        # Deleting all found links until only the removed ones remain
        for page_soup in self.page_soups:
            for ad in page_soup.findAll('div', attrs={'class': 'styled__Wrapper-sc-1kpvi4z-0 eDiSuB'}):     # Loop over every ad container
                if ad['to'] in self.active_ad_links:       # Attribute 'to' is the relative link to the ad
                    self.newly_removed_ad_links.remove(ad['to'])        
                else:
                    self.active_ad_links.append(ad['to'])
                    self.new_ad_links.append(ad['to'])
            
        self.removed_ad_links += self.newly_removed_ad_links
        for removed_link in self.newly_removed_ad_links:        # Remove removed_links from active_links
            print('Removed ' + removed_link)
            self.active_ad_links.remove(removed_link)

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

headers = {}
headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:48.0) Gecko/20100101 Firefox/48.0'
bugs = Monitored_category('https://www.blocket.se/annonser/hela_sverige/fordon/bilar?cb=29&cbl1=11&cg=1020&st=s')
update_delay = 7 * 60   # Seconds

while True:
    bugs.fetch_all()
    bugs.update_ad_links()

    for new_ad_link in bugs.new_ad_links:
        os.system('start chrome beta.blocket.se' + new_ad_link)
    bugs.save()

    for ad in bugs.active_ad_links:
        print('adding ad')
        newAd = Ad('https://beta.blocket.se' + ad)
        newAd.fetch()
        newAd.set_price()
        newAd.set_title()
    '''
    print('\nLast updated ' + time.strftime('%H:%M:%S'))
    print('Removed ad links: ' + str(bugs.removed_ad_links))
    print('Number of ads: ' + str(len(bugs.active_ad_links)))
    print("Number pages = " + str(len(bugs.page_soups)))
    time.sleep(update_delay)'''
    time.sleep(update_delay)