#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import logging
import requests
from BeautifulSoup import BeautifulSoup


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
loghandler = logging.StreamHandler(sys.stderr)
loghandler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
log.addHandler(loghandler)

base_url = "http://www.tripadvisor.com/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"



def get_city_page(city, state, datadir):
    """ Returns the URL of the list of the hotels in a city. Corresponds to
    STEP 1 & 2 of the slides.
    Parameters
    ----------
    city : str
    state : str
    datadir : str
    Returns
    -------
    url : str
        The relative link to the website with the hotels list.
    """
    # Build the request URL
    url = base_url + "city=" + city + "&state=" + state
    # Request the HTML page
    headers = {'User-Agent': user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    with open(os.path.join(datadir, city + '-tourism-page.html'), "w") as h:
        h.write(html)

    # Use BeautifulSoup to extract the url for the list of hotels in
    # the city and state we are interested in.

    # For example in this case we need to get the following href
    # <li class="hotels twoLines">
    # <a href="/Hotels-g60745-Boston_Massachusetts-Hotels.html" data-trk="hotels_nav">...</a>
    soup = BeautifulSoup(html)
    li = soup.find("li", {"class": "hotels twoLines"})
    city_url = li.find('a', href=True)
    return city_url['href']


def get_hotellist_page(city_url, page_count, city, datadir='data/'):
    """ Returns the hotel list HTML. The URL of the list is the result of
    get_city_page(). Also, saves a copy of the HTML to the disk. Corresponds to
    STEP 3 of the slides.
    Parameters
    ----------
    city_url : str
        The relative URL of the hotels in the city we are interested in.
    page_count : int
        The page that we want to fetch. Used for keeping track of our progress.
    city : str
        The name of the city that we are interested in.
    datadir : str, default is 'data/'
        The directory in which to save the downloaded html.
    Returns
    -------
    html : str
        The HTML of the page with the list of the hotels.
    """
    url = base_url + city_url
    # Sleep 2 sec before starting a new http request
    time.sleep(2)
    # Request page
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    # Save the webpage
    with open(os.path.join(datadir, city + '-hotelist-' + str(page_count) + '.html'), "w") as h:
        h.write(html)
    return html


def parse_hotellist_page(html):
    """Parses the website with the hotel list and prints the hotel name, the
    number of stars and the number of reviews it has. If there is a next page
    in the hotel list, it returns a list to that page. Otherwise, it exits the
    script. Corresponds to STEP 4 of the slides.
    Parameters
    ----------
    html : str
        The HTML of the website with the hotel list.
    Returns
    -------
    URL : str
        If there is a next page, return a relative link to this page.
        Otherwise, exit the script.
    """
    soup = BeautifulSoup(html)
    # Extract hotel name, star rating and number of reviews
    hotel_boxes = soup.findAll('div', {'class' :'listing wrap reasoning_v5_wrap jfy_listing p13n_imperfect'})
    if not hotel_boxes:
        log.info("#################################### Option 2 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing_info jfy'})
    if not hotel_boxes:
        log.info("#################################### Option 3 ######################################")
        hotel_boxes = soup.findAll('div', {'class' :'listing easyClear  p13n_imperfect'})

    for hotel_box in hotel_boxes:
        hotel_name = hotel_box.find("a", {"target" : "_blank"}).find(text=True)
        log.info("Hotel name: %s" % hotel_name.strip())

        stars = hotel_box.find("img", {"class" : "sprite-ratings"})
        if stars:
            log.info("Stars: %s" % stars['alt'].split()[0])

        num_reviews = hotel_box.find("span", {'class': "more"}).findAll(text=True)
        if num_reviews:
            log.info("Number of reviews: %s " % [x for x in num_reviews if "review" in x][0].strip())

        #get URL of hotel page (like below)
        title_link = hotel_box.find("a", {"target" : "_blank"})['href']
        title_link = base_url + title_link
        parse_review(title_link)
            
    # Get next URL page if exists, otherwise exit
    div = soup.find("div", {"class" : "pagination paginationfillbtm"})
    #div is a nonetype
    # check if this is the last page
    if div.find("span", {"class" : "guiArw pageEndNext"}):
        log.info("We reached last page")
        sys.exit()
    # If not, return the url to the next page
    hrefs = div.findAll('a', href= True)
    for href in hrefs:
        if href.find(text = True).strip() == '&raquo;':
            log.info("Next url is %s" % href['href'])
            return href['href']

def parse_review(url):
    #get HTML of the URL (like get_hotellist_page function)
    time.sleep(2)
    headers = { 'User-Agent' : user_agent }
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    #parse HTML to get REVIEW_FILTER_FORM like above
    soup = BeautifulSoup(html)
    databox = soup.find('div', {'class':'content wrap trip_type_layout'})
    #traveler ratings
    ratings = databox.findAll('div', {'class':'wrap row'})
    excellent = ratings[0]
    verygood = ratings[1]
    average = ratings[2]
    poor = ratings[3]
    terrible = ratings[4]
    rating_excellent = excellent.find('span', {'class':'compositeCount'}).find(text=True)
    log.info('Excellent ratings: %s' %rating_excellent.strip())
    rating_verygood = verygood.find('span', {'class':'compositeCount'}).find(text=True)
    log.info('Very good ratings: %s' %rating_verygood.strip())
    rating_average = average.find('span', {'class':'compositeCount'}).find(text=True)
    log.info('Average ratings: %s' %rating_average.strip())
    rating_poor = poor.find('span', {'class':'compositeCount'}).find(text=True)
    log.info('Poor ratings: %s' %rating_poor.strip())
    rating_terrible = terrible.find('span', {'class':'compositeCount'}).find(text=True)
    log.info('Terrible ratings: %s' %rating_terrible.strip())
    #see reviews for different types of people
    peopletypes = databox.findAll('div', {'class':'filter_connection_wrapper'})
    families = peopletypes[0]
    couples = peopletypes[1]
    solo = peopletypes[2]
    business = peopletypes[3]
    f = families.find('div', {'class':'value'}).find(text=True)
    log.info('Family ratings: %s' %f.strip())
    c = couples.find('div', {'class':'value'}).find(text=True)
    log.info('Couple ratings: %s' %c.strip())
    s = solo.find('div', {'class':'value'}).find(text=True)
    log.info('Solo ratings: %s' %s.strip())
    b = business.find('div', {'class':'value'}).find(text=True)
    log.info('Business ratings: %s' %b.strip())
    #rating summary
    summaries = databox.findAll('li')
    sleep_quality = summaries[0].find('img')
    stars = sleep_quality['alt']
    log.info('Sleep Quality: %s' %stars)
    location = summaries[1].find('img')
    stars1 = location['alt']
    log.info('Location: %s' %stars1)
    rooms = summaries[2].find('img')
    stars2 = location['alt']
    log.info('Rooms: %s' %stars2)
    service = summaries[3].find('img')
    stars3 = location['alt']
    log.info('Service': %stars3)
    value = summaries[3].find('img')
    stars4 = value['alt']
    log.info('Value : %s' %stars4)
    cleanliness = summaries[4].find(img.png)
    stars5 = value['alt']
    log-info('Cleanliness': %stars4)
def scrape_hotels(city,  state, datadir='data/'):
    """Runs the main scraper code
    Parameters
    ----------
    city : str
        The name of the city for which to scrape hotels.
    state : str
        The state in which the city is located.
    datadir : str, default is 'data/'
        The directory under which to save the downloaded html.
    """

    # Get current directory
    current_dir = os.getcwd()
    # Create datadir if does not exist
    if not os.path.exists(os.path.join(current_dir, datadir)):
        os.makedirs(os.path.join(current_dir, datadir))

    # Get URL to obtaint the list of hotels in a specific city
    city_url = get_city_page(city, state, datadir)
    c = 0
    while(True):
        c += 1
        html = get_hotellist_page(city_url, c, city, datadir)
        city_url = parse_hotellist_page(html)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape tripadvisor')
    parser.add_argument('-datadir', type=str,
                        help='Directory to store raw html files',
                        default="data/")
    parser.add_argument('-state', type=str,
                        help='State for which the hotel data is required.',
                        required=True)
    parser.add_argument('-city', type=str,
                        help='City for which the hotel data is required.',
                        required=True)

    args = parser.parse_args()
    scrape_hotels(args.city, args.state, args.datadir)
