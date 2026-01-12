
"""
Web scraping module using BeautifulSoup4 for Drug Intelligence Automation
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
import time
from urllib.parse import urljoin, urlparse

from logger import get_logger


class WebScraper:
    """Web scraping functionality using BeautifulSoup4"""
    
    def __init__(self, base_url: str = None, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.logger = get_logger()
        
        # Set default headers to mimic browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_page(self, url: str, params: Dict = None) -> Optional[BeautifulSoup]:
        """Fetch a web page and return BeautifulSoup object"""
        try:
            self.logger.info(f"Fetching URL: {url}")
            
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'lxml')
            
            self.logger.debug(f"Successfully fetched and parsed: {url}")
            return soup
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching URL {url}: {str(e)}", exc_info=True)
            return None
    
    def fetch_page_with_retry(self, url: str, max_retries: int = 3, 
                              delay: int = 2) -> Optional[BeautifulSoup]:
        """Fetch page with retry mechanism"""
        for attempt in range(max_retries):
            try:
                soup = self.fetch_page(url)
                if soup:
                    return soup
            except Exception as e:
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
            if attempt < max_retries - 1:
                time.sleep(delay)
        
        self.logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
    
    def extract_table_data(self, soup: BeautifulSoup, table_id: str = None,
                          table_class: str = None) -> List[List[str]]:
        """Extract data from HTML table"""
        try:
            # Find table
            if table_id:
                table = soup.find('table', id=table_id)
            elif table_class:
                table = soup.find('table', class_=table_class)
            else:
                table = soup.find('table')
            
            if not table:
                self.logger.warning("Table not found")
                return []
            
            # Extract rows
            data = []
            rows = table.find_all('tr')
            
            for row in rows:
                cols = row.find_all(['td', 'th'])
                cols_data = [col.get_text(strip=True) for col in cols]
                if cols_data:  # Skip empty rows
                    data.append(cols_data)
            
            self.logger.info(f"Extracted {len(data)} rows from table")
            return data
            
        except Exception as e:
            self.logger.error(f"Error extracting table data: {str(e)}", exc_info=True)
            return []
    
    def extract_links(self, soup: BeautifulSoup, filter_pattern: str = None) -> List[Dict[str, str]]:
        """Extract all links from page"""
        try:
            links = []
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)
                
                # Make absolute URL
                if self.base_url:
                    href = urljoin(self.base_url, href)
                
                # Filter if pattern provided
                if filter_pattern and filter_pattern not in href:
                    continue
                
                links.append({
                    'url': href,
                    'text': text
                })
            
            self.logger.info(f"Extracted {len(links)} links")
            return links
            
        except Exception as e:
            self.logger.error(f"Error extracting links: {str(e)}", exc_info=True)
            return []
    
    def extract_drug_information(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract drug information from a page (custom logic)"""
        try:
            drug_info = {
                'name': '',
                'active_ingredient': '',
                'status': '',
                'approval_date': '',
                'manufacturer': ''
            }
            
            # Example: Extract drug name from h1 or specific class
            name_elem = soup.find('h1', class_='drug-name')
            if name_elem:
                drug_info['name'] = name_elem.get_text(strip=True)
            
            # Example: Extract active ingredient
            ingredient_elem = soup.find('div', class_='active-ingredient')
            if ingredient_elem:
                drug_info['active_ingredient'] = ingredient_elem.get_text(strip=True)
            
            # Example: Extract status
            status_elem = soup.find('span', class_='drug-status')
            if status_elem:
                drug_info['status'] = status_elem.get_text(strip=True)
            
            self.logger.debug(f"Extracted drug info: {drug_info['name']}")
            return drug_info
            
        except Exception as e:
            self.logger.error(f"Error extracting drug information: {str(e)}", exc_info=True)
            return {}
    
    def search_drug_database(self, drug_name: str, database_url: str) -> List[Dict[str, Any]]:
        """Search for drug in online database"""
        try:
            self.logger.info(f"Searching for drug: {drug_name}")
            
            # Example search parameters
            params = {
                'query': drug_name,
                'type': 'drug'
            }
            
            soup = self.fetch_page(database_url, params=params)
            
            if not soup:
                return []
            
            # Extract search results
            results = []
            result_divs = soup.find_all('div', class_='search-result')
            
            for div in result_divs:
                result = {
                    'name': div.find('h3').get_text(strip=True) if div.find('h3') else '',
                    'description': div.find('p').get_text(strip=True) if div.find('p') else '',
                    'url': div.find('a')['href'] if div.find('a') else ''
                }
                results.append(result)
            
            self.logger.info(f"Found {len(results)} results for {drug_name}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching drug database: {str(e)}", exc_info=True)
            return []
    
    def scrape_drug_approval_status(self, drug_url: str) -> Dict[str, str]:
        """Scrape drug approval status from regulatory website"""
        try:
            soup = self.fetch_page(drug_url)
            
            if not soup:
                return {}
            
            status_info = {
                'approval_status': '',
                'approval_date': '',
                'withdrawn_date': '',
                'notes': ''
            }
            
            # Example: Extract from table or specific divs
            status_table = soup.find('table', class_='approval-info')
            if status_table:
                rows = status_table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 2:
                        key = cols[0].get_text(strip=True).lower()
                        value = cols[1].get_text(strip=True)
                        
                        if 'approval status' in key:
                            status_info['approval_status'] = value
                        elif 'approval date' in key:
                            status_info['approval_date'] = value
                        elif 'withdrawn' in key:
                            status_info['withdrawn_date'] = value
            
            return status_info
            
        except Exception as e:
            self.logger.error(f"Error scraping approval status: {str(e)}", exc_info=True)
            return {}
    
    def scrape_multiple_pages(self, urls: List[str], delay: int = 1) -> List[Dict[str, Any]]:
        """Scrape multiple pages with delay"""
        results = []
        
        for idx, url in enumerate(urls):
            self.logger.info(f"Scraping page {idx + 1}/{len(urls)}: {url}")
            
            soup = self.fetch_page(url)
            if soup:
                # Extract information (customize based on your needs)
                info = self.extract_drug_information(soup)
                results.append(info)
            
            # Delay between requests to be polite
            if idx < len(urls) - 1:
                time.sleep(delay)
        
        return results
    
    def close(self):
        """Close the session"""
        self.session.close()
        self.logger.debug("Scraper session closed")


class DrugDatabaseScraper(WebScraper):
    """Specialized scraper for drug databases"""
    
    def __init__(self, database_name: str = "FDA"):
        super().__init__()
        self.database_name = database_name
        
        # Set database-specific URLs
        self.database_urls = {
            'FDA': 'https://www.accessdata.fda.gov/scripts/cder/daf/',
            'EMA': 'https://www.ema.europa.eu/en/medicines',
            'WHO': 'https://www.whocc.no/atc_ddd_index/'
        }
        
        self.base_url = self.database_urls.get(database_name, '')
    
    def search_by_active_ingredient(self, ingredient: str) -> List[Dict[str, Any]]:
        """Search drug by active ingredient"""
        try:
            self.logger.info(f"Searching {self.database_name} for: {ingredient}")
            
            # Implement database-specific search logic
            # This is a template - customize based on actual database structure
            
            results = []
            
            # Example implementation
            if self.database_name == "FDA":
                search_url = f"{self.base_url}?searchterm={ingredient}"
                soup = self.fetch_page(search_url)
                
                if soup:
                    # Extract results based on FDA page structure
                    results = self.extract_table_data(soup, table_class='fda-results')
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching by ingredient: {str(e)}", exc_info=True)
            return []
    
    def get_drug_approval_history(self, drug_name: str) -> List[Dict[str, str]]:
        """Get approval history for a drug"""
        try:
            self.logger.info(f"Fetching approval history for: {drug_name}")
            
            # Implement logic to fetch approval history
            history = []
            
            # This is a template - customize based on actual needs
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting approval history: {str(e)}", exc_info=True)
            return []