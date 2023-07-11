# Cigna: Scraping info for all doctors under New York, NY 10016

# import libraries
import random
import time
import json
from playwright.sync_api import sync_playwright, TimeoutError
import os

def scrape_facets(base_url: str, timeout: int) -> dict:
    """
    from the base url, this scrapes all the specialties(facets) values 
    to filter results on and dumps it into a JSON file

    Args:
        base_url (str): base url used for scraping
        timeout (int): number of milliseconds after which page closes

    Returns:
        dict: this is the log with metadata on the scraped data
    """
    
    # log result from scraper
    log_response = {}
    
    with sync_playwright() as p: 
        def handle_response(response):
                        
            # the endpoint we are insterested in         
            if "facets" in response.url:
                json_data = response.json()
                
                if ('facets' in json_data['searchResult']['providerGroups'][0].keys()): 
                    
                    total_count = json_data['searchResult']['providerGroups'][0]['facets'][0]['totalCount']
                    log_response['total_count'] = total_count
                    
                    raw_data_list = json_data['searchResult']['providerGroups'][0]['facets'][0]['providerFacetDetail']
                    log_response['curr_page_count'] = len(raw_data_list)
                                        
                    # Save the JSON data to a file
                    with open('facets.json', 'w') as file:
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

def format_facets(file_path: str) -> dict:
    """
    this reads all the facets from the JSON file
    and returns as a dict

    Args:
        file_path (str): path for the JSON file for facets dump

    Returns:
        dict: {name of the facet: count for results with this facet filter on}
    """
    
    # read the json dump
    facets_file = open(file_path, 'rb')
    raw_facets_data = json.load(facets_file)
    
    # initialize dict
    facets = {}
    
    # create a dict and sort
    for facet in raw_facets_data:
        # get facet code
        code = facet['code']
        # get count for facet
        count = facet['totalCount']
        facets[code] = count
        
    # return facets
    return facets

def get_facets(url: str, timeout: int) -> dict:
    """
    get all facets in a dict

    Args:
        url (str): url to be scraped to get facets
        timeout (int): number of milliseconds after which page closes

    Returns:
        dict: {name of the facet: count for results with this facet filter on}
    """
    
    # initialize facets
    facets = {}
    
    # check if facets file exists
    file_path = './facets.json'
    
    if not os.path.exists(file_path):
        # get all facets to filter on
        log_output = scrape_facets(url, timeout)
        
        # check if facets has been retrived
        if 'success' in log_output:
            facets = format_facets('./facets.json')
        else:
            print("Unable to get Facets to filter on, Try Again")
            print(log_output)
            return facets
    else:            
        facets = format_facets('./facets.json')
    
    return facets
        
def cigna_scraper(base_url: str, file_path: str, timeout: int) -> dict:
    """
    this scrapes all the search results from each page using base url
    and dumps it into a JSON file using the file path given

    Args:
        base_url (str): page url to be scraped
        file_path (str): path of the JSON file dump
        timeout (int): number of milliseconds after which page closes

    Returns:
        dict: this is the log with metadata on the scraped data
    """

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

def execute_scraper(curr_page_url: str, curr_page_file_path: str, continue_loop: bool, timeout: int):
    """
    this calls the playwright scraper cigna_scraper()

    Args:
        curr_page_url (str): current page url to be scraped
        curr_page_file_path (str): file path for the current page JSON dump
        continue_loop (bool): flag which decides to continue pagination or not
        timeout (int): number of milliseconds after which page closes

    Returns:
        _type_: _description_
    """
    
    # get the log from the scraper
    log_output = cigna_scraper(curr_page_url, curr_page_file_path, timeout)
    
    # Print the script's log
    print("Script log: ", log_output)
    
    # stop pagination if page not successfully scraped
    if 'success' not in log_output:
        continue_loop = False
        print("Unable to scrap data for page: " + curr_page_url)
        
    return continue_loop, log_output

def start_pagination(continue_loop: bool, args: dict) -> dict:
    """
    this controls the pagination for each base url

    Args:
        continue_loop (bool): flag which decides to continue pagination or not
        args (dict): all arguments needed for pagination

    Returns:
        dict: updated args dict 
    """
    
    # get all params
    base_url = args['base_url']
    base_file_path = args['base_file_path']
    page = args['page']
    offset = args['offset']
    limit = args['limit']
    timeout = args['timeout']
    max_count = args['max_count']
    facet = args['facet']

    # pagination loop
    while continue_loop and (page == 1 or offset + limit < max_count + 1):
                
        print("Scraping data for Page: " + str(page) + " with offset: " + str(offset))
        
        # form file path
        curr_page_file_path = base_file_path + f"page_{page}.json"
        
        # form url
        curr_page_url = base_url + f"&offset={offset}&limit={limit}&facets=facetSpecialties:{facet}"
        # execute playwright scraper for current page
        continue_loop, log_output = execute_scraper(curr_page_url, curr_page_file_path, continue_loop, timeout)
            
        if not continue_loop:
            print("Stopping pagination loop at: ", {'page': page, 'offset': offset, 'timeout': timeout} )
            break
        
        # random sleep secs 
        sleep_secs = random.randint(1, 10)
        print("Sleeping for " + str(sleep_secs))
        
        # sleep for few secs to give time for the next instance of scraper to begin
        time.sleep(sleep_secs)
        
        # increment page & offset
        page += 1
        offset += limit

    # update all args passed
    args['page'] = page
    args['offset'] = offset
    
    return args
        
def main():
    
    # base url to extract search results for zipcode 10016 (New York) from cigna website
    base_url = 'https://hcpdirectory.cigna.com/web/public/consumer/directory/doctors?city=New%20York&zipCode=10016&stateCode=NY&country=US&formattedAddress=New%20York,%20NY%2010016&latitude=40.747&longitude=-73.98&searchLocation=New%20York,%20NY%2010016&county=New%20york&providerGroupCode=P&providerAttributesName=MD&providerGroupCodes=P&searchCategoryType=doctor-name&searchCategoryCode=HSC03&searchTerm=MD&consumerCode=HDC001&medicalProductCode=AMP'

    # base file path to store all extract info
    base_file_path = './data_dump/10016_'

    # default pagination parameters
    def_page = 1
    def_offset = 0
    def_limit = 20
    # default max search results
    def_max_count = def_limit
    # default pagination loop flag
    continue_loop = True
    # default timeout for each page
    def_timeout = 30000
    
    # get facets
    facets = get_facets(base_url, def_timeout)
    
    # all args to be passed
    args = {
        'base_url': base_url,
        'base_file_path': base_file_path, 
        'page': def_page, 
        'offset': def_offset, 
        'limit': def_limit, 
        'timeout': def_timeout, 
        'max_count': def_max_count,
        'facet': ''
        }
    
    for facet, val in facets.items():
        
        if facet == 'Adolescent Medicine':
            print("Scraping for ", facet, " with count: ", val)
            
            facet_en = facet.replace(' ', '%20')
            facet_path = facet.replace(' ', '_')
            
            # update facet for url
            args['base_url'] = base_url
            args['base_file_path'] = base_file_path + f"{facet_path}_"
            args['max_count'] = val
            args['page'] = def_page
            args['offset'] = def_offset
            args['facet'] = facet_en
            
            args = start_pagination(continue_loop, args)
                
    print(args)
    
if __name__ == "__main__":
    main()