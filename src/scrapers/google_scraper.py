"""Scraper avançado usando Google Custom Search API."""
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from datetime import datetime
import os


class GoogleScraper:
    """Classe para buscas avançadas usando Google Custom Search API.
    
    Attributes:
        REDES_SOCIAIS: Dicionário com domínios para cada rede social
        api_key: Chave da API do Google
        cx: ID do Custom Search Engine
    """
    
    REDES_SOCIAIS = {
        "instagram": "instagram.com/p",
        "twitter": "x.com/*/status",
        "linkedin": "linkedin.com/posts"
    }
    
    def __init__(self, api_key: str = None, cx: str = None):
        """
        Inicializa o GoogleScraper.
        
        Args:
            api_key: Google API Key (ou usa variável de ambiente GOOGLE_API_KEY)
            cx: Custom Search Engine ID (ou usa variável de ambiente GOOGLE_CX)
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.cx = cx or os.getenv('GOOGLE_CX')
        
        if not self.api_key or not self.cx:
            raise ValueError(
                "API Key e CX são obrigatórios. "
                "Forneça via parâmetros ou variáveis de ambiente GOOGLE_API_KEY e GOOGLE_CX"
            )
        
        self.service = build("customsearch", "v1", developerKey=self.api_key)
    
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
        max_resultados: int = 10,
        data_inicio: str = None,
        data_fim: str = None,
        ordenar_por_data: bool = False,
        dias_anteriores: int = None
    ) -> List[Dict]:
        """
        Busca URLs de uma rede social específica usando Google Custom Search API.
        Retorna metadados completos (título, link, snippet, data, description).
        
        Args:
            palavra_chave: Palavra-chave para buscar (usa correspondência exata)
            rede_social: Nome da rede social ("twitter", "instagram", "linkedin")
            max_resultados: Número máximo de URLs para retornar (máx: 10 por requisição)
            data_inicio: Data de início no formato YYYY-MM-DD (ex: "2025-01-01")
            data_fim: Data de fim no formato YYYY-MM-DD
            ordenar_por_data: Se True, ordena resultados por data (mais recentes primeiro)
            dias_anteriores: Restringe busca aos últimos N dias (ex: 7 para última semana)
        
        Returns:
            Lista de dicionários com metadados completos
        """
        if rede_social.lower() not in self.REDES_SOCIAIS:
            print(f"❌ Rede social '{rede_social}' não suportada. Use: {', '.join(self.REDES_SOCIAIS.keys())}")
            return []
        
        # Constrói a query
        site = self.REDES_SOCIAIS[rede_social.lower()]
        query = f'site:{site} "{palavra_chave}"'
        
        # Adiciona filtro de data se especificado
        if data_inicio:
            query = f'after:{data_inicio} {query}'
        if data_fim:
            query = f'before:{data_fim} {query}'
        
        print(f"\n🔍 Buscando: '{palavra_chave}' em {rede_social.upper()}")
        print(f"📝 Query: {query}")
        
        try:
            # Parâmetros da busca
            params = {
                'q': query,
                'cx': self.cx,
                'num': min(max_resultados, 10),  # API limita a 10 por requisição
                'lr': 'lang_pt'  # Filtro de idioma português
            }
            
            # Adiciona ordenação por data se solicitado
            if ordenar_por_data:
                params['sort'] = 'date'
            
            # Adiciona restrição de dias se especificado
            if dias_anteriores:
                params['dateRestrict'] = f'd{dias_anteriores}'
            
            # Executa a busca
            resultado = self.service.cse().list(**params).execute()
            
            # Extrai URLs e metadados dos resultados
            resultados_completos = []
            items = resultado.get('items', [])
            
            print(f"\n📋 Encontrados {len(items)} resultado(s):\n")
            
            for i, item in enumerate(items, 1):
                url = item.get('link')
                if url:
                    # Extrai todos os metadados
                    metadados = {
                        'url': url,
                        'titulo': item.get('title'),
                        'snippet': item.get('snippet'),
                        'description': item.get('htmlSnippet'),
                        'data': None
                    }
                    
                    # Tenta extrair data de diferentes campos
                    pagemap = item.get('pagemap', {})
                    
                    # Tenta obter data de metatags
                    if 'metatags' in pagemap and pagemap['metatags']:
                        metatag = pagemap['metatags'][0]
                        metadados['data'] = (metatag.get('article:published_time') or 
                                           metatag.get('datePublished') or 
                                           metatag.get('date'))
                    
                    resultados_completos.append(metadados)
                    
                    # Exibe formatado
                    print(f"[{i}] Título: {metadados['titulo']}")
                    print(f"    Link: {metadados['url']}")
                    print(f"    Snippet: {metadados['snippet'][:150] if metadados['snippet'] else 'N/A'}...")
                    if metadados['data']:
                        print(f"    Data: {metadados['data']}")
                    print()
            
            print(f"✓ {len(resultados_completos)} resultado(s) extraído(s)\n")
            
            return resultados_completos
            
        except Exception as e:
            print(f"❌ Erro ao buscar: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def buscar_com_detalhes(
        self,
        palavra_chave: str,
        rede_social: str,
        max_resultados: int = 10,
        data_inicio: str = None,
        ordenar_por_data: bool = False,
        dias_anteriores: int = None
    ) -> List[Dict]:
        """
        Busca URLs com metadados completos (título, snippet, data).
        
        Args:
            palavra_chave: Palavra-chave para buscar
            rede_social: Nome da rede social
            max_resultados: Número máximo de resultados
            data_inicio: Data de início (YYYY-MM-DD)
            ordenar_por_data: Se True, ordena por data
            dias_anteriores: Restringe aos últimos N dias
        
        Returns:
            Lista de dicionários com: url, titulo, snippet, data_publicacao
        """
        if rede_social.lower() not in self.REDES_SOCIAIS:
            print(f"❌ Rede social '{rede_social}' não suportada.")
            return []
        
        # Constrói a query
        site = self.REDES_SOCIAIS[rede_social.lower()]
        query = f'site:{site} "{palavra_chave}"'
        
        if data_inicio:
            query = f'after:{data_inicio} {query}'
        
        print(f"\n🔍 Buscando detalhes: '{palavra_chave}' em {rede_social.upper()}")
        
        try:
            # Parâmetros da busca
            params = {
                'q': query,
                'cx': self.cx,
                'num': min(max_resultados, 10),
                'lr': 'lang_pt'
            }
            
            if ordenar_por_data:
                params['sort'] = 'date'
            
            if dias_anteriores:
                params['dateRestrict'] = f'd{dias_anteriores}'
            
            # Executa a busca
            resultado = self.service.cse().list(**params).execute()
            
            # Extrai dados completos
            resultados_detalhados = []
            items = resultado.get('items', [])
            
            print(f"\n📋 Resultados encontrados: {len(items)}\n")
            
            for i, item in enumerate(items, 1):
                detalhe = {
                    'url': item.get('link'),
                    'titulo': item.get('title'),
                    'snippet': item.get('snippet'),
                    'data_publicacao': item.get('snippet'),  # Snippet geralmente contém a data
                    'metadata': item.get('pagemap', {})
                }
                
                resultados_detalhados.append(detalhe)
                
                # Exibe formatado
                print(f"[{i}] {detalhe['titulo']}")
                print(f"    URL: {detalhe['url']}")
                print(f"    Snippet: {detalhe['snippet'][:100]}...")
                print()
            
            return resultados_detalhados
            
        except Exception as e:
            print(f"❌ Erro ao buscar detalhes: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def buscar_todas_redes(
        self,
        palavra_chave: str,
        max_resultados_por_rede: int = 10,
        data_inicio: str = None,
        ordenar_por_data: bool = False
    ) -> Dict[str, List[Dict]]:
        """
        Busca URLs em todas as redes sociais suportadas.
        
        Args:
            palavra_chave: Palavra-chave para buscar
            max_resultados_por_rede: Número máximo de URLs por rede
            data_inicio: Data de início (YYYY-MM-DD)
            ordenar_por_data: Se True, ordena por data
        
        Returns:
            Dicionário com rede_social: [lista de metadados]
        """
        print(f"\n{'='*70}")
        print(f"🔍 BUSCA AVANÇADA: '{palavra_chave}' EM TODAS AS REDES")
        print(f"{'='*70}")
        
        resultados = {}
        
        for rede in self.REDES_SOCIAIS.keys():
            print(f"\n{'─'*70}")
            print(f"📱 {rede.upper()}")
            print(f"{'─'*70}")
            
            urls = self.buscar_urls(
                palavra_chave,
                rede,
                max_resultados_por_rede,
                data_inicio=data_inicio,
                ordenar_por_data=ordenar_por_data
            )
            resultados[rede] = urls
        
        print(f"\n{'='*70}")
        print(f"✅ BUSCA CONCLUÍDA")
        print(f"{'='*70}")
        
        # Resumo
        total = 0
        for rede, urls in resultados.items():
            count = len(urls)
            total += count
            print(f"  {rede.capitalize()}: {count} URL(s)")
        print(f"\nTotal: {total} URL(s)")
        
        return resultados
    
    def obter_info_quota(self) -> Dict:
        """
        Retorna informações sobre uso de quota da API.
        
        Returns:
            Dicionário com informações da busca anterior
        """
        # Faz uma busca simples para obter metadados
        try:
            resultado = self.service.cse().list(
                q='test',
                cx=self.cx,
                num=1
            ).execute()
            
            search_info = resultado.get('searchInformation', {})
            
            return {
                'tempo_busca': search_info.get('searchTime'),
                'total_resultados': search_info.get('totalResults'),
                'formatted_total': search_info.get('formattedTotalResults')
            }
        except Exception as e:
            print(f"❌ Erro ao obter informações: {e}")
            return {}
