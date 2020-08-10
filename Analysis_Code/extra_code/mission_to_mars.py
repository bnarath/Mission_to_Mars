
## Dependencies

from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = 'all'


import requests
from splinter import Browser
from bs4 import BeautifulSoup as bs
import time

from urls_list import * #where all urls and paths are saved

no_pages = 10

def scrape_mars_news(no_pages=10):
    #Scrape the latest news (pages = no_pages, default 10)
    #If there are not enough pages, then scrape till end (based on More at the end)
    #Return the unique news as list of dictionaries
    
    #Configure Browser
    browser = Browser(browser_choice, executable_path=executable_path, headless=True)
    #Visit url
    browser.visit(nasa_mars_news)
    page = 1
    next_page = True
    #Fieldnames to scrap
    fields = ['date', 'news_title', 'news_p']
    #Initialize news list
    news_list = []
    
    while (page<=no_pages) and (next_page is not None):
        #Create a bs object with lxml 
        soup = bs(browser.html, 'lxml')
        try:
            news = soup.find_all('li', class_='slide')
            #Append the scraped data to the list
            news_list += [{fields[index]:value.text for index,value in enumerate(news_entry.div.find(class_='list_text').find_all('div'))} for news_entry in news]
            #increment
            page+=1
            #Check if "more button" is present
            #This post is wow
            #https://stackoverflow.com/questions/46468030/how-select-class-div-tag-in-splinter
            next_page = browser.find_by_css('footer[class="list_footer more_button"] a')
            if next_page is not None:
                time.sleep(2)#Delay
                next_page.click()#Click More button
        except Exception as e:
            print(e)
            #Close browser to avoid resource issue (if the loop is finished)
            if (page==no_pages) or (next_page is None):
                browser.quit()
            
        #It looks like some of the pages have older data too. Hence, there are many duplicates.
        #We need to remove duplicates
    #Close browser to avoid resource issue
    browser.quit()
    
    #Remove duplicates
    unique_news_hash = set()
    to_retain_index = []
    for index, news in enumerate(news_list):
        if news['date']+news['news_title'] not in unique_news_hash: 
            unique_news_hash.update({news['date']+news['news_title']}) #Update the hash if not present
            to_retain_index.append(index) #Add the index to retain              


    news_list = [news_list[Id] for Id in to_retain_index]
    
    return news_list

news_list  = scrape_mars_news(no_pages=no_pages)
