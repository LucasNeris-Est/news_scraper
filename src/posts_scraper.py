"""Classe base para scrapers de posts de redes sociais."""
from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright, Browser, Page
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from datetime import datetime
import json


class PostsScraper(ABC):
    """Classe base abstrata para scrapers de posts de redes sociais."""
    
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
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
    
    @abstractmethod
    def buscar_posts(self, palavras_chave: str, limite: int = 5) -> List[str]:
        """
        Busca posts baseado em palavras-chave.
        
        Args:
            palavras_chave: Termos de busca
            limite: Número máximo de posts a retornar
        
        Returns:
            Lista de URLs dos posts encontrados
        """
        pass
    
    @abstractmethod
    def extrair_conteudo(self, url: str) -> Dict[str, str]:
        """
        Extrai o conteúdo completo de um post.
        
        Args:
            url: URL do post
        
        Returns:
            Dicionário com os dados do post (autor, conteudo, data, link, curtidas, compartilhamentos, etc.)
        """
        pass
    
    def buscar_e_extrair(self, palavras_chave: str, limite: int = 5) -> List[Dict[str, str]]:
        """
        Busca e extrai o conteúdo de múltiplos posts.
        
        Args:
            palavras_chave: Termos de busca
            limite: Número máximo de posts
        
        Returns:
            Lista de dicionários com os posts extraídos
        """
        if not self.browser:
            raise RuntimeError("Scraper deve ser usado como context manager")
        
        links = self.buscar_posts(palavras_chave, limite)
        
        if not links:
            return []
        
        posts = []
        for i, link in enumerate(links, 1):
            print(f"Processando post {i}/{len(links)}: {link}")
            post = self.extrair_conteudo(link, palavras_chave)
            posts.append(post)
        
        return posts
    
    def salvar_json(self, posts: List[Dict[str, str]], arquivo: str = "posts.json"):
        """
        Salva os posts em um arquivo JSON.
        
        Args:
            posts: Lista de dicionários com os posts
            arquivo: Nome do arquivo de saída
        """
        dados = {
            "total_posts": len(posts),
            "data_extracao": datetime.now().isoformat(),
            "posts": posts
        }
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        print(f"\n{len(posts)} posts salvos em {arquivo}")


def _extrair_texto_seguro(elemento, default=""):
    """Extrai texto de forma segura de um elemento BeautifulSoup."""
    return elemento.get_text(strip=True) if elemento else default
