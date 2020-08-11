# scrape_mars.py

## Dependencies

import requests
from selenium import webdriver
from bs4 import BeautifulSoup as bs
import time
import pandas as pd
import re
import threading
import os
#In Python 3.2+, stdlib concurrent.futures module provides a higher level API to threading, 
# including passing return values or exceptions from a worker thread back to the main thread:
import concurrent.futures
try:
    from urls_list import * #where all urls and paths are saved
except:
    from Code.urls_list import *

def instatiate_driver():
    #########################################################################################
    #Instatiate Selenium driver
    #Returns the handle object
    #########################################################################################
    chrome_options = webdriver.ChromeOptions()
    #CHROMEDRIVER_PATH = "/app/.chromedriver/bin/chromedriver"
    CHROMEDRIVER_PATH = executable_path #NEED TO CHANGE IN HROKU
    chrome_options.binary_location = '.apt/usr/bin/google-chrome-stable'
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('headless')
    #Instatiate selenium driver with the right options and return the handle
    #driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=chrome_options) #NEED TO CHANGE IN HROKU
    driver = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH)
    return driver



def scrape_latest_news(st):
    #########################################################################################
    #Scrape the latest news
    #Returns news_title, news_p
    #########################################################################################
    
    news_title, news_p = None, None
    #Configure Browser
    browser = instatiate_driver()
    try:
        #Visit url
        browser.get(nasa_mars_news)
        #bs object with lxml parser
        time.sleep(st)#This is very important
        soup = bs(browser.page_source, 'lxml')
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
    browser = browser = instatiate_driver()

    try:
        #Visit url
        browser.get(nasa_jpl)
        #bs object with lxml parser
        time.sleep(st)#This is very important
        #Click a button "FULL IMAGE"
        browser.find_element_by_id('full_image').click()
        time.sleep(1)

        #Click more info button
        browser.find_element_by_css_selector('[id="fancybox-lock"]').find_element_by_css_selector('div[class="buttons"] a:nth-child(2)').click()    
        time.sleep(1)

        #Take the image link (largesize)
        featured_image_url = browser.find_element_by_css_selector('figure[class="lede"] a').get_attribute('href')
        
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
    browser = browser = instatiate_driver()
    
    try:
        #Visit url
        browser.get(mars_twitter_page)
        #bs object with lxml parser
        time.sleep(st)#This is very important
        soup = bs(browser.page_source, 'lxml')
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
    browser = browser = instatiate_driver()

    try:
        #Visit url
        browser.get(usgs_search)
        #bs object with lxml parser
        time.sleep(st)#This is very important (site loads super slow)
        soup = bs(browser.page_source, 'lxml')
        hs_links = soup.find(id='product-section').find_all('a',class_="itemLink product-item")
        for index,link in enumerate(hs_links):
            if link.img is None:
                title = re.sub(' Enhanced', '', link.text)
            else:
                browser.get(usgs_base+link['href'])
                time.sleep(1)
                img_url = browser.find_element_by_css_selector('img[class="wide-image"]').get_attribute('src')
            
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