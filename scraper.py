# Cigna: Scraping info for all doctors under New York, NY 10016

# import libraries
import random
import time
import json
from playwright.sync_api import sync_playwright, TimeoutError

# base url to extract search results for zipcode 10016 (New York) from cigna website
base_url = 'https://hcpdirectory.cigna.com/web/public/consumer/directory/doctors?city=New%20York&zipCode=10016&stateCode=NY&country=US&formattedAddress=New%20York,%20NY%2010016&latitude=40.747&longitude=-73.98&searchLocation=New%20York,%20NY%2010016&county=New%20york&providerGroupCode=P&providerAttributesName=MD&providerGroupCodes=P&searchCategoryType=doctor-name&searchCategoryCode=HSC03&searchTerm=MD&consumerCode=HDC001&medicalProductCode=AMP'

# base file path to store all extract info
base_file_path = './data_dump/10016_'

# default pagination parameters
page = 1
offset = 0
limit = 20

# default url & file path
curr_page_url = None
curr_page_file_path = None

# max search results
max_count = limit

# stop pagination loop
continue_loop = True

# timeout for each page
timeout = 30000

# Function for the scraper
def cigna_scraper(base_url, file_path, timeout):

    # log result from scraper
    log_response = {}
    
    with sync_playwright() as p: 
        def handle_response(response):
                        
            # the endpoint we are insterested in         
            if "providers" in response.url:
                json_data = response.json()
                
                if ('providers' in json_data['searchResult']['providerGroups'][0].keys()): 
                    
                    total_count = json_data['searchResult']['providerGroups'][0]['totalSearchCount']
                    log_response['total_count'] = total_count
                    
                    raw_data_list = json_data['searchResult']['providerGroups'][0]['providers']
                    log_response['curr_page_count'] = len(raw_data_list)
                                        
                    # Save the JSON data to a file
                    with open(file_path, 'w') as file:
                        json.dump(raw_data_list, file)
                                
        browser = p.chromium.launch(headless=False) 
        page = browser.new_page() 
        
        try:
            page.on("response", handle_response) 
            page.goto(base_url, wait_until="networkidle", timeout=timeout)
        except TimeoutError:
            if 'total_count' in log_response:
                log_response['success'] = "extracted required data and dumped to file"
            else:
                log_response['failed'] = "Timeout Error: Please increase timeout greater than " + str(timeout//1000) + " secs"
            
        page.context.close() 
        browser.close()
        
    # return log_response    
    return log_response

# Function that calls the Playwright scraper
def execute_scraper(curr_page_url, curr_page_file_path, continue_loop, timeout):
    
    # get the log from the scraper
    log_output = cigna_scraper(curr_page_url, curr_page_file_path, timeout)
    
    # Print the script's log
    print("Script log: ", log_output)
    
    # stop pagination if page not successfully scraped
    if 'success' not in log_output:
        continue_loop = False
        print("Unable to scrap data for page: " + curr_page_url)
        
    return continue_loop, log_output

# continue pagination: 
    """
    to be used, when continuing from a failed page instead of starting from first page
    for example, uncomment the below set of params to start scraping from page 41
    
    page = 49
    offset = 980
    continue_loop = True
    timeout = 50000
    max_count = 29303
    """

# pagination loop
while continue_loop and (page == 1 or offset + limit < max_count + 1):
    
    print("Scraping data for Page: " + str(page) + " with offset: " + str(offset))
    
    # form file path
    curr_page_file_path = base_file_path + f"page_{page}.json"
    
    # form url, if first page
    if page == 1:
        curr_page_url = base_url
        # execute playwright scraper for current page
        continue_loop, log_output = execute_scraper(curr_page_url, curr_page_file_path, continue_loop, timeout)
        # get total number of search results once for the first page
        if 'total_count' in log_output:
            max_count = int(log_output['total_count'])
    else:
        curr_page_url = base_url + f"&offset={offset}&limit={limit}"
        # execute playwright scraper for current page
        continue_loop, log_output = execute_scraper(curr_page_url, curr_page_file_path, continue_loop, timeout)
        
    if not continue_loop:
        print("Stopping pagination loop at: ", {'page': page, 'offset': offset, 'timeout': timeout} )
        break
    
    # random sleep secs 
    sleep_secs = random.randint(20, 30)
    print("Sleeping for " + str(sleep_secs))
    
    # sleep for few secs to give time for the next instance of scraper to begin
    time.sleep(sleep_secs)
    
    # increment page & offset
    page += 1
    offset += limit