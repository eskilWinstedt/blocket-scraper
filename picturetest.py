import urllib.request
from bs4 import BeautifulSoup

def format2filename(filename):
    return ''.join([i for i in filename if not (i in ['.', '\\', '/', ':', '*', '?', '"', '<', '>', '|'])])

request = urllib.request.Request("https://www.blocket.se/annons/skane/volkswagen_bubbla_1200_oldschool/85373511")
html = urllib.request.urlopen(request)
soup =  BeautifulSoup(html, 'html.parser')

pictureboxes = soup.findAll('div', attrs={'class': 'LoadingAnimationStyles__PlaceholderWrapper-c75se8-0 jkleoR'})
pictureboxes = pictureboxes[-1]

pictureboxes = pictureboxes.findChild()
pictureboxes = pictureboxes.findChild()
pictureboxes = pictureboxes.findChild()
pictureboxes = pictureboxes.findChildren()


picturelinks = []
start = "background-image:url("
for box in pictureboxes:
    style_value = box.attrs['style']
    start_index = style_value.find(start) + len(start)
    link = style_value[start_index:]
    end_index = link.find(")")
    link = link[:end_index]

    picturelinks.append(link)
    f = open(format2filename(link) + '.jpg', 'wb')
    f.write(urllib.request.urlopen(link).read())
    f.close()
