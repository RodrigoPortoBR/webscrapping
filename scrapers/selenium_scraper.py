import logging
import time
from typing import Optional, Dict
from bs4 import BeautifulSoup
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from scrapers.generic_scraper import GenericScraper

logger = logging.getLogger(__name__)

class SeleniumScraper:
    def __init__(self):
        self.chrome_options = uc.ChromeOptions()
        # Enable headless for automated operation. Some sites may still block.
        # Use simple os.environ check or default to headless=new for stability
        import os
        if os.environ.get('HEADLESS', 'false').lower() == 'true':
             self.chrome_options.add_argument('--headless=new')
        
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--window-size=1920,1080')
        self.chrome_options.add_argument('--start-maximized')
        # Let explicit UA be handled by uc or set if needed. Removing for now to avoid mismatch.
        # self.chrome_options.add_argument('user-agent=...')
        
        # Instantiate GenericScraper to reuse its parsing logic
        self.parser = GenericScraper()

    def scrape(self, url: str) -> Optional[Dict[str, any]]:
        """
        Scrapes a URL using Selenium to handle dynamic content (JS rendering).
        Reuses GenericScraper for parsing the HTML.
        """
        driver = None
        try:
            logger.info(f"Selenium: Acessando {url}...")
            driver = uc.Chrome(options=self.chrome_options)
            driver.get(url)
            
            # Wait for content to load
            time.sleep(10) # Increased wait
            
            # Scroll to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Reuse parsing logic
            price = self.parser._find_price(soup)
            name = self.parser._find_name(soup)
            
            if price:
                return {
                    'price': price,
                    'product_name': name or "Unknown Product",
                    'url': url,
                    'currency': 'EUR'
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Erro no Selenium para {url}: {e}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except OSError:
                    pass # Ignore WinError 6 on quit

def scrape_selenium(url: str) -> Optional[Dict]:
    scraper = SeleniumScraper()
    return scraper.scrape(url)
