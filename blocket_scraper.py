import urllib.request
from bs4 import BeautifulSoup
import time
import os
import pickle

# To do:
# *See when ads are removed
# *Download ads information. 
# 
#

def format2filename(filename):
    return ''.join([i for i in filename if not (i in ['.', '\\', '/', ':', '*', '?', '"', '<', '>', '|'])])

class Ad:
    def __init__(self):
        self.upload_time
        self.relative_url
        self.location
        self.price
        self.titel
        self.description


class Monitored_category:
    def __init__(self, url):
        # This is used to download the website
        self.url = url
        self.headers = {}
        self.filename = format2filename(url)
        

        self.active_ad_links = []
        self.removed_ad_links = []
        self.load()
        self.fetch_all()
        self.update_ad_links()

    def fetch(self, url):
        '''Takes an url to a page as the argument, fetches the page and returns it as a soup'''
        while True:
            try:
                request = urllib.request.Request(url, headers = self.headers)
                html = urllib.request.urlopen(request)
                return BeautifulSoup(html)
                break
            except Exception as e:
                print("An error occured during fetching. Retrying in 30 seconds")
                print("Exception: " + str(e))
                time.sleep(30)
            
    
    def fetch_all(self):
        '''Fetches all pages in one category and saves them as soups in a list where every element is one page'''
        self.page_soups = []
        self.page_soups.append(self.fetch(self.url))
        page_links = [self.url]

        page_nav_div = self.page_soups[0].find('div', attrs={'class': 'Pagination__Buttons-uamu6s-3'})      # Get the div with the page-nav buttons
        number_pages = len(page_nav_div.find_all('a'))
        for page_index in range(2, number_pages + 1):       # Starting at index 2 because page 1 is already fetched
            page_link = self.url + '&page=' + str(page_index)
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
        file = open('resources/monitored_category_{}.txt'.format(self.filename), 'wb')       # wb works for pickle.dump()

        file.seek(0)        # Clears
        file.truncate()     # the file

        file_content = {
            'active_ad_links': self.active_ad_links,
            'removed_ad_links': self.removed_ad_links
        }

        pickle.dump(file_content, file)

    def load(self):
        '''Loads saved file'''
        if os.path.isfile(self.filename):
            file = open('resources/monitored_category_{}.txt'.format(self.filename), 'rb')
            file_content = pickle.load(file)
            self.active_ad_links = file_content['active_ad_links']
            self.removed_ad_links =  file_content['removed_ad_links']
'''
	def loadSettings(self):
		if checkFileExisting('resources/saved_settings.txt'):
			file = open('resources/saved_settings.txt', 'r')
			self.savedSettings = file.read()
			try: 
				self.settings = eval(self.savedSettings)
			except Exception as e:
				print('Exeption: ' + str(e))
			self.updateDisplayDimensions()
			return False
		else:
			return True
'''


headers = {}
headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:48.0) Gecko/20100101 Firefox/48.0'
bugs = Monitored_category('https://beta.blocket.se/annonser/hela_sverige/fordon/bilar?cb=40&cg=1020&st=s&cbl1=17')

update_delay = 7 * 60   # Seconds

while True:
    bugs.fetch_all()
    bugs.update_ad_links()
    for new_ad_link in bugs.new_ad_links:
        os.system('start chrome beta.blocket.se' + new_ad_link)
        break
    bugs.save()
    print('\nLast updated ' + time.strftime('%H:%M:%S'))
    print('Removed ad links: ' + str(bugs.removed_ad_links))
    print('Number of ads: ' + str(len(bugs.active_ad_links)))
    print("Number pages = " + str(len(bugs.page_soups)))
    time.sleep(update_delay)