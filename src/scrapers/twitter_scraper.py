"""Scraper específico para o Twitter/X."""
from bs4 import BeautifulSoup
from typing import Dict
from datetime import datetime
import time
import re
from ..posts_scraper import PostsScraper


class TwitterScraper(PostsScraper):
    """Scraper para posts do Twitter/X."""
    
    BASE_URL = "https://twitter.com"
    
    def __init__(self, headless: bool = True, **kwargs):
        """Inicializa o TwitterScraper com wait_until='domcontentloaded'."""
        super().__init__(headless=headless, wait_until="domcontentloaded", **kwargs)
    
    def extrair_dados_post(self, legenda: str) -> Dict[str, any]:
        """
        Extrai dados específicos de um post do Twitter a partir da legenda capturada.
        
        Args:
            legenda: Texto completo capturado da página
        
        Returns:
            Dicionário com autor, legenda_limpa, curtidas, comentarios, retweets, visualizacoes, data_post
        """
        print(f"🔍 Extraindo dados específicos do Twitter da legenda...")
        
        try:
            # Corta a legenda até encontrar trechos de interface do Twitter
            legenda_limpa = legenda
            if legenda_limpa:
                marcadores_fim = [
                    "Read ",
                    "New to X?",
                    "Sign up now to get your own",
                    "Trending now",
                    "What's happening",
                    "Terms of Service",
                    "Privacy Policy",
                    "Cookie Policy",
                    "© 2025 X Corp.",
                    "© 2024 X Corp.",
                ]
                
                for marcador in marcadores_fim:
                    if marcador in legenda_limpa:
                        legenda_limpa = legenda_limpa.split(marcador)[0].strip()
                        break
            
            # Extrai autor (formato @username - geralmente após o nome completo)
            autor = None
            if legenda_limpa:
                # Procura por @username com \n antes e depois
                match = re.search(r'\n(@[A-Za-z0-9_]+)\n', legenda_limpa)
                if match:
                    autor = match.group(1)
            
            # Extrai o texto do tweet (entre @username e "Translate post" ou data)
            texto_tweet = None
            if autor and legenda_limpa:
                # Procura o texto após o @username até encontrar "Translate post" ou padrão de data
                partes = legenda_limpa.split(autor, 1)
                if len(partes) > 1:
                    texto_completo = partes[1].strip()
                    # Remove "Translate post", "Last edited" e data
                    for separador in ["Translate post", "Last edited", r'\d{1,2}:\d{2}\s*(?:AM|PM)']:
                        if separador.startswith(r'\d'):
                            match_sep = re.search(separador, texto_completo)
                            if match_sep:
                                texto_tweet = texto_completo[:match_sep.start()].strip()
                                break
                        elif separador in texto_completo:
                            texto_tweet = texto_completo.split(separador)[0].strip()
                            break
                    if not texto_tweet:
                        texto_tweet = texto_completo
            
            # Atualiza legenda_limpa com o texto do tweet extraído
            if texto_tweet:
                legenda_limpa = texto_tweet
            
            # Extrai data de publicação (formato: "8:16 AM · Nov 22, 2025")
            data_post = None
            match_data = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM))\s*·\s*(\w+\s+\d{1,2},\s+\d{4})', legenda)
            if match_data:
                data_post = match_data.group(0)
            
            # Extrai visualizações, retweets, curtidas e comentários
            # Padrão: Views \n número1 \n número2 \n número3 \n número4
            visualizacoes = None
            retweets = None
            curtidas = None
            comentarios = None
            
            # Procura por "Views" seguido de números
            match_views = re.search(r'Views\s*\n\s*(\d+(?:[,\.]\d+)*[KM]?)', legenda)
            if match_views:
                visualizacoes_str = match_views.group(1).replace(',', '').replace('.', '')
                # Converte K e M para números
                if 'K' in visualizacoes_str:
                    visualizacoes = float(visualizacoes_str.replace('K', '')) * 1000
                elif 'M' in visualizacoes_str:
                    visualizacoes = float(visualizacoes_str.replace('M', '')) * 1000000
                else:
                    visualizacoes = int(visualizacoes_str)
            
            # Extrai os 4 números após Views (comentários, retweets, curtidas, compartilhamentos)
            match_stats = re.search(r'Views\s*\n\s*\d+[KM]?\s*\n\s*(\d+(?:[,\.]\d+)*)\s*\n\s*(\d+(?:[,\.]\d+)*)\s*\n\s*(\d+(?:[,\.]\d+)*)\s*\n\s*(\d+(?:[,\.]\d+)*)', legenda)
            if match_stats:
                try:
                    comentarios = int(match_stats.group(1).replace(',', '').replace('.', ''))
                    retweets = int(match_stats.group(2).replace(',', '').replace('.', ''))
                    curtidas = int(match_stats.group(3).replace(',', '').replace('.', ''))
                    # grupo 4 seria compartilhamentos/bookmarks
                except:
                    pass
            
            
            dados = {
                "author": autor,
                "text": legenda_limpa,
                "likes": curtidas,
                "comments": comentarios,
                "retweets": retweets,
                "views": visualizacoes,
                "date_post": data_post
            }
            
            print(f"✓ Dados extraídos:")
            print(f"   - Autor: {autor or 'Não encontrado'}")
            print(f"   - Legenda: {legenda_limpa[:50] + '...' if legenda_limpa and len(legenda_limpa) > 50 else legenda_limpa or 'Não encontrada'}")
            print(f"   - Curtidas: {curtidas or 'Não encontrado'}")
            print(f"   - Comentários: {comentarios or 'Não encontrado'}")
            print(f"   - Retweets: {retweets or 'Não encontrado'}")
            print(f"   - Visualizações: {visualizacoes or 'Não encontrado'}")
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
                "comentarios": None,
                "retweets": None,
                "visualizacoes": None,
                "data_post": None
            }
    
    def processar_post(self, url: str, arquivo_saida: str = "post_twitter.json") -> Dict:
        """
        Processa um post completo do Twitter: captura texto e extrai dados.
        
        Args:
            url: URL do post do Twitter
            arquivo_saida: Nome do arquivo JSON de saída (timestamp será adicionado automaticamente)
        
        Returns:
            Dicionário com todos os dados do post
        """
        print(f"\n{'='*60}")
        print(f"🐦 PROCESSANDO POST DO TWITTER")
        print(f"{'='*60}\n")
        
        # Adiciona timestamp ao nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_base, extensao = arquivo_saida.rsplit('.', 1) if '.' in arquivo_saida else (arquivo_saida, 'json')
        arquivo_com_timestamp = f"{nome_base}_{timestamp}.{extensao}"
        
        # 1. Captura o texto completo da página
        texto_completo = self.capturar_texto_rede_social(url)
        
        # 2. Extrai dados específicos do Twitter a partir do texto capturado
        dados_especificos = self.extrair_dados_post(texto_completo)
        
        # 3. Salva tudo em JSON (inclui retweets e visualizações)
        resultado = self.salvar_json(
            texto_capturado=texto_completo,
            url=url,
            legenda=dados_especificos.get("text", ""),
            curtidas=dados_especificos.get("likes"),
            data_post=dados_especificos.get("date_post"),
            autor=dados_especificos.get("author"),
            arquivo=arquivo_com_timestamp,
            comentarios=dados_especificos.get("comments"),
            retweets=dados_especificos.get("retweets"),
            views=dados_especificos.get("views"),
            social_network="twitter"
        )
        
        print(f"\n{'='*60}")
        print(f"✅ PROCESSAMENTO CONCLUÍDO")
        print(f"{'='*60}\n")
        
        return resultado
