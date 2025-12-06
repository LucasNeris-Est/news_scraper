"""Scraper específico para o Instagram."""
from bs4 import BeautifulSoup
from typing import Dict
from datetime import datetime
import time
from ..posts_scraper import PostsScraper


class InstagramScraper(PostsScraper):
    """Scraper para posts do Instagram."""
    
    BASE_URL = "https://www.instagram.com"
    
    def extrair_dados_post(self, url: str) -> Dict[str, any]:
        """
        Extrai dados específicos de um post do Instagram.
        
        Args:
            url: URL do post do Instagram
        
        Returns:
            Dicionário com autor, legenda, curtidas, data_post
        """
        if not self.browser:
            raise RuntimeError("Scraper deve ser usado como context manager (use 'with')")
        
        print(f"🔍 Extraindo dados específicos do Instagram...")
        
        page = self.browser.new_page(
            viewport={'width': self.viewport_width, 'height': self.viewport_height}
        )
        
        try:
            # Navega para a URL
            page.goto(url, wait_until="networkidle", timeout=self.timeout_navegacao)
            
            # Fecha popups
            self.close_popups(page, tempo_espera=1)
            
            # Aguarda carregamento
            time.sleep(self.tempo_carregamento)
            
            # Captura HTML
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extrai legenda/conteúdo do post primeiro
            legenda = ""
            # Tenta diferentes seletores para a legenda
            conteudo_tags = soup.find_all('span', class_=lambda x: x and ('_ap3a' in str(x) or 'x1lliihq' in str(x)))
            if conteudo_tags:
                legenda = "\n".join([tag.get_text(strip=True) for tag in conteudo_tags if tag.get_text(strip=True)])
            
            # Se não encontrou, tenta h1
            if not legenda:
                h1_tag = soup.find('h1')
                if h1_tag:
                    legenda = h1_tag.get_text(strip=True)
            
            # Corta a legenda até encontrar o trecho de login/footer
            if legenda:
                marcadores_fim = [
                    "Log into like or comment.",
                    "Log in to like or comment.",
                    "See more posts",
                    "Meta\nAbout",
                ]
                
                for marcador in marcadores_fim:
                    if marcador in legenda:
                        legenda = legenda.split(marcador)[0].strip()
                        break
            
            # Extrai autor (username) da primeira linha da legenda
            autor = None
            if legenda:
                # O autor geralmente é a primeira linha da legenda
                linhas = legenda.split('\n')
                for linha in linhas[:3]:  # Verifica as 3 primeiras linhas
                    linha_limpa = linha.strip()
                    # Verifica se parece com um username (sem espaços, não muito longo)
                    if linha_limpa and ' ' not in linha_limpa and len(linha_limpa) < 50 and not linha_limpa.startswith('#'):
                        # Remove "Verified" se existir
                        autor = linha_limpa.replace('Verified', '').strip()
                        break
            
            # Se não encontrou na legenda, tenta pelos seletores HTML
            if not autor:
                autor_tags = soup.find_all('a', class_=lambda x: x and 'x1i10hfl' in str(x))
                for tag in autor_tags:
                    texto = tag.get_text(strip=True)
                    if texto and len(texto) > 0 and not texto.startswith('http'):
                        autor = texto
                        break
            
            # Extrai curtidas da legenda primeiro
            curtidas = None
            import re
            
            if legenda:
                # Procura por padrões de curtidas na legenda
                curtidas_patterns = [
                    r'(\d+(?:[,\.]\d+)*)\s*likes',
                    r'(\d+(?:[,\.]\d+)*)\s*curtidas',
                    r'(\d+(?:[,\.]\d+)*)\s*gostaram',
                    r'(\d+(?:[,\.]\d+)*)\s*like',
                ]
                
                for pattern in curtidas_patterns:
                    match = re.search(pattern, legenda.lower())
                    if match:
                        try:
                            numero_str = match.group(1).replace(',', '').replace('.', '')
                            curtidas = int(numero_str)
                            break
                        except:
                            curtidas = match.group(1)
                            break
            
            # Se não encontrou na legenda, tenta pelos seletores HTML
            if curtidas is None:
                curtidas_patterns_html = ['likes', 'curtidas', 'gostaram']
                for pattern in curtidas_patterns_html:
                    curtidas_tag = soup.find('span', string=lambda x: x and pattern in str(x).lower())
                    if curtidas_tag:
                        texto = curtidas_tag.get_text(strip=True)
                        # Tenta extrair números
                        numeros = re.findall(r'[\d,\.]+', texto)
                        if numeros:
                            try:
                                curtidas = int(numeros[0].replace(',', '').replace('.', ''))
                            except:
                                curtidas = texto
                        break
            
            # Extrai data de publicação
            data_post = None
            data_tag = soup.find('time', attrs={'datetime': True})
            if data_tag:
                data_post = data_tag.get('datetime')
            
            dados = {
                "autor": autor,
                "legenda": legenda,
                "curtidas": curtidas,
                "data_post": data_post
            }
            
            print(f"✓ Dados extraídos:")
            print(f"   - Autor: {autor or 'Não encontrado'}")
            print(f"   - Legenda: {legenda[:50] + '...' if legenda and len(legenda) > 50 else legenda or 'Não encontrada'}")
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
        finally:
            page.close()
    
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
        
        # 2. Extrai dados específicos do Instagram
        dados_especificos = self.extrair_dados_post(url)
        
        # 3. Salva tudo em JSON
        resultado = self.salvar_json(
            texto_capturado=texto_completo,
            url=url,
            legenda=dados_especificos.get("legenda", ""),
            curtidas=dados_especificos.get("curtidas"),
            data_post=dados_especificos.get("data_post"),
            autor=dados_especificos.get("autor"),
            arquivo=arquivo_com_timestamp
        )
        
        print(f"\n{'='*60}")
        print(f"✅ PROCESSAMENTO CONCLUÍDO")
        print(f"{'='*60}\n")
        
        return resultado
