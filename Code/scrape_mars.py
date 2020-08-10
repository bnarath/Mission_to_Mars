# scrape_mars.py

## Dependencies

import requests
from splinter import Browser
from bs4 import BeautifulSoup as bs
import time
import pandas as pd
import re
import threading
#In Python 3.2+, stdlib concurrent.futures module provides a higher level API to threading, 
# including passing return values or exceptions from a worker thread back to the main thread:
import concurrent.futures
try:
    from urls_list import * #where all urls and paths are saved
except:
    from Code.urls_list import *


def scrape_latest_news(st):
    #########################################################################################
    #Scrape the latest news
    #Returns news_title, news_p
    #########################################################################################
    news_title, news_p = None, None
    #Configure Browser
    browser = Browser(browser_choice, executable_path=executable_path, headless=True)
    try:
        #Visit url
        browser.visit(nasa_mars_news)
        #bs object with lxml parser
        time.sleep(st)#This is very important
        soup = bs(browser.html, 'lxml')
        news = soup.find('li', class_='slide').div.find(class_='list_text').find_all('div')
        news_title, news_p = news[1].text, news[2].text
    except Exception as e:
        print(e)      
    #Close browser to avoid resource issue
    browser.quit() 
    return (news_title, news_p)

def scrape_featured_image_url(st):
    #########################################################################################
    #Scrape the featured image url from nasa jpl site
    #Returns featured_image_url
    #########################################################################################
    featured_image_url = None
    #Configure Browser
    browser = Browser(browser_choice, executable_path=executable_path, headless=True)
    try:
        #Visit url
        browser.visit(nasa_jpl)
        #Click a button "FULL IMAGE"
        browser.find_by_id('full_image', wait_time=1).click()
        #Click more info button
        browser.find_by_css('[id="fancybox-lock"]')[0].find_by_css('div[class="buttons"] a:nth-child(2)')[0].click()
        time.sleep(st)
        #Take the image link (largesize)
        featured_image_url = browser.find_by_css('figure[class="lede"] a')['href']
    except Exception as e:
        print(e)  
    #Close browser to avoid resource issue
    browser.quit()
    return featured_image_url

def scrape_mars_weather(st):
    #########################################################################################
    #Scrape the latest Mars weather tweet from the twitter page
    #Returns mars_weather
    #########################################################################################
    mars_weather = None
    #Configure Browser
    browser = Browser(browser_choice, executable_path=executable_path, headless=True)
    try:
        #Visit url
        browser.visit(mars_twitter_page)
        #bs object with lxml parser
        time.sleep(st)#This is very important
        soup = bs(browser.html, 'lxml')
        #Extract the weather info using soup css selector
        mars_weather = soup.find('div', attrs={'data-testid':'tweet'}).select('div:nth-of-type(2) > div:nth-of-type(2) > div:nth-of-type(1) > div:nth-of-type(1) > span')[0].text
    except Exception as e:
        print(e) 
    #Close browser to avoid resource issue
    browser.quit()
    return mars_weather

def scrape_mars_facts(st):
    DF = pd.read_html(mars_facts, attrs={'id':'tablepress-p-mars'})[0]
    DF.rename(columns={0:'', 1:'value'}, inplace=True)
    return DF

def scrape_hemispheres(st):  
    #########################################################################################
    #Scrape high resolution images for each of Mar's hemispheres from USGS Astrogeology site
    #Returns list of dictionaries with title and image urls
    ######################################################################################### 
    hemisphere_image_urls = []
    #Configure Browser
    browser = Browser(browser_choice, executable_path=executable_path, headless=True)
    try:
        #Visit url
        browser.visit(usgs_search)
        #bs object with lxml parser
        time.sleep(st)#This is very important (site loads super slow)
        soup = bs(browser.html, 'lxml')
        hs_links = soup.find(id='product-section').find_all('a',class_="itemLink product-item")
        for index,link in enumerate(hs_links):
            if link.img is None:
                title = re.sub(' Enhanced', '', link.text)
            else:
                browser.visit(usgs_base+link['href'])
                time.sleep(1)
                img_url = browser.find_by_css('img[class="wide-image"]')['src']
            
            if index%2:#Image and title come together
                hemisphere_image_urls.append({'title':title,'img_url':img_url})
    except Exception as e:
        print(e)     
    #Close browser to avoid resource issue
    browser.quit()
    return hemisphere_image_urls

## Retry function
def retry(fun, st, max_tries=5):
## Sometimes the websites respond slow and result in parsing errors. 
## This function retries scraping until the max retries.
    delay = 2
    Iter=1
    result=None
    while (Iter<=max_tries) or (result is None):
        try:
           result = fun(st)
           assert(result is not None)
           break
        except Exception as e:
            print(e)
        time.sleep(delay)
        delay*=2
        st+=1 
    return result

def scrape():

    #Using concurrency brings down time from 1 minute to less than 30 sec (--- 29.444027185440063 seconds ---)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(retry, fn, st) \
            for fn,st in [(scrape_latest_news, 4), \
                (scrape_featured_image_url, 4), \
                    (scrape_mars_weather, 4), \
                        (scrape_mars_facts, 0), \
                            (scrape_hemispheres, 10)]]

        nasa_mars_news_data, scrape_featured_image_url_data,\
        scrape_mars_weather_data, scrape_mars_facts_data,\
            scrape_hemispheres_data = [future.result() for future in futures]


    for future in concurrent.futures.as_completed(futures):
        print(future.result()) 

    

    scraped_dict = {
        'nasa_mars_news_data':nasa_mars_news_data,
        'scrape_featured_image_url_data':scrape_featured_image_url_data,
        'scrape_mars_weather_data':scrape_mars_weather_data,
        'scrape_mars_facts_data':scrape_mars_facts_data,
        'scrape_hemispheres_data':scrape_hemispheres_data
    }
    print('######################################################')
    return scraped_dict


##Checking scrape.py
if __name__ == "__main__":
    start_time = time.time()
    print(scrape())
    print(f"--- {time.time() - start_time} seconds ---")