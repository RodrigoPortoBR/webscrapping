"""
Scraper para o site Netshoes
Usa Selenium para extração mais confiável de preços
Extrai informações de preço do tênis Asics Gel Resolution X
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import re
from typing import Optional, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def scrape_netshoes(url: str, headless: bool = True, timeout: int = 30) -> Optional[Dict[str, any]]:
    """
    Faz scraping do preço no site Netshoes usando Selenium
    
    Args:
        url: URL do produto na Netshoes
        headless: Se True, executa o navegador em modo headless (sem interface)
        timeout: Timeout em segundos para carregamento da página
        
    Returns:
        Dict com informações do produto ou None se houver erro
    """
    driver = None
    try:
        # Configurar opções do Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        # Inicializar driver
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(timeout)
        
        # Acessar a página
        logger.info(f"Acessando Netshoes: {url}")
        driver.get(url)
        
        # Aguardar carregamento
        wait = WebDriverWait(driver, timeout)
        
        # Extrair nome do produto
        try:
            product_name_element = wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            product_name = product_name_element.text.strip()
        except TimeoutException:
            product_name = "Tênis ASICS GEL-Resolution X Clay"
        
        # Aguardar um pouco para garantir que os preços carregaram
        import time
        time.sleep(2)
        
        # Procurar pelo preço usando regex no page source
        price = None
        pix_price = None
        
        # Procurar por preços específicos usando contexto
        try:
            page_source = driver.page_source
            
            # Procurar especificamente pelo preço PIX (próximo ao texto "no Pix")
            pix_pattern = re.compile(r'R\$\s*(\d+\.?\d*),(\d{2})\s*no\s*Pix', re.IGNORECASE)
            pix_match = pix_pattern.search(page_source)
            
            if pix_match:
                pix_price = float(f"{pix_match.group(1).replace('.', '')}.{pix_match.group(2)}")
                logger.info(f"Preço PIX encontrado: R$ {pix_price:.2f}")
            
            # Procurar pelo preço parcelado (próximo ao texto "em até" ou "sem juros")
            installment_pattern = re.compile(r'R\$\s*(\d+\.?\d*),(\d{2})\s*em\s*até', re.IGNORECASE)
            installment_match = installment_pattern.search(page_source)
            
            if installment_match:
                price = float(f"{installment_match.group(1).replace('.', '')}.{installment_match.group(2)}")
                logger.info(f"Preço parcelado encontrado: R$ {price:.2f}")
            
            # Se não encontrou com os padrões específicos, tentar padrão mais genérico
            # mas filtrando por preços razoáveis para tênis (acima de R$ 500)
            if not pix_price and not price:
                price_pattern = re.compile(r'R\$\s*(\d+\.?\d*),(\d{2})')
                matches = price_pattern.findall(page_source)
                
                if matches:
                    # Converter e filtrar preços razoáveis para tênis premium
                    prices = []
                    for match in matches:
                        potential_price = float(f"{match[0].replace('.', '')}.{match[1]}")
                        if 500 <= potential_price <= 5000:  # Filtro mais restritivo
                            prices.append(potential_price)
                    
                    if prices:
                        # Remover duplicatas e ordenar
                        prices = sorted(list(set(prices)))
                        logger.info(f"Preços encontrados (fallback): {prices}")
                        # Usar o menor preço como PIX e o próximo como regular
                        pix_price = prices[0] if not pix_price else pix_price
                        price = prices[1] if len(prices) > 1 and not price else (prices[0] if not price else price)
                        
        except Exception as e:
            logger.warning(f"Erro ao extrair preços via regex: {e}")
        
        # Usar o melhor preço disponível (preferir PIX se disponível)
        final_price = pix_price if pix_price else price
        
        if not final_price:
            logger.warning(f"Não foi possível extrair o preço do site Netshoes")
            return None
        
        result = {
            'store': 'Netshoes',
            'product_name': product_name,
            'price': final_price,
            'pix_price': pix_price,
            'regular_price': price,
            'url': url,
            'currency': 'BRL'
        }
        
        logger.info(f"Netshoes - Produto: {product_name}, Preço: R$ {final_price:.2f}")
        return result
        
    except WebDriverException as e:
        logger.error(f"Erro do WebDriver ao acessar Netshoes: {e}")
        return None
    except Exception as e:
        logger.error(f"Erro ao processar dados da Netshoes: {e}")
        return None
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    # Teste do scraper
    test_url = "https://www.netshoes.com.br/p/tenis-asics-gelresolution-x-clay-masculino-azul-SG4-0139-008"
    result = scrape_netshoes(test_url, headless=False)  # headless=False para ver o navegador durante o teste
    if result:
        print(f"✓ Scraper Netshoes funcionando!")
        print(f"  Produto: {result['product_name']}")
        print(f"  Preço: R$ {result['price']:.2f}")
        if result.get('pix_price'):
            print(f"  Preço Pix: R$ {result['pix_price']:.2f}")
        if result.get('regular_price'):
            print(f"  Preço Normal: R$ {result['regular_price']:.2f}")
    else:
        print("✗ Erro ao executar scraper Netshoes")
