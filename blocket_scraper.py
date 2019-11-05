import urllib.request
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import os
import pickle

'''
BUGS:
    1. Appearently Python doesn't allow a dictionary to be updated during iteration. Will have to solve in some other way
'''


def format2filename(filename):
    return ''.join([i for i in filename if not (i in ['.', '\\', '/', ':', '*', '?', '"', '<', '>', '|'])])

def get_base_url(full_url):
    parsed_url = urlparse(full_url)
    return '{url.scheme}://{url.netloc}'.format(url=parsed_url)


class Ad:
    def __init__(self, url):
        self.url = url
        
        self.upload_time = 0
        self.relative_url = 0
        self.location = 0
        self.price = 0
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
    
    def get_price(self):
        '''Won't work if no price is specified'''
        self.price = self.soup.find('div', attrs={'class': 'Price__StyledPrice-crp2x0-0'}).get_text()
        print(self.price)


class Monitored_category:
    def __init__(self, url):
        # This is used to download the website
        self.url = url
        self.base_url = get_base_url(url)
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
    
    def get_relative_page_links(self, soup, relative_links):
        '''Gets all links to all pages visible from the supplied page soup'''
        page_nav_div = soup.find('div', attrs={'class': 'Pagination__Buttons-uamu6s-3'})      # Get the div with the page-nav buttons
        link_tags = page_nav_div.find_all('a')

        for link_tag in link_tags:
            page_number = link_tag.string   # Gets <tag>THIS IN HERE</tag> from a tag
            print(page_number)
            relative_link = link_tag['href']
            relative_links[int(page_number)] = relative_link
        return relative_links

    def fetch_all(self):
        '''Fetches all pages in one category and saves them as soups in a list where every element is one page'''
        self.page_soups = []
        self.page_soups.append(self.fetch(self.url))
        relative_page_links = {}     # Saves relative links to all pages in the given category
        relative_page_links = self.get_relative_page_links(self.page_soups[0], relative_page_links) # Scans the first page soup for all visible page links
        
        for page_number, relative_page_link in relative_page_links.items():     # Can't use items() because it will not allow the dictionary to change size during the for loop
            if page_number == 1:
                continue    # The first page has already been fetched
            absolute_page_link = self.base_url + relative_page_link
            page_soup = self.fetch(absolute_page_link)
            self.page_soups.append(page_soup)
            if not page_number + 1 in relative_page_links:  # If the next page numbers link is not saved.  The current page will be searched for more page links
                print('updating')
                relative_page_links = self.get_relative_page_links(page_soup, relative_page_links)
                print(relative_page_links)

    def update_ad_links(self): 
        '''Finds new ads and saves their links'''
        self.new_ad_links = []
        self.newly_removed_ad_links = self.active_ad_links.copy()        # Deleting all found links until only the removed ones remain
        for page_soup in self.page_soups:
            for ad in page_soup.findAll('div', attrs={'class': 'styled__Wrapper-sc-1kpvi4z-0 eDiSuB'}):     # Loop over every ad container
                if ad['to'] in self.active_ad_links:       # Attribute 'to' is the relative link to the ad
                    print(ad['to'])
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
bugs = Monitored_category('https://www.blocket.se/annonser/hela_sverige/fordon/bilar?cb=40&cbl1=15&cg=1020&st=s')
update_delay = 7 * 60   # Seconds

while True:
    bugs.fetch_all()
    bugs.update_ad_links()

    for new_ad_link in bugs.new_ad_links:
        os.system('start chrome beta.blocket.se' + new_ad_link)
    bugs.save()

    '''for ad in bugs.active_ad_links:
        newAd = Ad('https://beta.blocket.se' + ad)
        newAd.fetch()
        newAd.get_price()
        break'''
    print('\nLast updated ' + time.strftime('%H:%M:%S'))
    print('Removed ad links: ' + str(bugs.removed_ad_links))
    print('Number of ads: ' + str(len(bugs.active_ad_links)))
    print("Number pages = " + str(len(bugs.page_soups)))
    time.sleep(update_delay)
