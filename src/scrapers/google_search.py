"""Scraper para buscar URLs de redes sociais no Google."""
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import re
import time


class GoogleSearch:
    """Classe para realizar buscas no Google e extrair URLs de redes sociais.
    
    Attributes:
        REDES_SOCIAIS: Dicionário com prefixos de busca para cada rede social
        tempo_espera: Tempo de espera entre requisições (segundos)
        headers: Headers HTTP para as requisições ao Google
    """
    
    REDES_SOCIAIS = {
        "twitter": "site:x.com/",
        "instagram": "site:instagram.com/p/",
        "linkedin": "site:linkedin.com/posts/",
    }
    
    def __init__(self, tempo_espera: int = 2):
        """
        Inicializa o GoogleSearch.
        
        Args:
            tempo_espera: Tempo de espera entre requisições em segundos
        """
        self.tempo_espera = tempo_espera
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        return False
    
    def buscar_urls(
        self,
        palavra_chave: str,
        rede_social: str,
        max_resultados: int = 10
    ) -> List[str]:
        """
        Busca URLs de uma rede social específica no Google.
        
        Args:
            palavra_chave: Palavra-chave para buscar
            rede_social: Nome da rede social ("twitter", "instagram", "linkedin")
            max_resultados: Número máximo de URLs para retornar
        
        Returns:
            Lista de URLs encontradas
        """
        if rede_social.lower() not in self.REDES_SOCIAIS:
            print(f"❌ Rede social '{rede_social}' não suportada. Use: {', '.join(self.REDES_SOCIAIS.keys())}")
            return []
        
        site_filter = self.REDES_SOCIAIS[rede_social.lower()]
        query = f"{site_filter} {palavra_chave}"
        
        print(f"\n🔍 Buscando: '{palavra_chave}' em {rede_social.upper()}")
        
        # Codifica a query para URL
        query_codificada = requests.utils.quote(query)
        url = f"https://www.google.com/search?q={query_codificada}&num={max_resultados * 2}"
        
        urls_encontradas = []
        
        try:
            # Faz requisição ao Google
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            # Parse do HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tenta diferentes seletores para encontrar os links
            # O Google usa várias estruturas diferentes
            links_encontrados = set()
            
            # Método 1: Busca por tags <a> que contenham a URL da rede social
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                
                # Ignora links internos do Google
                if href.startswith('/search') or href.startswith('#'):
                    continue
                
                # Limpa URL do Google
                url_limpa = self._limpar_url_google(href)
                
                # Valida se é da rede social correta
                if url_limpa and self._validar_url(url_limpa, rede_social):
                    if url_limpa not in links_encontrados:
                        links_encontrados.add(url_limpa)
                        urls_encontradas.append(url_limpa)
                        
                        if len(urls_encontradas) >= max_resultados:
                            break
            
            # Método 2: Busca em divs de resultados (estrutura clássica do Google)
            if len(urls_encontradas) < max_resultados:
                for div in soup.find_all('div', class_='g'):
                    a_tag = div.find('a', href=True)
                    if a_tag:
                        href = a_tag['href']
                        url_limpa = self._limpar_url_google(href)
                        
                        if url_limpa and self._validar_url(url_limpa, rede_social):
                            if url_limpa not in links_encontrados:
                                links_encontrados.add(url_limpa)
                                urls_encontradas.append(url_limpa)
                                
                                if len(urls_encontradas) >= max_resultados:
                                    break
            
            print(f"  ✓ {len(urls_encontradas)} URL(s) encontrada(s)")
            return urls_encontradas[:max_resultados]
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Erro ao fazer requisição: {e}")
            return []
        except Exception as e:
            print(f"✗ Erro ao extrair URLs: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def buscar_todas_redes(
        self,
        palavra_chave: str,
        max_resultados_por_rede: int = 10
    ) -> Dict[str, List[str]]:
        """
        Busca URLs de todas as redes sociais suportadas.
        
        Args:
            palavra_chave: Palavra-chave para buscar
            max_resultados_por_rede: Número máximo de URLs por rede social
        
        Returns:
            Dicionário com rede_social: [lista de URLs]
        """
        print(f"\n{'='*60}")
        print(f"🔍 BUSCANDO '{palavra_chave}' EM TODAS AS REDES SOCIAIS")
        print(f"{'='*60}")
        
        resultados = {}
        
        for rede in self.REDES_SOCIAIS.keys():
            print(f"\n--- {rede.upper()} ---")
            urls = self.buscar_urls(palavra_chave, rede, max_resultados_por_rede)
            resultados[rede] = urls
            
            # Pausa entre buscas para evitar bloqueio do Google
            if rede != list(self.REDES_SOCIAIS.keys())[-1]:  # Não espera no último
                print(f"⏳ Aguardando {self.tempo_espera}s antes da próxima busca...")
                time.sleep(self.tempo_espera)
        
        print(f"\n{'='*60}")
        print(f"✅ BUSCA CONCLUÍDA")
        print(f"{'='*60}")
        
        # Resumo
        for rede, urls in resultados.items():
            print(f"  {rede.capitalize()}: {len(urls)} URL(s)")
        
        return resultados
    
    def _validar_url(self, url: str, rede_social: str) -> bool:
        """
        Valida se a URL pertence à rede social especificada.
        
        Args:
            url: URL para validar
            rede_social: Nome da rede social
        
        Returns:
            True se a URL é válida para a rede social
        """
        patterns = {
            "twitter": r'x\.com/[^/]+/status/\d+',
            "instagram": r'instagram\.com/p/[A-Za-z0-9_-]+',
            "linkedin": r'linkedin\.com/posts/[^/]+',
        }
        
        pattern = patterns.get(rede_social.lower())
        if pattern:
            return bool(re.search(pattern, url))
        return False
    
    def _limpar_url_google(self, url: str) -> str:
        """
        Remove parâmetros de redirecionamento do Google da URL.
        
        Args:
            url: URL com possíveis parâmetros do Google
        
        Returns:
            URL limpa
        """
        # Remove /url?q= do Google
        if '/url?q=' in url:
            match = re.search(r'/url\?q=([^&]+)', url)
            if match:
                url = match.group(1)
        
        # Se começar com http, provavelmente já é a URL final
        if url.startswith('http'):
            # Remove parâmetros de tracking (tudo após &)
            if '&' in url:
                url = url.split('&')[0]
            
            # Decodifica URL
            try:
                from urllib.parse import unquote
                url = unquote(url)
            except:
                pass
            
            return url
        
        return None


