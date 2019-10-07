import urllib.request
from bs4 import BeautifulSoup
import time
import os


class Monitored_category:
    def __init__(self, url, headers = {}):
        # This is used to download the website
        self.url = url
        self.headers = headers
        
        self.ad_links = []
        self.fetch_all()
        self.update_ad_links()
    
    def fetch(self, url):
        '''Takes an url to a page as the argument, fetches the page and returns it as a soup'''
        request = urllib.request.Request(url, headers = self.headers)
        html = urllib.request.urlopen(request)
        return BeautifulSoup(html)
    
    def fetch_all(self):
        '''Fetches all pages in one category and saves them as soups in a list where every element is on page'''
        self.page_soups = []
        self.page_soups.append(self.fetch(self.url))

        page_nav_div = self.page_soups[0].find('div', attrs={'class': 'Pagination__Buttons-uamu6s-3'})      # Get the div with the page-nav buttons
        number_pages = len(page_nav_div.find_all('a'))
        for page_index in range(2, number_pages + 2):       # Starting at index 2 because page 1 is already fetched
            self.page_soups.append(self.fetch(self.url + '&page=' + str(page_index)))

    def update_ad_links(self): 
        '''Finds new ads and saves their links'''
        self.new_ad_links = []

        for page_soup in self.page_soups:
            for ad in page_soup.findAll('div', attrs={'class': 'styled__Wrapper-sc-1kpvi4z-0 eDiSuB'}):     # Loop over every ad container
                if not ad['to'] in self.ad_links:            # Attribute 'to' is the relative link to the ad
                    self.ad_links.append(ad['to'])               
                    self.new_ad_links.append(ad['to'])


headers = {}
headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:48.0) Gecko/20100101 Firefox/48.0'
bugs = Monitored_category('https://beta.blocket.se/annonser/hela_sverige/fordon/bilar?cb=40&cg=1020&st=s&cbl1=17')


update_delay = 10   # Seconds

while True:
    bugs.fetch_all()
    bugs.update_ad_links()
    for new_ad_link in bugs.new_ad_links:
        os.system('start chrome beta.blocket.se' + new_ad_link)
    print('Last updated ' + time.strftime('%H:%M:%S'))
    bugs.fetch_all()
    time.sleep(update_delay)
