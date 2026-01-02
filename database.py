"""
Sistema de armazenamento de histórico de preços
Usa JSON para persistência simples
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceDatabase:
    """Gerencia o histórico de preços em arquivo JSON"""
    
    def __init__(self, db_file: str = "price_history.json"):
        """
        Inicializa o banco de dados
        
        Args:
            db_file: Caminho para o arquivo JSON de histórico
        """
        self.db_file = db_file
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Cria o arquivo de banco de dados se não existir"""
        if not os.path.exists(self.db_file):
            self._save_data({
                "created_at": datetime.now().isoformat(),
                "history": []
            })
            logger.info(f"Banco de dados criado: {self.db_file}")
    
    def _load_data(self) -> Dict:
        """Carrega dados do arquivo JSON"""
        try:
            with open(self.db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao carregar banco de dados: {e}")
            return {"created_at": datetime.now().isoformat(), "history": []}
    
    def _save_data(self, data: Dict):
        """Salva dados no arquivo JSON"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erro ao salvar banco de dados: {e}")
    
    def add_price_check(self, prices: List[Dict]):
        """
        Adiciona uma nova verificação de preços ao histórico
        
        Args:
            prices: Lista de dicionários com informações de preço de cada loja
        """
        data = self._load_data()
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "prices": prices
        }
        
        data["history"].append(entry)
        self._save_data(data)
        
        logger.info(f"Verificação de preços salva: {len(prices)} lojas")
    
    def get_latest_prices(self) -> Optional[Dict]:
        """
        Retorna a última verificação de preços
        
        Returns:
            Dict com timestamp e preços, ou None se não houver histórico
        """
        data = self._load_data()
        history = data.get("history", [])
        
        if not history:
            return None
        
        return history[-1]
    
    def get_previous_prices(self) -> Optional[Dict]:
        """
        Retorna a penúltima verificação de preços (para comparação)
        
        Returns:
            Dict com timestamp e preços, ou None se não houver histórico suficiente
        """
        data = self._load_data()
        history = data.get("history", [])
        
        if len(history) < 2:
            return None
        
        return history[-2]
    
    def get_all_history(self) -> List[Dict]:
        """
        Retorna todo o histórico de preços
        
        Returns:
            Lista de verificações de preço
        """
        data = self._load_data()
        return data.get("history", [])
    
    def get_price_trend(self, store: str) -> List[Dict]:
        """
        Retorna o histórico de preços de uma loja específica
        
        Args:
            store: Nome da loja (ex: 'Prospin', 'Centauro', 'Netshoes')
            
        Returns:
            Lista de dicts com timestamp e preço
        """
        history = self.get_all_history()
        trend = []
        
        for entry in history:
            for price_info in entry.get("prices", []):
                if price_info.get("store") == store:
                    trend.append({
                        "timestamp": entry["timestamp"],
                        "price": price_info.get("price"),
                        "product_name": price_info.get("product_name")
                    })
        
        return trend
    
    def get_lowest_price(self, store: Optional[str] = None) -> Optional[Dict]:
        """
        Retorna o menor preço já registrado
        
        Args:
            store: Nome da loja (opcional). Se None, busca em todas as lojas
            
        Returns:
            Dict com informações do menor preço encontrado
        """
        history = self.get_all_history()
        lowest = None
        
        for entry in history:
            for price_info in entry.get("prices", []):
                if store and price_info.get("store") != store:
                    continue
                
                price = price_info.get("price")
                if price and (lowest is None or price < lowest["price"]):
                    lowest = {
                        "timestamp": entry["timestamp"],
                        "store": price_info.get("store"),
                        "price": price,
                        "product_name": price_info.get("product_name"),
                        "url": price_info.get("url")
                    }
        
        return lowest


if __name__ == "__main__":
    # Teste do banco de dados
    db = PriceDatabase("test_price_history.json")
    
    # Adicionar dados de teste
    test_prices = [
        {"store": "Prospin", "product_name": "Tênis Asics", "price": 899.90, "url": "http://example.com"},
        {"store": "Centauro", "product_name": "Tênis Asics", "price": 849.90, "url": "http://example.com"},
        {"store": "Netshoes", "product_name": "Tênis Asics", "price": 879.90, "url": "http://example.com"},
    ]
    
    db.add_price_check(test_prices)
    
    # Testar recuperação
    latest = db.get_latest_prices()
    print(f"✓ Última verificação: {latest['timestamp']}")
    print(f"  {len(latest['prices'])} preços salvos")
    
    # Limpar arquivo de teste
    if os.path.exists("test_price_history.json"):
        os.remove("test_price_history.json")
        print("✓ Teste concluído e arquivo de teste removido")
