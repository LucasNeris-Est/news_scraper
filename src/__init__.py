"""Módulo principal do scraper de notícias."""
from .news_scraper import NewsScraper
from .scrapers.g1_scraper import G1Scraper

__all__ = ['NewsScraper', 'G1Scraper']

