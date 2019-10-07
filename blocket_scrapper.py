from bs4 import BeautifulSoup
import urllib.request
import time
import os

headers = {}
headers['User-Agent'] = "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:48.0) Gecko/20100101 Firefox/48.0"
req = urllib.request.Request('https://beta.blocket.se/annonser/hela_sverige/fordon/bilar?cb=40&cg=1020&st=s&cbl1=17', headers = headers)

# Keeps all links to the ads
ads = []
initialIteration = True
timer = (7*60)

while True:
    html = urllib.request.urlopen(req)
    soup = BeautifulSoup(html)

    for ad in soup.findAll('div', attrs={'class': 'styled__Wrapper-sc-1kpvi4z-0 eDiSuB'}):
        # Is the link new?
        if not ad['to'] in ads:
            ads.append(ad['to'])
            print(ad['to'])

            # All ads will be unknow during the first iteration
            if not initialIteration:
                command = "start chrome beta.blocket.se" + ad['to']
                os.system(command)

    print(ads)
    # Search every 3 minutes
    for i in range(timer):
        print(str(int((timer - i) / 60)) + " minter och sekunder " + str((timer - i) % 60))
        time.sleep(1)
    # Next iteration is not the first
    initialIteration = False