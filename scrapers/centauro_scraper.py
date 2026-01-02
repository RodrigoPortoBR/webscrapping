"""
Scraper para o site Centauro
Usa Selenium devido ao bloqueio de requisições HTTP diretas
Extrai informações de preço do tênis Asics Gel Resolution X
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time
import re
from typing import Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_centauro(url: str, headless: bool = True, timeout: int = 30) -> Optional[Dict[str, any]]:
    """
    Faz scraping do preço no site Centauro usando Selenium
    
    Args:
        url: URL do produto na Centauro
        headless: Se True, executa o navegador em modo headless (sem interface)
        timeout: Timeout em segundos para carregamento da página
        
    Returns:
        Dict com informações do produto ou None se houver erro
    """
    driver = None
    try:
        # Configurar Chrome - usando exatamente a mesma configuração do diagnostic
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Acessar a página
        logger.info(f"Acessando Centauro: {url}")
        driver.get(url)
        
        # Aguardar carregamento - exatamente como no diagnostic
        time.sleep(5)
        
        # Obter page source
        page_source = driver.page_source
        logger.info(f"Tamanho do page source: {len(page_source)} caracteres")
        
        # Extrair nome do produto
        product_name = "Tênis ASICS Gel-Resolution X Clay"
        try:
            h1 = driver.find_element(By.TAG_NAME, "h1")
            if h1 and h1.text:
                product_name = h1.text.strip()
                logger.info(f"Nome do produto: {product_name}")
        except Exception:
            pass
        
        # Procurar por todos os preços - exatamente como no diagnostic
        price_pattern = re.compile(r'R\$\s*(\d+\.?\d*),(\d{2})')
        matches = price_pattern.findall(page_source)
        
        logger.info(f"Total de matches de preço: {len(matches)}")
        
        if not matches:
            logger.warning("Nenhum preço encontrado no page source")
            return None
        
        # Converter todos os preços
        prices = []
        for match in matches:
            potential_price = float(f"{match[0].replace('.', '')}.{match[1]}")
            prices.append(potential_price)
        
        # Filtrar por faixa razoável (500-5000)
        prices_filtered = [p for p in prices if 500 <= p <= 5000]
        
        logger.info(f"Preços filtrados (500-5000): {prices_filtered}")
        
        if not prices_filtered:
            logger.warning("Nenhum preço na faixa esperada encontrado")
            return None
        
        # Remover duplicatas e ordenar
        prices_unique = sorted(list(set(prices_filtered)))
        
        # O menor preço é geralmente o PIX, o próximo é o preço normal
        pix_price = prices_unique[0]
        regular_price = prices_unique[1] if len(prices_unique) > 1 else prices_unique[0]
        
        result = {
            'store': 'Centauro',
            'product_name': product_name,
            'price': pix_price,  # Usar o menor preço (PIX) como preço principal
            'pix_price': pix_price,
            'regular_price': regular_price,
            'url': url,
            'currency': 'BRL'
        }
        
        logger.info(f"Centauro - Produto: {product_name}, Preço PIX: R$ {pix_price:.2f}, Preço Normal: R$ {regular_price:.2f}")
        return result
        
    except Exception as e:
        logger.error(f"Erro ao processar dados da Centauro: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # Teste do scraper
    test_url = "https://www.centauro.com.br/tenis-asics-gel-resolution-x-clay-masculino-992675.html?cor=1L"
    print(f"Testando scraper Centauro...")
    result = scrape_centauro(test_url, headless=True)
    if result:
        print(f"\n✓ Scraper Centauro funcionando!")
        print(f"  Produto: {result['product_name']}")
        print(f"  Preço: R$ {result['price']:.2f}")
        if result.get('pix_price'):
            print(f"  Preço Pix: R$ {result['pix_price']:.2f}")
        if result.get('regular_price'):
            print(f"  Preço Normal: R$ {result['regular_price']:.2f}")
    else:
        print("\n✗ Erro ao executar scraper Centauro")
