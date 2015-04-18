#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import logging
import requests
import time
import datetime
from BeautifulSoup import BeautifulSoup

base_url = "http://www.etsy.com/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"

#returns html for the given page number
def get_result_page(page):
    url="https://www.etsy.com/search?q=knitted+hats&page="+str(page)
    headers = {'User-Agent':user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    soup = BeautifulSoup(html)
    return soup

#get ranked list of shops from search result page
def parse_result_page(html, results, page):
    nonads = html.find('div', {'id':'search-results', 'class':'clearfix'})
    listings = nonads.findAll('div', {'class':'listing-maker'})
    rank=(page-1)*45
    for shop in listings:
        name = shop.find('a', href=True).find(text=True).strip()
        rank += 1
        results[rank]={'Name':name}

#returns html for the given shop name
def get_shop_page(name):
    url="https://www.etsy.com/shop/"+str(name)
    headers = {'User-Agent':user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    soup = BeautifulSoup(html)
    return soup

#get data from shop page
def parse_shop_page(html, results, shop):
    #total number of items
    sections = html.find('div', {'id':'shop-sections', 'class':'section'})
    if not (sections is None or len(sections)==0):
        items = int(sections.find('span', {'class':'count'}).find(text=True).strip()[:-6])
    else:
        items= -1
    results[shop]['Num_items'] = items

    #number of sections
    if (sections is None or len(sections)==0):
        results[shop]['Num_sections']=-1
    else:
        s = sections.findAll('li')
        results[shop]['Num_sections']=len(s)-1

    #location
    owner = html.find('div', {'id':'shop-owner', 'class':'section custom'})
    l=-1
    if not (owner is None or len(owner)==0):
        location = owner.find('div', {'class':'location'})
        if not (location is None or len(location)==0):
            l = location.find(text=True).strip()
    results[shop]['Location']=l
    
    #how old
    age=-1
    joined = html.find('div', {'class':'join-date'})
    if not (joined is None or len(joined)==0):
        joined = joined.find(text=True).strip()
        fields = str(joined).split(' ')
        months = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
        start = datetime.datetime(int(fields[4]),int(months[fields[2]]),int(fields[3][:-1]))
        today=datetime.datetime.now()
        age = str(today-start)
        fields=age.split(' ')
        age=int(fields[0])
    results[shop]['Age']=age
    
    #reviews
    numreviews=-1
    avgreviews=-1
    reviews=html.find('span', {'class':'review-rating'})
    if not (reviews is None or len(reviews)==0):
        avgreviews = reviews.find('meta', {'itemprop':'rating'})['content']
        numreviews = reviews.find('meta', {'itemprop':'count'})['content']
    results[shop]['Num_reviews']=numreviews
    results[shop]['Rating']=avgreviews

    #sales
    s=-1
    salesclass = html.find('li', {'class':'sales '})
    if not (salesclass is None or len(salesclass)==0):
        href = salesclass.find('a', href=True)
        if not (href is None or len(href)==0) and href.find(text=True):
            sales = href.find(text=True).strip()
            sales = sales[:-6].replace(",","")
            if not (sales is None or len(sales)==0):
                s = int(sales)
    results[shop]['Sales']=s
    
    #admirers
    a=-1
    adclass = html.find('li', {'class':'admirers'})
    if not (adclass is None or len(adclass)==0):
        href = adclass.find('a', href=True)
        if not (href is None or len(href)==0) and href.find(text=True):
            admirers = href.find(text=True).strip()
            admirers = admirers[:-9].replace(",","")
            if not (admirers is None or len(admirers)==0):
                a = int(admirers)
    results[shop]['Admirers']=a

    #accepts gift cards?
    gc=False
    if html.find('div', {'class':'shop-giftcard-callout clear'}):
       gc=True
    results[shop]['Gift_card']=gc
#avg price of sold items vs avg price of inventory
#avg num items per section

#get hats data
def hats():
    results={}
    i=1
    while(i<2):
        html = get_result_page(i)
        parse_result_page(html, results, i)
        i += 1
    ranks = results.keys()
    names = results.values()
    for rank in ranks:
        print(names[rank-1]['Name'])
        shop_html = get_shop_page(names[rank-1]['Name'])
        parse_shop_page(shop_html, results, rank)
    return results
