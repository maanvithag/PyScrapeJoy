# import libraries
from playwright.sync_api import sync_playwright, TimeoutError
import json
import random
import time

class PageScraper:
    def __init__(self, args: dict) -> None:
        """
        Initializing PageScraper object

        Args:
            base_url (str): page url to be scraped
            file_path (str): path of the JSON file dump
            timeout (int): number of milliseconds after which page closes
        """
        self.url = args['base_url']
        self.extract_file_path = args['extract_file_path']
        self.page = args['page']
        self.offset = args['offset']
        self.limit = args['limit']
        self.timeout = args['timeout']
        self.max_count = args['max_count']
        self.facet = args['facet']
        self.min_sleep = args['min_sleep']
        self.max_sleep = args['max_sleep']
    
    def cigna_scraper(self, curr_page_url: str, curr_page_file_path: str) -> dict:
        """
        this scrapes all the search results from each page using base url
        and dumps it into a JSON file using the file path given
        
        Args:
            curr_page_url (str): current page url to be scraped
            curr_page_file_path (str): path of the current JSON file dump

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
                        with open(curr_page_file_path, 'w') as file:
                            json.dump(raw_data_list, file)
                                    
            browser = p.chromium.launch(headless=False) 
            page = browser.new_page() 
            
            try:
                page.on("response", handle_response) 
                page.goto(curr_page_url, wait_until="networkidle", timeout=self.timeout)
            except TimeoutError:
                if 'total_count' in log_response:
                    log_response['success'] = "extracted required data and dumped to file"
                else:
                    log_response['failed'] = "Timeout Error: Please increase timeout greater than " + str(self.timeout//1000) + " secs"
                
            page.context.close() 
            browser.close()
            
        # return log_response    
        return log_response

    def execute_scraper(self, curr_page_url: str, curr_page_file_path: str, continue_loop: bool):
        """
        this calls the playwright scraper cigna_scraper()

        Args:
            curr_page_url (str): current page url to be scraped
            curr_page_file_path (str): file path for the current page JSON dump
            continue_loop (bool): flag which decides to continue pagination or not
        """
        
        # get the log from the scraper
        log_output = self.cigna_scraper(curr_page_url, curr_page_file_path)
        
        # Print the script's log
        print("Script log: ", log_output)
        
        # stop pagination if page not successfully scraped
        if 'success' not in log_output:
            continue_loop = False
            print("Unable to scrap data for page: " + curr_page_url)
            
        return continue_loop

    def start_pagination(self) -> dict:
        """
        this controls the pagination for each base url

        Returns:
            dict: updated args dict 
        """
        
        # default pagination flag
        continue_loop = True

        # pagination loop
        while continue_loop and (self.page == 1 or self.offset + self.limit < self.max_count + 1):
                    
            print("Scraping data for Page: " + str(self.page) + " with offset: " + str(self.offset))
            
            # form file path
            curr_page_file_path = self.extract_file_path + f"page_{self.page}.json"
            
            # form url
            curr_page_url = self.url + f"&offset={self.offset}&limit={self.limit}&facets=facetSpecialties:{self.facet}"
            # execute playwright scraper for current page
            continue_loop = self.execute_scraper(curr_page_url, curr_page_file_path, continue_loop)
                
            if not continue_loop:
                print("Stopping pagination loop at: ", {'page': self.page, 'offset': self.offset, 'timeout': self.timeout})
                break
            
            # random sleep secs 
            sleep_secs = random.randint(self.min_sleep, self.max_sleep)
            print("Sleeping for " + str(sleep_secs))
            
            # sleep for few secs to give time for the next instance of scraper to begin
            time.sleep(sleep_secs)
            
            # increment page & offset
            self.page += 1
            self.offset += self.limit
        
        return self
