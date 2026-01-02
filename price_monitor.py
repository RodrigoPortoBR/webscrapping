"""
Monitor de Preços - Dinâmico
Orquestra os scrapers, banco de dados e notificações
"""

import yaml
import logging
import time
import schedule
from datetime import datetime
from typing import List, Dict, Optional

# Importar o scraper genérico
from scrapers.generic_scraper import scrape_generic
from database import PriceDatabase
from notifier import EmailNotifier

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('price_monitor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PriceMonitor:
    """Classe principal do monitor de preços"""
    
    def __init__(self, config_file: str = "config.yaml"):
        """
        Inicializa o monitor de preços
        
        Args:
            config_file: Caminho para o arquivo de configuração
        """
        self.config = self._load_config(config_file)
        
        # Override email password from environment variable if available (for GitHub Actions)
        import os
        env_password = os.environ.get('EMAIL_PASSWORD')
        if env_password:
            self.config['email']['sender_password'] = env_password
            
        self.db = PriceDatabase()
        self.notifier = EmailNotifier(self.config['email'])
        
        logger.info("Monitor de Preços inicializado")
    
    def _load_config(self, config_file: str) -> Dict:
        """Carrega configurações do arquivo YAML"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuração carregada de {config_file}")
            return config
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            raise
    
    def scrape_all_stores(self) -> List[Dict]:
        """
        Executa scraping em todas as lojas configuradas
        
        Returns:
            Lista de dicionários com preços de cada loja
        """
        logger.info("=" * 60)
        logger.info(f"Iniciando verificação de preços - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        prices = []
        products = self.config.get('products', [])
        settings = self.config.get('settings', {})
        request_delay = settings.get('request_delay', 5)
        
        for product in products:
            name = product.get('name')
            url = product.get('url')
            store = product.get('store', 'Unknown')
            
            logger.info(f"Verificando {store}...")
            
            try:
                # Tentativa 1: Scraper Genérico (rápido)
                data = scrape_generic(url)
                
                # Tentativa 2: Selenium (fallback para sites dinâmicos)
                if not data:
                    logger.info(f"Scraper genérico falhou para {store}. Tentando Selenium...")
                    from scrapers.selenium_scraper import scrape_selenium
                    data = scrape_selenium(url)

                if data:
                    # Garantir que temos o nome configurado se o scraper falhar no nome
                    if data['product_name'] == "Unknown Product":
                        data['product_name'] = name
                    
                    data['store'] = store
                    prices.append(data)
                    logger.info(f"✓ {store}: R$ {data['price']} ({data['product_name']})")
                else:
                    logger.warning(f"✗ Falha ao obter preço de {store} (Genérico e Selenium)")
            except Exception as e:
                logger.error(f"Erro ao processar {store}: {e}")
            
            # Delay para evitar bloqueio
            time.sleep(request_delay)
        
        logger.info(f"Verificação concluída: {len(prices)}/{len(products)} lojas com sucesso")
        return prices
    
    def check_opportunities(self, current_prices: List[Dict], previous_prices: Optional[Dict] = None) -> List[Dict]:
        """
        Verifica se há oportunidades de compra baseado nas configurações
        """
        opportunities = []
        # Buscar config padrão de alerta
        default_alert = self.config.get('default_alert', {'type': 'threshold', 'max_price': 600.0})
        
        # Mapear configs de produtos para fácil acesso
        products_config = {p.get('name'): p for p in self.config.get('products', [])}
        
        for price_data in current_prices:
            store = price_data.get('store')
            current_price = price_data.get('price')
            
            # Tentar encontrar config específica pelo nome ou URL (simplificado aqui pelo nome que injetamos ou match)
            # Como injetamos 'store' no price_data, vamos tentar casar com a config
            
            # Encontrar max price para este item
            product_cfg = None
            for p in self.config.get('products', []):
                 if p.get('store') == store: 
                     product_cfg = p
                     break
            
            max_price = default_alert.get('max_price')
            if product_cfg and 'max_price' in product_cfg:
                max_price = product_cfg['max_price']
            
            if not current_price:
                continue
            
            opportunity = None
            
            # Lógica simples de threshold
            if current_price <= max_price:
                opportunity = price_data.copy()
                opportunity['reason'] = f'Preço {current_price} abaixo do alvo de {max_price}'
            
            if opportunity:
                opportunities.append(opportunity)
                logger.info(f"🎯 Oportunidade: {store} - {current_price} - {opportunity['reason']}")
        
        return opportunities
    
    def run_check(self):
        """Executa uma verificação completa de preços"""
        try:
            # Obter preços atuais
            current_prices = self.scrape_all_stores()
            
            if not current_prices:
                logger.warning("Nenhum preço foi obtido nesta verificação")
                return
            
            # Obter preços anteriores (mantendo lógica antiga de DB)
            previous_prices = self.db.get_latest_prices()
            
            # Salvar preços atuais
            self.db.add_price_check(current_prices)
            
            # Verificar oportunidades
            opportunities = self.check_opportunities(current_prices, previous_prices)
            
            # Enviar notificação se houver oportunidades
            if opportunities:
                logger.info(f"📧 Enviando notificação de {len(opportunities)} oportunidade(s)...")
                # Passar apenas prices atuais para notificação simplificada se database mudar
                self.notifier.send_price_alert(opportunities, previous_prices)
            else:
                logger.info("Nenhuma oportunidade identificada")
        
        except Exception as e:
            logger.error(f"Erro durante verificação: {e}", exc_info=True)
    
    def run_once(self):
        logger.info("Modo execução única")
        self.run_check()
    
    def run_scheduled(self):
        times = self.config['scheduling'].get('scheduled_times', ["12:00", "18:00"])
        logger.info(f"Agendando para: {times}")
        
        for t in times:
            schedule.every().day.at(t).do(self.run_check)
            
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Encerrando...")

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    
    monitor = PriceMonitor()
    if args.once:
        monitor.run_once()
    else:
        monitor.run_scheduled()

if __name__ == "__main__":
    main()
