"""Scraper específico para o Instagram."""
from bs4 import BeautifulSoup
from typing import Dict
from datetime import datetime
import time
from ..posts_scraper import PostsScraper


class InstagramScraper(PostsScraper):
    """Scraper para posts do Instagram."""
    
    BASE_URL = "https://www.instagram.com"
    
    def __init__(self, headless: bool = True, **kwargs):
        """Inicializa o InstagramScraper com wait_until='domcontentloaded'."""
        super().__init__(headless=headless, wait_until="domcontentloaded", **kwargs)
    
    def extrair_dados_post(self, legenda: str) -> Dict[str, any]:
        """
        Extrai dados específicos de um post do Instagram a partir da legenda capturada.
        
        Args:
            legenda: Texto completo capturado da página
        
        Returns:
            Dicionário com autor, legenda_limpa, curtidas, data_post
        """
        print(f"🔍 Extraindo dados específicos do Instagram da legenda...")
        
        try:
            import re
            
            # Corta a legenda até encontrar o trecho de login/footer
            legenda_limpa = legenda
            if legenda_limpa:
                marcadores_fim = [
                    "Log into like or comment.",
                    "Log in to like or comment.",
                    "See more posts",
                    "Meta\nAbout",
                ]
                
                for marcador in marcadores_fim:
                    if marcador in legenda_limpa:
                        legenda_limpa = legenda_limpa.split(marcador)[0].strip()
                        break
            
            # Extrai autor (username) da primeira linha da legenda
            autor = None
            if legenda_limpa:
                linhas = legenda_limpa.split('\n')
                for linha in linhas[:3]:  # Verifica as 3 primeiras linhas
                    linha_limpa = linha.strip()
                    # Verifica se parece com um username (sem espaços, não muito longo)
                    if linha_limpa and ' ' not in linha_limpa and len(linha_limpa) < 50 and not linha_limpa.startswith('#'):
                        # Remove "Verified" se existir
                        autor = linha_limpa.replace('Verified', '').strip()
                        break
            
            # Extrai curtidas da legenda
            curtidas = None
            if legenda_limpa:
                # Procura por padrões de curtidas na legenda
                curtidas_patterns = [
                    r'(\d+(?:[,\.]\d+)*)\s*likes',
                    r'(\d+(?:[,\.]\d+)*)\s*curtidas',
                    r'(\d+(?:[,\.]\d+)*)\s*gostaram',
                    r'(\d+(?:[,\.]\d+)*)\s*like',
                ]
                
                for pattern in curtidas_patterns:
                    match = re.search(pattern, legenda_limpa.lower())
                    if match:
                        try:
                            numero_str = match.group(1).replace(',', '').replace('.', '')
                            curtidas = int(numero_str)
                            break
                        except:
                            curtidas = match.group(1)
                            break
            
            # Extrai data de publicação (formato relativo ou ISO)
            data_post = None
            if legenda_limpa:
                # Procura por padrões de data
                data_patterns = [
                    r'(\d+[hdwmy])',  # 2d, 1w, 3h, 4m, 1y
                    r'(\d+\s*(?:hour|day|week|month|year)s?\s*ago)',
                    r'(\d+\s*(?:hora|dia|semana|mês|ano)s?\s*atrás)',
                    r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # ISO format
                ]
                
                for pattern in data_patterns:
                    match = re.search(pattern, legenda_limpa)
                    if match:
                        data_post = match.group(1)
                        break
            
            dados = {
                "author": autor,
                "text": legenda_limpa,
                "likes": curtidas,
                "date_post": data_post
            }
            
            print(f"✓ Dados extraídos:")
            print(f"   - Autor: {autor or 'Não encontrado'}")
            print(f"   - Legenda: {legenda_limpa[:50] + '...' if legenda_limpa and len(legenda_limpa) > 50 else legenda_limpa or 'Não encontrada'}")
            print(f"   - Curtidas: {curtidas or 'Não encontrado'}")
            print(f"   - Data: {data_post or 'Não encontrada'}")
            
            return dados
            
        except Exception as e:
            print(f"✗ Erro ao extrair dados: {e}")
            import traceback
            traceback.print_exc()
            return {
                "autor": None,
                "legenda": "",
                "curtidas": None,
                "data_post": None
            }
    
    def processar_post(self, url: str, arquivo_saida: str = "post_instagram.json") -> Dict:
        """
        Processa um post completo do Instagram: captura texto e extrai dados.
        
        Args:
            url: URL do post do Instagram
            arquivo_saida: Nome do arquivo JSON de saída (timestamp será adicionado automaticamente)
        
        Returns:
            Dicionário com todos os dados do post
        """
        print(f"\n{'='*60}")
        print(f"📱 PROCESSANDO POST DO INSTAGRAM")
        print(f"{'='*60}\n")
        
        # Adiciona timestamp ao nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_base, extensao = arquivo_saida.rsplit('.', 1) if '.' in arquivo_saida else (arquivo_saida, 'json')
        arquivo_com_timestamp = f"{nome_base}_{timestamp}.{extensao}"
        
        # 1. Captura o texto completo da página
        texto_completo = self.capturar_texto_rede_social(url)
        
        # 2. Extrai dados específicos do Instagram a partir do texto capturado
        dados_especificos = self.extrair_dados_post(texto_completo)
        
        # 3. Salva tudo em JSON
        resultado = self.salvar_json(
            texto_capturado=texto_completo,
            url=url,
            legenda=dados_especificos.get("text", ""),
            curtidas=dados_especificos.get("likes"),
            data_post=dados_especificos.get("date_post"),
            autor=dados_especificos.get("author"),
            arquivo=arquivo_com_timestamp,
            social_network="instagram"
        )
        
        print(f"\n{'='*60}")
        print(f"✅ PROCESSAMENTO CONCLUÍDO")
        print(f"{'='*60}\n")
        
        return resultado
