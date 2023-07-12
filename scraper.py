# Cigna: Scraping info for all doctors under New York, NY 10016

# import libraries
import yaml
from get_facets import Facets
from page_scraper import PageScraper

def get_args_main(file_path) -> dict:
    """
    Gets all the arguments for main() from the constants.yml file

    Returns:
        dict: all args in this dict
    """
    
    with open(file_path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        
    return config
        
def main(args_file_path: str) -> None:
    
    main_args = get_args_main(args_file_path)
    
    # get facets args
    base_facet_url = main_args['facets_args']['facets_base_url']
    base_facet_timeout = main_args['facets_args']['facets_timeout']
    facet_file_path = main_args['facets_args']['facets_file_path']
    
    # get facets    
    facets_obj = Facets(base_facet_url, base_facet_timeout, facet_file_path)
    facets = facets_obj.get_facets()
                
    # get page args
    page_args = main_args['page_args']
    
    for facet, val in facets.items():
        
        if facet == 'Speech Therapy':
            print("Scraping for ", facet, " with count: ", val)
            
            facet_en = facet.replace(' ', '%20')
            facet_path = facet.replace(' ', '_')
            
            # update facet for file path
            page_args['extract_file_path'] += f"{facet_path}_"
            page_args['max_count'] = val
            page_args['facet'] = facet_en
            
            pg_scraper = PageScraper(page_args)
            args = pg_scraper.start_pagination()
                
    print(args.__dict__)
    
if __name__ == "__main__":
    main('./constants.yml')