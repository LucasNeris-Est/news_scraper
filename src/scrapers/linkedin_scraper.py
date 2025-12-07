"""Scraper específico para o LinkedIn."""
from bs4 import BeautifulSoup
from typing import Dict
from datetime import datetime
import time
import re
from ..posts_scraper import PostsScraper


class LinkedInScraper(PostsScraper):
    """Scraper para posts do LinkedIn."""
    
    BASE_URL = "https://www.linkedin.com"
    
    def extrair_dados_post(self, legenda: str) -> Dict[str, any]:
        """
        Extrai dados específicos de um post do LinkedIn a partir da legenda capturada.
        
        Args:
            legenda: Texto completo capturado da página
        
        Returns:
            Dicionário com autor, legenda_limpa, curtidas, data_post
        """
        print(f"🔍 Extraindo dados específicos do LinkedIn da legenda...")
        
        try:
            # Corta a legenda até encontrar trechos de interface do LinkedIn
            legenda_limpa = legenda
            if legenda_limpa:
                marcadores_fim = [
                    "Sign in to view more content",
                    "Join now",
                    "Sign in",
                    "Create your free account",
                    "Agree & Join",
                    "© 2025 LinkedIn",
                    "© 2024 LinkedIn",
                    "LinkedIn and third parties",
                ]
                
                for marcador in marcadores_fim:
                    if marcador in legenda_limpa:
                        legenda_limpa = legenda_limpa.split(marcador)[0].strip()
                        break
            
            # Extrai autor da primeira linha da legenda
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
            
            # Extrai curtidas/likes da legenda
            curtidas = None
            if legenda_limpa:
                # Procura por padrões de curtidas/likes (formato: "110\n13 Comments\nLike")
                curtidas_patterns = [
                    r'\n(\d+(?:[,\.]\d+)*)\n\d+\s*Comments?\s*\nLike',  # Padrão LinkedIn: número antes de "X Comments\nLike"
                    r'(\d+(?:[,\.]\d+)*)\s*reactions?',
                    r'(\d+(?:[,\.]\d+)*)\s*likes?',
                    r'(\d+(?:[,\.]\d+)*)\s*reações',
                    r'(\d+(?:[,\.]\d+)*)\s*curtidas?',
                ]
                
                for pattern in curtidas_patterns:
                    match = re.search(pattern, legenda_limpa, re.IGNORECASE)
                    if match:
                        try:
                            numero_str = match.group(1).replace(',', '').replace('.', '')
                            curtidas = int(numero_str)
                            break
                        except:
                            curtidas = match.group(1)
                            break
            
            # Extrai comentários da legenda
            comentarios = None
            if legenda_limpa:
                # Procura por padrões de comentários (formato: "13 Comments")
                comentarios_patterns = [
                    r'(\d+(?:[,\.]\d+)*)\s*Comments?',
                    r'(\d+(?:[,\.]\d+)*)\s*Comentários?',
                    r'(\d+(?:[,\.]\d+)*)\s*Comment',
                ]
                
                for pattern in comentarios_patterns:
                    match = re.search(pattern, legenda_limpa, re.IGNORECASE)
                    if match:
                        try:
                            numero_str = match.group(1).replace(',', '').replace('.', '')
                            comentarios = int(numero_str)
                            break
                        except:
                            comentarios = match.group(1)
                            break
            
            # Extrai data de publicação (formato relativo: 2d, 1w, 3h, etc)
            data_post = None
            if legenda_limpa:
                # Procura por padrões de tempo relativo
                data_patterns = [
                    r'(\d+[hdwmy])',  # 2d, 1w, 3h, 4m, 1y
                    r'(\d+\s*(?:hour|day|week|month|year)s?\s*ago)',
                    r'(\d+\s*(?:hora|dia|semana|mês|ano)s?\s*atrás)',
                ]
                
                for pattern in data_patterns:
                    match = re.search(pattern, legenda_limpa.lower())
                    if match:
                        data_post = match.group(1)
                        break
            
            dados = {
                "autor": autor,
                "legenda": legenda_limpa,
                "curtidas": curtidas,
                "comentarios": comentarios,
                "data_post": data_post
            }
            
            print(f"✓ Dados extraídos:")
            print(f"   - Autor: {autor or 'Não encontrado'}")
            print(f"   - Legenda: {legenda_limpa[:50] + '...' if legenda_limpa and len(legenda_limpa) > 50 else legenda_limpa or 'Não encontrada'}")
            print(f"   - Curtidas: {curtidas or 'Não encontrado'}")
            print(f"   - Comentários: {comentarios or 'Não encontrado'}")
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
                "data_post": None
            }
    
    def processar_post(self, url: str, arquivo_saida: str = "post_linkedin.json") -> Dict:
        """
        Processa um post completo do LinkedIn: captura texto e extrai dados.
        
        Args:
            url: URL do post do LinkedIn
            arquivo_saida: Nome do arquivo JSON de saída (timestamp será adicionado automaticamente)
        
        Returns:
            Dicionário com todos os dados do post
        """
        print(f"\n{'='*60}")
        print(f"💼 PROCESSANDO POST DO LINKEDIN")
        print(f"{'='*60}\n")
        
        # Adiciona timestamp ao nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_base, extensao = arquivo_saida.rsplit('.', 1) if '.' in arquivo_saida else (arquivo_saida, 'json')
        arquivo_com_timestamp = f"{nome_base}_{timestamp}.{extensao}"
        
        # 1. Captura o texto completo da página
        texto_completo = self.capturar_texto_rede_social(url)
        
        # 2. Extrai dados específicos do LinkedIn a partir do texto capturado
        dados_especificos = self.extrair_dados_post(texto_completo)
        
        # 3. Salva tudo em JSON (inclui comentarios nos dados adicionais)
        resultado = self.salvar_json(
            texto_capturado=texto_completo,
            url=url,
            legenda=dados_especificos.get("legenda", ""),
            curtidas=dados_especificos.get("curtidas"),
            data_post=dados_especificos.get("data_post"),
            autor=dados_especificos.get("autor"),
            arquivo=arquivo_com_timestamp,
            comentarios=dados_especificos.get("comentarios")
        )
        
        print(f"\n{'='*60}")
        print(f"✅ PROCESSAMENTO CONCLUÍDO")
        print(f"{'='*60}\n")
        
        return resultado
