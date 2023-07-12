# import libraries
import os
from playwright.sync_api import sync_playwright, TimeoutError
import json

class Facets:

    def __init__(self, url: str, timeout: int, file_path: str) -> None:
        """
        Initializing Facets object
        
        Args:
            url (str): base url used for scraping
            timeout (int): number of milliseconds after which page closes
            file_path (str): path for the JSON file for facets dump
        """
        self.url = url
        self.timeout = timeout
        self.file_path = file_path

    def scrape_facets(self) -> dict:
        """
        from the base url, this scrapes all the specialties(facets) values 
        to filter results on and dumps it into a JSON file

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
                page.goto(self.url, wait_until="networkidle", timeout=self.timeout)
            except TimeoutError:
                if 'total_count' in log_response:
                    log_response['success'] = "extracted required data and dumped to file"
                else:
                    log_response['failed'] = "Timeout Error: Please increase timeout greater than " + str(self.timeout//1000) + " secs"
                
            page.context.close() 
            browser.close()
            
        # return log_response    
        return log_response

    def format_facets(self) -> dict:
        """
        this reads all the facets from the JSON file
        and returns as a dict

        Returns:
            dict: {name of the facet: count for results with this facet filter on}
        """
        
        # read the json dump
        facets_file = open(self.file_path, 'rb')
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

    def get_facets(self) -> dict:
        """
        get all facets in a dict

        Returns:
            dict: {name of the facet: count for results with this facet filter on}
        """
        
        # initialize facets
        facets = {}
        
        # check if facets file exists    
        if not os.path.exists(self.file_path):
            # get all facets to filter on
            log_output = self.scrape_facets()
            
            # check if facets has been retrived
            if 'success' in log_output:
                facets = self.format_facets()
            else:
                print("Unable to get Facets to filter on, Try Again")
                print(log_output)
                return facets
        else:            
            facets = self.format_facets()
        
        return facets