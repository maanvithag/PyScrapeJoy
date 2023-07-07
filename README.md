# PyScrapeJoy

[![Playwright](https://img.shields.io/badge/playwright-1.35.0-seagreen)](https://playwright.dev/python/) [![Python](https://img.shields.io/badge/python-3.9.17-seagreen)](https://www.python.org/downloads/) [![Pandas](https://img.shields.io/badge/pandas-2.0.2-seagreen)](https://pypi.org/project/pandas/2.0.2/) [![MIT License](https://img.shields.io/badge/license-MIT-red)](https://www.python.org/downloads/) [![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2)](https://www.linkedin.com/in/maanvithag/) 

PyScrapeJoy is a python web scraper which scrapes and formats providers information from the cigna website, built using Python Sync Playwright. 

### Prerequisites:
- [Virtualenv](https://pypi.org/project/virtualenv/)
- [Playwright](https://playwright.dev/python/docs/intro)

### Step 1: Create a Virtualenv
```
$ virtualenv pyscrapejoy
$ source pyscrapejoy/bin/activate
```

### Step 2: Install all packages
```
$ pip install -r requirements.txt
$ playwright install
```

### Step 3: Run `scraper.py`
- This is the main python code for synchronous playwright scraper which starts from a base url 
- The base url is the search results of all doctors under New York, NY 10016 location. 
- This is a dynamically loaded page so the data is scraped by intercepting the response from the relevant XHR request and dumped into a file later to be cleaned and formatted.
- Each page link has a logical structure, so instead of emulating a button click for the next page, we can modify the base url with the respective offset. 
- The code loops through each page and dumps the response to a json file. 
- There are around 1500 pages with 20 results in each page.
- To not overload the website servers, we add a sleep for a random number of seconds in between pages. 
- After a while the pages take longer and longer to load so they timeout. Either we can increase the timeout and see if it works or have a 20-30 minutes downtime before continuing pagination.
- When we start scraping again after this downtime, we do not have to start from page 1 and just continue by taking in the parameters from last page that failed. 

### Step 4: Format data by running `format_scraped_data.ipynb`
- This is a Jupyter notebook for cleaning and formatting the raw scraped data. 
- We read all the json files under the given directory path, format them, and clean up for duplicates. 
- The end result is a pandas dataframe with 'providerId' as the key and all info on the providers in respective columns. I have added only a subset of these columns for this exercise, we can add more if required. 
- We can add more transformations after this or take one step ahead to load this into a NoSQL DB like MongoDB