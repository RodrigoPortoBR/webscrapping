"""
Scraper para o site Prospin
Extrai informações de preço do tênis Asics Gel Resolution X
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_prospin(url: str) -> Optional[Dict[str, any]]:
    """
    Faz scraping do preço no site Prospin
    
    Args:
        url: URL do produto na Prospin
        
    Returns:
        Dict com informações do produto ou None se houver erro
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extrair nome do produto
        product_name = soup.find('h1', class_='product-name')
        if product_name:
            product_name = product_name.get_text(strip=True)
        else:
            product_name = "Tênis Asics Gel Resolution X"
        
        # Procurar por preços - Prospin geralmente usa classes como 'price', 'product-price', etc.
        price = None
        
        # Tentar diferentes seletores comuns
        price_selectors = [
            {'class': 'price'},
            {'class': 'product-price'},
            {'class': 'special-price'},
            {'itemprop': 'price'},
            {'class': 'valor-por'},
        ]
        
        for selector in price_selectors:
            price_element = soup.find(['span', 'div', 'p'], selector)
            if price_element:
                price_text = price_element.get_text(strip=True)
                # Extrair valor numérico (ex: "R$ 899,90" -> 899.90)
                price_match = re.search(r'R?\$?\s*(\d+\.?\d*),(\d{2})', price_text)
                if price_match:
                    price = float(f"{price_match.group(1).replace('.', '')}.{price_match.group(2)}")
                    break
        
        # Se não encontrou com os seletores, tentar buscar no texto
        if not price:
            # Procurar por padrão de preço no HTML
            price_pattern = re.compile(r'R?\$?\s*(\d+\.?\d*),(\d{2})')
            all_text = soup.get_text()
            matches = price_pattern.findall(all_text)
            if matches:
                # Pegar o primeiro preço encontrado que seja razoável (entre R$100 e R$5000)
                for match in matches:
                    potential_price = float(f"{match[0].replace('.', '')}.{match[1]}")
                    if 100 <= potential_price <= 5000:
                        price = potential_price
                        break
        
        if not price:
            logger.warning(f"Não foi possível extrair o preço do site Prospin")
            return None
        
        result = {
            'store': 'Prospin',
            'product_name': product_name,
            'price': price,
            'url': url,
            'currency': 'BRL'
        }
        
        logger.info(f"Prospin - Produto: {product_name}, Preço: R$ {price:.2f}")
        return result
        
    except requests.RequestException as e:
        logger.error(f"Erro ao acessar Prospin: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro ao processar dados da Prospin: {e}")
        return None


if __name__ == "__main__":
    # Teste do scraper
    test_url = "https://www.prospin.com.br/tenis-asics-gel-resolution-x-clay-saibro-marinho-e-verde"
    result = scrape_prospin(test_url)
    if result:
        print(f"✓ Scraper Prospin funcionando!")
        print(f"  Produto: {result['product_name']}")
        print(f"  Preço: R$ {result['price']:.2f}")
    else:
        print("✗ Erro ao executar scraper Prospin")
