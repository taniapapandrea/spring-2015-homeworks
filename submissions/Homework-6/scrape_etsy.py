#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import logging
import time
import datetime
import requests
from BeautifulSoup import BeautifulSoup
import matplotlib.pyplot as plt
import numpy as np

base_url = "http://www.etsy.com/"
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"

shops=[]

#returns html for the given page number
def get_result_page(page):
    url="https://www.etsy.com/search?q=knitted+hats&page="+str(page)
    headers = {'User-Agent':user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    soup = BeautifulSoup(html)
    return soup

#returns html for the given page number
def get_second_result_page(page):
    url="https://www.etsy.com/search?q=abstract+painting&page="+str(page)
    headers = {'User-Agent':user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    soup = BeautifulSoup(html)
    return soup

#get ranked list of shops from search result page
def parse_result_page(html, results, page):
    nonads = html.find('div', {'id':'search-results', 'class':'clearfix'})
    listings = nonads.findAll('div', {'class':'listing-maker'})
    rank=len(results) + 1
    for shop in listings:
        name = shop.find('a', href=True).find(text=True).strip()
        print(name)
        if not name in shops:
            shops.append(name)
            results[rank]={'Name':name}
            rank += 1
    print('shops so far ', len(results))

#returns html for the given shop name, as long as it hasn't been visited yet
def get_shop_page(name):
    url="https://www.etsy.com/shop/"+str(name)
    headers = {'User-Agent':user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    soup = BeautifulSoup(html)
    return soup

#returns a list of all the prices of in-stock items for a given shop
def prices(name):
    html = get_shop_page(name)
    #number of pages
    pages = html.find('ul', {'class':'pages'})
    url='https://www.etsy.com/shop/'+str(name)
    prices=[]
    headers = {'User-Agent':user_agent}
    response = requests.get(url, headers=headers)
    html = response.text.encode('utf-8')
    html = BeautifulSoup(html)
    pricelist = html.findAll('span', {'class':'currency-value'})
    for x in pricelist:
        price = x.find(text=True).strip()
        s = str(price)
        f=s.split('.')
        f=f[0]
        f=f.replace(',','')
        prices.append(int(f))
    return prices

#get data from shop page
def parse_shop_page(html, results, shop, name):
    #total number of items
    items=-1
    sections = html.find('div', {'id':'shop-sections', 'class':'section'})
    if not (sections is None or len(sections)==0):
        i = sections.find('span', {'class':'count'})
        if not (i is None or len(i)==0):
            i = i.find(text=True)
            if not (i is None or len(i)==0):
                i = i.strip()
                if not (i is None or len(i)==0):
                    i = i[:-6]
                    if not (i is None or len(i)==0):
                        items = int(i)
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
        if len(fields)>2:
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
    
    #average price
    li = prices(str(name))
    results[shop]['Prices'] = li
    print(shop)

#get hats data
def hats(numpages):
    results={}
    i=1
    while(i<numpages+1):
        html = get_result_page(i)
        parse_result_page(html, results, i)
        print('page ', i)
        i += 1
    print(results)
    ranks = results.keys()
    names = results.values()
    for rank in ranks:
        name = names[rank-1]['Name']
        shop_html = get_shop_page(name)
        parse_shop_page(shop_html, results, rank, name)
    return results

#get hats data
def paintings(numpages):
    results={}
    i=1
    while(i<numpages+1):
        html = get_second_result_page(i)
        parse_result_page(html, results, i)
        print('page ', i)
        i += 1
    print(results)
    ranks = results.keys()
    names = results.values()
    for rank in ranks:
        name = names[rank-1]['Name']
        shop_html = get_shop_page(name)
        parse_shop_page(shop_html, results, rank, name)
    return results
