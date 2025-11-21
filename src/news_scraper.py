"""Classe base para scrapers de notícias."""
from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright, Browser, Page
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import json


class NewsScraper(ABC):
    """Classe base abstrata para scrapers de notícias."""
    
    def __init__(self, headless: bool = True):
        """
        Inicializa o scraper.
        
        Args:
            headless: Se True, executa o navegador em modo headless
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
    
    def __enter__(self):
        """Context manager entry."""
        playwright = sync_playwright().start()
        self.browser = playwright.chromium.launch(headless=self.headless)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.browser:
            self.browser.close()
    
    @abstractmethod
    def buscar_links(self, palavras_chave: str, limite: int = 5) -> List[str]:
        """
        Busca links de notícias baseado em palavras-chave.
        
        Args:
            palavras_chave: Termos de busca
            limite: Número máximo de links a retornar
        
        Returns:
            Lista de URLs das notícias encontradas
        """
        pass
    
    @abstractmethod
    def extrair_conteudo(self, url: str) -> Dict[str, str]:
        """
        Extrai o conteúdo completo de uma notícia.
        
        Args:
            url: URL da notícia
        
        Returns:
            Dicionário com os dados da notícia (titulo, conteudo, autor, data, link, etc.)
        """
        pass
    
    def buscar_e_extrair(self, palavras_chave: str, limite: int = 5) -> List[Dict[str, str]]:
        """
        Busca e extrai o conteúdo de múltiplas notícias.
        
        Args:
            palavras_chave: Termos de busca
            limite: Número máximo de notícias
        
        Returns:
            Lista de dicionários com as notícias extraídas
        """
        if not self.browser:
            raise RuntimeError("Scraper deve ser usado como context manager")
        
        links = self.buscar_links(palavras_chave, limite)
        
        if not links:
            return []
        
        noticias = []
        for i, link in enumerate(links, 1):
            print(f"Processando notícia {i}/{len(links)}: {link}")
            noticia = self.extrair_conteudo(link)
            noticias.append(noticia)
        
        return noticias
    
    def salvar_json(self, noticias: List[Dict[str, str]], arquivo: str = "noticias.json"):
        """
        Salva as notícias em um arquivo JSON.
        
        Args:
            noticias: Lista de dicionários com as notícias
            arquivo: Nome do arquivo de saída
        """
        dados = {
            "total_noticias": len(noticias),
            "data_extracao": datetime.now().isoformat(),
            "noticias": noticias
        }
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        print(f"\n{len(noticias)} notícias salvas em {arquivo}")


def _extrair_texto_seguro(elemento, default=""):
    """Extrai texto de forma segura de um elemento BeautifulSoup."""
    return elemento.get_text(strip=True) if elemento else default
