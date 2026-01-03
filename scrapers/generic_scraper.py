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
            in_stock = self._find_stock(soup)
            
            if price:
                return {
                    'price': price,
                    'product_name': name or "Unknown Product",
                    'url': url,
                    'currency': 'EUR', # Defaulting to EUR as per user request context
                    'in_stock': in_stock
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def _find_stock(self, soup: BeautifulSoup) -> bool:
        """
        Attempts to find if product is in stock.
        Returns True by default if no clear 'out of stock' indicator is found.
        """
        # Strategy 1: OpenGraph / Meta tags
        availability = soup.find('meta', property='og:availability') or \
                       soup.find('meta', property='product:availability') or \
                       soup.find('meta', attrs={'name': 'availability'})
        
        if availability and availability.get('content'):
            content = availability['content'].lower()
            if any(x in content for x in ['instock', 'in stock', 'available', 'disponivel', 'disponível']):
                return True
            if any(x in content for x in ['oos', 'out of stock', 'unavailable', 'esgotado', 'indisponivel']):
                return False

        # Strategy 2: Schema.org JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                # Helper to check availability in schema dict
                def check_schema_stock(obj):
                    if isinstance(obj, dict):
                        avail = obj.get('availability')
                        if isinstance(avail, str):
                            if 'InStock' in avail: return True
                            if 'OutOfStock' in avail: return False
                    return None

                if isinstance(data, dict):
                    if data.get('@type') == 'Product':
                        offers = data.get('offers')
                        if isinstance(offers, (dict, list)):
                            res = check_schema_stock(offers if isinstance(offers, dict) else (offers[0] if offers else {}))
                            if res is not None: return res
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            res = check_schema_stock(item.get('offers'))
                            if res is not None: return res
            except:
                continue

        # Strategy 3: Common keywords in page text
        # We look for "out of stock" patterns first to be safe
        out_of_stock_patterns = [
            'esgotado', 'indisponível', 'indisponivel', 'fora de stock', 
            'out of stock', 'sold out', 'not available', 'indisponibile',
            'encomenda especial', 'feito por encomenda', 'avisar-me', 
            'order from supplier', 'encomenda a fornecedor', 'product-unavailable'
        ]
        
        # Check specific containers first (buttons, status labels)
        # Increased search scope for text checks
        stock_elements = soup.find_all(['span', 'div', 'p', 'button', 'a'])
        for elem in stock_elements:
            text = elem.get_text(strip=True).lower()
            if any(p in text for p in out_of_stock_patterns):
                # Verify it's not a small disclaimer but looks like a status
                if len(text.split()) < 10: # Status labels are usually short
                    return False
        
        # Special check for Fnac: often has a button "Avisar-me" or text "Indisponível online"
        page_text = soup.get_text().lower()
        if 'indisponível online' in page_text or 'stock esgotado' in page_text:
            return False

        # Strategy 4: Check "Add to Cart" button existence/state
        # Improved regex to catch more variations
        cart_patterns = r'comprar|carrinho|cesto|adicionar|add to cart|buy|purchase|encomendar'
        cart_buttons = soup.find_all(['button', 'input', 'a'], string=re.compile(cart_patterns, re.IGNORECASE))
        
        if cart_buttons:
            for btn in cart_buttons:
                # Check if button is visibly disabled
                if 'disabled' in btn.attrs or 'disabled' in ' '.join(btn.get('class', [])).lower():
                    continue 
                # Check for hidden or aria-disabled
                if btn.get('aria-disabled') == 'true' or 'hidden' in btn.attrs:
                    continue
                return True # Found an active buying button

        # Fallback: if we have "encomendar" button but it's marked as encomenda especial above,
        # we already returned False in Strategy 3.
        
        # Default logic: if we found a price, we assumed True unless we found an OOS marker.
        # But if we can't find ANY buying button, it's safer to assume False for automated monitoring.
        return len(cart_buttons) > 0

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
