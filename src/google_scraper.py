"""Classe base para integração entre GoogleSearch e scrapers de redes sociais."""
from typing import List, Dict
from src.scrapers.google_search import GoogleSearch
from src.scrapers.instagram_scraper import InstagramScraper
from src.scrapers.linkedin_scraper import LinkedInScraper
from src.scrapers.twitter_scraper import TwitterScraper
import json
import os
from datetime import datetime


class GoogleScraper(GoogleSearch):
    """Pipeline completo: busca URLs no Google e extrai dados dos posts."""
    
    def __init__(
        self,
        headless: bool = True,
        tempo_espera_busca: int = 2,
        pasta_saida: str = "posts_extraidos"
    ):
        """
        Inicializa o pipeline completo.
        
        Args:
            headless: Se True, executa scrapers em modo headless
            tempo_espera_busca: Tempo de espera entre buscas no Google
            pasta_saida: Pasta onde os posts serão salvos
        """
        self.headless = headless
        self.tempo_espera_busca = tempo_espera_busca
        self.pasta_saida = pasta_saida
        
        # Cria pasta de saída se não existir
        os.makedirs(pasta_saida, exist_ok=True)
    
    def processar_palavra_chave(
        self,
        palavra_chave: str,
        redes_sociais: List[str] = ["instagram", "twitter", "linkedin"],
        max_urls_por_rede: int = 5,
        arquivo_resumo: str = None
    ) -> Dict[str, Dict]:
        """
        Busca URLs no Google e extrai dados de posts para uma palavra-chave.
        
        Args:
            palavra_chave: Palavra-chave para buscar
            redes_sociais: Lista de redes sociais para buscar
            max_urls_por_rede: Número máximo de URLs por rede social
            arquivo_resumo: Nome do arquivo JSON com resumo (opcional)
        
        Returns:
            Dicionário com resumo de todos os posts extraídos
        """
        print(f"\n{'='*70}")
        print(f"🚀 PIPELINE: PROCESSANDO '{palavra_chave}'")
        print(f"{'='*70}\n")
        
        resumo_geral = {
            "palavra_chave": palavra_chave,
            "data_execucao": datetime.now().isoformat(),
            "redes_sociais": {}
        }
        
        # 1. Busca URLs no Google
        print("📍 ETAPA 1: Buscando URLs no Google...")
        with GoogleSearch(tempo_espera=self.tempo_espera_busca) as searcher:
            urls_por_rede = {}
            for rede in redes_sociais:
                urls = searcher.buscar_urls(palavra_chave, rede, max_urls_por_rede)
                urls_por_rede[rede] = urls
        
        # 2. Extrai dados de cada rede social
        print(f"\n📍 ETAPA 2: Extraindo dados dos posts...")
        
        for rede, urls in urls_por_rede.items():
            if not urls:
                print(f"\n⚠️ Nenhuma URL encontrada para {rede.upper()}")
                resumo_geral["redes_sociais"][rede] = {
                    "urls_encontradas": 0,
                    "posts_extraidos": 0,
                    "posts": []
                }
                continue
            
            print(f"\n{'─'*70}")
            print(f"📱 Processando {rede.upper()}: {len(urls)} URL(s)")
            print(f"{'─'*70}")
            
            posts_extraidos = self._processar_rede(rede, urls, palavra_chave)
            
            resumo_geral["redes_sociais"][rede] = {
                "urls_encontradas": len(urls),
                "posts_extraidos": len(posts_extraidos),
                "posts": posts_extraidos
            }
        
        # 3. Salva resumo geral
        if arquivo_resumo:
            self._salvar_resumo(resumo_geral, arquivo_resumo)
        
        # 4. Exibe estatísticas finais
        self._exibir_estatisticas(resumo_geral)
        
        print(f"\n{'='*70}")
        print(f"✅ PIPELINE CONCLUÍDO")
        print(f"{'='*70}\n")
        
        return resumo_geral
    
    def _processar_rede(
        self,
        rede: str,
        urls: List[str],
        palavra_chave: str
    ) -> List[Dict]:
        """
        Processa URLs de uma rede social específica.
        
        Args:
            rede: Nome da rede social
            urls: Lista de URLs para processar
            palavra_chave: Palavra-chave original da busca
        
        Returns:
            Lista de dicionários com dados dos posts
        """
        posts_extraidos = []
        
        # Seleciona o scraper apropriado
        scraper_class = {
            "instagram": InstagramScraper,
            "linkedin": LinkedInScraper,
            "twitter": TwitterScraper
        }.get(rede.lower())
        
        if not scraper_class:
            print(f"❌ Scraper não implementado para {rede}")
            return []
        
        # Processa cada URL
        with scraper_class(headless=self.headless) as scraper:
            for i, url in enumerate(urls, 1):
                print(f"\n  [{i}/{len(urls)}] Processando: {url}")
                
                try:
                    # Nome do arquivo baseado na palavra-chave e timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    arquivo = f"{palavra_chave.replace(' ', '_')}_{rede}_{i}_{timestamp}.json"
                    
                    # Extrai dados do post
                    resultado = scraper.processar_post(url, arquivo)
                    
                    if resultado:
                        posts_extraidos.append({
                            "url": url,
                            "arquivo": arquivo,
                            "autor": resultado.get("autor"),
                            "curtidas": resultado.get("curtidas"),
                            "comentarios": resultado.get("comentarios"),
                            "data_post": resultado.get("data_post")
                        })
                        print(f"  ✅ Post extraído com sucesso")
                    else:
                        print(f"  ⚠️ Falha ao extrair post")
                        
                except Exception as e:
                    print(f"  ❌ Erro ao processar URL: {e}")
                    continue
        
        return posts_extraidos
    
    def _salvar_resumo(self, resumo: Dict, arquivo: str):
        """Salva resumo geral em arquivo JSON."""
        try:
            caminho = os.path.join(self.pasta_saida, arquivo)
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(resumo, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Resumo salvo em: {os.path.abspath(caminho)}")
        except Exception as e:
            print(f"\n❌ Erro ao salvar resumo: {e}")
    
    def _exibir_estatisticas(self, resumo: Dict):
        """Exibe estatísticas do processamento."""
        print(f"\n{'='*70}")
        print(f"📊 ESTATÍSTICAS FINAIS")
        print(f"{'='*70}")
        
        total_urls = 0
        total_posts = 0
        
        for rede, dados in resumo["redes_sociais"].items():
            urls_count = dados["urls_encontradas"]
            posts_count = dados["posts_extraidos"]
            total_urls += urls_count
            total_posts += posts_count
            
            taxa_sucesso = (posts_count / urls_count * 100) if urls_count > 0 else 0
            
            print(f"\n{rede.upper()}:")
            print(f"  URLs encontradas: {urls_count}")
            print(f"  Posts extraídos: {posts_count}")
            print(f"  Taxa de sucesso: {taxa_sucesso:.1f}%")
        
        print(f"\n{'─'*70}")
        print(f"TOTAL:")
        print(f"  URLs processadas: {total_urls}")
        print(f"  Posts extraídos: {total_posts}")
        if total_urls > 0:
            print(f"  Taxa geral: {(total_posts/total_urls*100):.1f}%")
