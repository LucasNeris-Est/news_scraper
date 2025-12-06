"""Scraper específico para o site G1."""
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from typing import List, Dict
from datetime import datetime
from ..news_scraper import NewsScraper, _extrair_texto_seguro


class G1Scraper(NewsScraper):
    """Scraper para notícias do G1."""
    
    BASE_URL = "https://g1.globo.com"
    
    def buscar_links(self, palavras_chave: str, limite: int = 5) -> List[str]:
        """Busca links de notícias do G1."""
        palavras_codificadas = quote_plus(palavras_chave)
        url = f"{self.BASE_URL}/busca/?q={palavras_codificadas}&from=now-1d"
        
        if not self.browser:
            raise RuntimeError("Scraper deve ser usado como context manager")
        
        page = self.browser.new_page()
        
        try:
            page.goto(url, wait_until="load", timeout=30000)
            page.wait_for_selector("li.widget--card", timeout=15000)
            page.wait_for_timeout(2000)
            html_completo = page.content()
        except Exception as e:
            print(f"Erro ao carregar página: {e}")
            return []
        finally:
            page.close()
        
        soup = BeautifulSoup(html_completo, 'html.parser')
        
        # Busca cards de notícia excluindo vídeos
        cards = soup.find_all('li', class_=lambda x: x and 'widget--card' in x and 'widget--info' in x and 'video' not in x)
        
        links = []
        for card in cards[:limite]:
            text_container = card.find('div', class_='widget--info__text-container')
            if text_container:
                link_tag = text_container.find('a', href=True)
                if link_tag and (href := link_tag.get('href')):
                    links.append(href)
        
        return links
    
    def extrair_conteudo(self, url: str, palavras_chave: str) -> Dict[str, str]:
        """Extrai o conteúdo completo de uma notícia do G1."""
        if not self.browser:
            raise RuntimeError("Scraper deve ser usado como context manager")
        
        page = self.browser.new_page()
        
        try:
            page.goto(url, wait_until="load", timeout=30000)
            page.wait_for_selector("h1.content-head__title", timeout=15000)
            page.wait_for_timeout(2000)
            html = page.content()
        except Exception as e:
            print(f"Erro ao carregar notícia {url}: {e}")
            return {
                "titulo": "",
                "subtitulo": "",
                "palavras_chave": palavras_chave,
                "autor": None,
                "data": None,
                "link": url,
                "conteudo": "",
                "erro": str(e),
                "data_extracao": datetime.now().isoformat()
            }
        finally:
            page.close()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        
        # Importa função de sanitização
        from ..text_processing import sanitize_text
        
        # Extrai título
        titulo_tag = soup.find('h1', class_='content-head__title')
        titulo = _extrair_texto_seguro(titulo_tag, "Sem título")
        titulo = sanitize_text(titulo) if titulo else "Sem título"
        
        # Extrai subtítulo
        subtitulo_tag = soup.find('h2', class_='content-head__subtitle')
        subtitulo = _extrair_texto_seguro(subtitulo_tag) or None
        subtitulo = sanitize_text(subtitulo) if subtitulo else None
        
        # Extrai autor
        autor_tag = soup.find(class_='content-publication-data__from')
        autor = _extrair_texto_seguro(autor_tag) or None
        autor = sanitize_text(autor) if autor else None
        
        # Extrai data
        data_tag = soup.find('time', itemprop='datePublished')
        data = data_tag.get('datetime') if data_tag and data_tag.get('datetime') else None
        
        # Extrai conteúdo do corpo da notícia
        article_body = soup.find(class_='mc-article-body')
        conteudo = ""
        
        if article_body:
            paragrafos = article_body.find_all('p', class_='content-text__container')
            textos = []
            for p in paragrafos:
                texto = _extrair_texto_seguro(p)
                # Filtra parágrafos vazios e remove "LEIA TAMBÉM"
                if texto and "LEIA TAMBÉM" not in texto:
                    # Aplica sanitização em cada parágrafo
                    texto_limpo = sanitize_text(texto)
                    if texto_limpo:
                        textos.append(texto_limpo)
            conteudo = "\n\n".join(textos)
            # Aplica sanitização final no conteúdo completo
            conteudo = sanitize_text(conteudo)
        
        # Extrai link canônico se disponível
        link_canonical = soup.find('link', attrs={'itemprop': 'mainEntityOfPage'})
        link_final = link_canonical.get('href') if link_canonical and link_canonical.get('href') else url
        
        return {
            "titulo": titulo,
            "subtitulo": subtitulo,
            "autor": autor,
            "data": data,
            "palavras_chave": palavras_chave,
            "link": link_final,
            "conteudo": conteudo,
            "data_extracao": datetime.now().isoformat()
        }

