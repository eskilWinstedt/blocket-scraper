import urllib.request
from bs4 import BeautifulSoup
import time
import os


class Monitored_category:
    def __init__(self, url, headers = {}):
        # This is used to download the website
        self.request = urllib.request.Request(url, headers = headers)
        
        self.ad_links = []
        self.fetch()
        self.update_ad_links()

    def fetch(self):
        html = urllib.request.urlopen(self.request)
        self.soup = BeautifulSoup(html)
    
    def update_ad_links(self):
        self.new_ad_links = []
        # Loop over every ad container
        for ad in self.soup.findAll('div', attrs={'class': 'styled__Wrapper-sc-1kpvi4z-0 eDiSuB'}):
            # Is the link unknown?
            if not ad['to'] in self.ad_links:            # Attribute 'to' is the relative ad link
                self.ad_links.append(ad['to'])               
                self.new_ad_links.append(ad['to'])


headers = {}
headers['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:48.0) Gecko/20100101 Firefox/48.0'
bugs = Monitored_category('https://beta.blocket.se/annonser/hela_sverige/fordon/bilar?cb=40&cg=1020&st=s&cbl1=17')
update_delay = 5 * 60   # Seconds

while True:
    bugs.fetch()
    bugs.update_ad_links()
    for new_ad_link in bugs.new_ad_links:
        os.system('start chrome beta.blocket.se' + new_ad_link)
    print('Last updated ' + time.strftime('%H:%M:%S'))
    time.sleep(update_delay)