"""
Sistema de notificação por e-mail
Envia alertas quando há oportunidades de compra
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailNotifier:
    """Gerencia envio de notificações por e-mail"""
    
    # Configurações SMTP para provedores comuns
    SMTP_CONFIGS = {
        'gmail': {
            'server': 'smtp.gmail.com',
            'port': 587
        },
        'outlook': {
            'server': 'smtp-mail.outlook.com',
            'port': 587
        },
        'hotmail': {
            'server': 'smtp-mail.outlook.com',
            'port': 587
        },
        'yahoo': {
            'server': 'smtp.mail.yahoo.com',
            'port': 587
        }
    }
    
    def __init__(self, config: Dict):
        """
        Inicializa o notificador
        
        Args:
            config: Dicionário com configurações de e-mail do config.yaml
        """
        self.config = config
        self.provider = config.get('provider', 'custom').lower()
        
        # Usar configuração do provedor ou custom
        if self.provider in self.SMTP_CONFIGS:
            smtp_config = self.SMTP_CONFIGS[self.provider]
            self.smtp_server = smtp_config['server']
            self.smtp_port = smtp_config['port']
        else:
            self.smtp_server = config.get('smtp_server')
            self.smtp_port = config.get('smtp_port', 587)
        
        self.sender_email = config.get('sender_email')
        self.sender_password = config.get('sender_password')
        self.recipient_email = config.get('recipient_email')
    
    def _create_price_alert_email(self, opportunities: List[Dict], previous_prices: Optional[Dict] = None) -> str:
        """
        Cria o HTML do e-mail de alerta de preço
        
        Args:
            opportunities: Lista de oportunidades de compra
            previous_prices: Preços anteriores para comparação
            
        Returns:
            HTML do e-mail
        """
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .header { background-color: #0066cc; color: white; padding: 20px; text-align: center; }
                .content { padding: 20px; }
                .opportunity { 
                    background-color: #f0f8ff; 
                    border-left: 4px solid #0066cc; 
                    padding: 15px; 
                    margin: 15px 0;
                    border-radius: 5px;
                }
                .price { font-size: 24px; font-weight: bold; color: #00aa00; }
                .old-price { text-decoration: line-through; color: #999; }
                .discount { color: #cc0000; font-weight: bold; }
                .store { font-weight: bold; color: #0066cc; }
                .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
                .button { 
                    display: inline-block; 
                    padding: 10px 20px; 
                    background-color: #00aa00; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px;
                    margin-top: 10px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>☕ Alerta de Preço - Monitor de Cafeteiras Sage</h1>
            </div>
            <div class="content">
                <p>Boa notícia! Encontramos oportunidades de compra para os produtos que você está acompanhando:</p>
        """
        
        for opp in opportunities:
            store = opp.get('store', 'Loja')
            price = opp.get('price', 0)
            product_name = opp.get('product_name', 'Máquina de Café Sage')
            url = opp.get('url', '#')
            reason = opp.get('reason', 'Preço atrativo')
            in_stock = opp.get('in_stock', True)
            stock_label = "✅ Em estoque" if in_stock else "❌ Esgotado"
            
            html += f"""
                <div class="opportunity">
                    <p class="store">🏪 {store}</p>
                    <p><strong>{product_name}</strong></p>
                    <p class="price">€ {price:.2f}</p>
                    <p><em>{stock_label}</em></p>
            """
            
            # Adicionar comparação com preço anterior se disponível
            if previous_prices:
                prev_price = self._get_previous_price(store, previous_prices)
                if prev_price and prev_price > price:
                    discount = ((prev_price - price) / prev_price) * 100
                    html += f"""
                        <p>
                            Preço anterior: <span class="old-price">€ {prev_price:.2f}</span><br>
                            <span class="discount">💰 Economia de € {prev_price - price:.2f} ({discount:.1f}% OFF)</span>
                        </p>
                    """
            
            html += f"""
                    <p><em>{reason}</em></p>
                    <a href="{url}" class="button">Ver Produto</a>
                </div>
            """
        
        html += """
                <p style="margin-top: 30px;">
                    <strong>Dica:</strong> Os preços podem mudar rapidamente. Recomendamos verificar o site antes de finalizar a compra.
                </p>
            </div>
            <div class="footer">
                <p>Este é um alerta automático do seu Monitor de Preços.</p>
                <p>Você está recebendo este e-mail porque configurou alertas para este produto.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _get_previous_price(self, store: str, previous_prices: Dict) -> Optional[float]:
        """Busca o preço anterior de uma loja específica"""
        if not previous_prices:
            return None
        
        for price_info in previous_prices.get('prices', []):
            if price_info.get('store') == store:
                return price_info.get('price')
        
        return None
    
    def send_price_alert(self, opportunities: List[Dict], previous_prices: Optional[Dict] = None) -> bool:
        """
        Envia alerta de oportunidade de preço
        
        Args:
            opportunities: Lista de oportunidades de compra
            previous_prices: Preços anteriores para comparação
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        if not opportunities:
            logger.info("Nenhuma oportunidade para notificar")
            return False
        
        try:
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'☕ Alerta de Preço Sage - {len(opportunities)} oportunidade(s)!'
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Criar versão texto simples
            text_content = "Alerta de Preço - Máquinas Sage\n\n"
            for opp in opportunities:
                text_content += f"{opp.get('store')}: € {opp.get('price', 0):.2f} ({'Em estoque' if opp.get('in_stock') else 'Esgotado'})\n"
                text_content += f"Produto: {opp.get('product_name')}\n"
                text_content += f"Link: {opp.get('url')}\n\n"
            
            # Criar versão HTML
            html_content = self._create_price_alert_email(opportunities, previous_prices)
            
            # Anexar ambas as versões
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)
            
            # Enviar e-mail
            logger.info(f"Conectando ao servidor SMTP: {self.smtp_server}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"✓ E-mail enviado com sucesso para {self.recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("Erro de autenticação SMTP. Verifique o e-mail e senha (use App Password para Gmail)")
            return False
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """
        Envia um e-mail de teste
        
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        test_opportunity = [{
            'store': 'Teste',
            'product_name': 'Sage Barista Express (TESTE)',
            'price': 599.00,
            'url': 'https://www.google.com',
            'reason': 'Este é um e-mail de teste do sistema de monitoramento',
            'in_stock': True
        }]
        
        return self.send_price_alert(test_opportunity)


if __name__ == "__main__":
    # Teste do notificador (requer configuração válida)
    print("Para testar o notificador, configure suas credenciais de e-mail no config.yaml")
    print("e execute: python -c \"from notifier import EmailNotifier; import yaml; config = yaml.safe_load(open('config.yaml'))['email']; EmailNotifier(config).send_test_email()\"")
