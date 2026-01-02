import requests
from bs4 import BeautifulSoup
import re
import json
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class GenericScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

    def scrape(self, url: str) -> Optional[Dict[str, any]]:
        """
        Generic scraper that attempts to find product price and name
        using common patterns (Schema.org, OpenGraph, specific class names).
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            price = self._find_price(soup)
            name = self._find_name(soup)
            
            if price:
                return {
                    'price': price,
                    'product_name': name or "Unknown Product",
                    'url': url,
                    'currency': 'EUR' # Defaulting to EUR as per user request context
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def _find_price(self, soup: BeautifulSoup) -> Optional[float]:
        # Strategy 1: OpenGraph / Meta tags
        meta_price = soup.find('meta', property='product:price:amount') or \
                     soup.find('meta', property='og:price:amount')
        if meta_price and meta_price.get('content'):
            return self._parse_price(meta_price['content'])

        # Strategy 2: Schema.org JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    # Check for Product -> offers -> price
                    if data.get('@type') == 'Product':
                        offers = data.get('offers')
                        if isinstance(offers, dict):
                            price = offers.get('price') or offers.get('lowPrice')
                            if price:
                                return self._parse_price(price)
                        elif isinstance(offers, list) and len(offers) > 0:
                            price = offers[0].get('price') or offers[0].get('lowPrice')
                            if price:
                                return self._parse_price(price)
                # Handle list of structured data
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            offers = item.get('offers')
                            if isinstance(offers, dict):
                                price = offers.get('price') or offers.get('lowPrice')
                                if price:
                                    return self._parse_price(price)
            except:
                continue

        # Strategy 3: data-price and data-* attributes
        for attr in ['data-price', 'data-product-price', 'data-price-amount']:
            elem = soup.find(attrs={attr: True})
            if elem:
                val = self._parse_price(elem.get(attr))
                if val:
                    return val

        # Strategy 4: Common keywords in class/id with priority matching
        # Extended patterns for price detection
        price_patterns = ['price', 'preco', 'precio', 'prix', 'cost', 'value']
        
        for pattern in price_patterns:
            # Try itemprop first (most reliable)
            elem = soup.find(attrs={'itemprop': 'price'})
            if elem:
                text = elem.get_text(strip=True) or elem.get('content') or ''
                val = self._parse_price(text)
                if val:
                    return val
            
            # Try class/id with pattern
            candidates = soup.find_all(lambda tag: (
                tag.name in ['span', 'div', 'p', 'meta', 'strong', 'b'] and
                (pattern in ' '.join(tag.get('class', [])).lower() or
                 pattern in str(tag.get('id', '')).lower())
            ))
            
            for tag in candidates:
                text = tag.get_text(strip=True) or tag.get('content') or ''
                val = self._parse_price(text)
                if val:
                    return val

        # Strategy 5: Fallback - search for currency symbols with numbers
        # Look for EUR, €, patterns
        text_content = soup.get_text()
        currency_patterns = [
            r'€\s*([\d.,]+)',  # € 123.45
            r'([\d.,]+)\s*€',  # 123.45 €
            r'EUR\s*([\d.,]+)',  # EUR 123.45
            r'([\d.,]+)\s*EUR',  # 123.45 EUR
        ]
        
        for pattern in currency_patterns:
            matches = re.findall(pattern, text_content)
            if matches:
                # Try to find a valid price from matches
                for match in matches:
                    val = self._parse_price(match)
                    if val and 10 < val < 10000:  # Reasonable price range
                        return val

        return None

    def _find_name(self, soup: BeautifulSoup) -> Optional[str]:
        # Strategy 1: OG Title
        meta_title = soup.find('meta', property='og:title')
        if meta_title: return meta_title.get('content')
        
        # Strategy 2: H1
        h1 = soup.find('h1')
        if h1: return h1.get_text(strip=True)
        
        # Strategy 3: Title tag
        if soup.title: return soup.title.get_text(strip=True)
        
        return None

    def _parse_price(self, text: str) -> Optional[float]:
        if not text: return None
        # Remove currency symbols and non-numeric chars except . and ,
        # Handle 1.234,56 (EU) vs 1,234.56 (US) logic if needed. 
        # Assuming EU/PT format mostly: dots as thousands, comma as decimal
        try:
            # Simple cleanup: keep only digits, dot, comma
            clean = re.sub(r'[^\d.,]', '', str(text))
            
            # If we have comma, replace dot with nothing, comma with dot
            # e.g. 1.200,50 -> 1200.50
            if ',' in clean:
                clean = clean.replace('.', '').replace(',', '.')
            
            val = float(clean)
            if 0 < val < 10000: # Sanity check
                return val
        except:
            pass
        return None

def scrape_generic(url: str) -> Optional[Dict]:
    scraper = GenericScraper()
    return scraper.scrape(url)
