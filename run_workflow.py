import sys
import argparse
from datetime import datetime
from src.scrapers.g1_scraper import G1Scraper
from src.scrapers.google_scraper import GoogleScraper
from src.scrapers.instagram_scraper import InstagramScraper
from src.scrapers.linkedin_scraper import LinkedInScraper
from src.scrapers.twitter_scraper import TwitterScraper
from src.etl_pipeline import ETLPipeline
from src.trends_extractor import GoogleTrendsExtractor


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description='Scraper de notícias com vetorização')
    parser.add_argument('--palavras-chave', type=str, default=None,
                       help='Palavras-chave para busca (opcional, se não fornecido usa Google Trends)')
    parser.add_argument('--limite', type=int, default=5,
                       help='Número máximo de notícias por palavra-chave (padrão: 5)')
    parser.add_argument('--modelo', type=str, 
                       default='sentence-transformers/all-MiniLM-L6-v2',
                       help='Modelo de embeddings (padrão: all-MiniLM-L6-v2)')
    parser.add_argument('--tabela', type=str, default='noticias',
                       help='Nome da tabela no banco (padrão: noticias)')
    parser.add_argument('--salvar-json', type=str, default=None,
                       help='Salvar notícias em JSON (opcional)')
    parser.add_argument('--sem-trends', action='store_true', default=False,
                       help='Desabilitar Google Trends (só funciona com --palavras-chave)')
    parser.add_argument('--horas-trends', type=int, default=168,
                       help='Últimas N horas para Google Trends (padrão: 168 = 7 dias)')
    parser.add_argument('--max-trends', type=int, default=5,
                       help='Número máximo de tendências a extrair do Google Trends (padrão: 5)')
    
    args = parser.parse_args()
    
    # Determina as palavras-chave a usar
    palavras_chave_list = []
    
    if args.palavras_chave:
        # Se fornecido manualmente, usa apenas essa
        palavras_chave_list = [args.palavras_chave]
        print(f"Usando palavras-chave fornecidas: {args.palavras_chave}")
    elif not args.sem_trends:
        # Extrai tendências do Google Trends
        print("Extraindo tendências políticas do Google Trends...")
        with GoogleTrendsExtractor(headless=True) as trends:
            palavras_chave_list = trends.extrair_tendencias_politicas(
                hours=args.horas_trends,
                max_trends=args.max_trends
            )
        
        # Fecha o context manager antes de continuar
        # (o with já fecha automaticamente, mas garantimos que está fechado)
        
        if not palavras_chave_list:
            print("Nenhuma tendência encontrada no Google Trends.")
            return
        
        print(f"Tendências encontradas: {len(palavras_chave_list)}")
        for i, trend in enumerate(palavras_chave_list, 1):
            print(f"  {i}. {trend}")
    
    if not palavras_chave_list:
        print("Nenhuma palavra-chave para buscar.")
        return
    
    # Coleta todas as notícias
    todas_noticias = []
    
    # Usa um novo context manager para o scraper (separado do trends)
    with G1Scraper(headless=True) as scraper:
        for i, palavras_chave in enumerate(palavras_chave_list, 1):
            print(f"\n[{i}/{len(palavras_chave_list)}] Buscando notícias para: {palavras_chave}")
            noticias = scraper.buscar_e_extrair(palavras_chave, limite=args.limite)
            
            if noticias:
                todas_noticias.extend(noticias)
                print(f"  -> {len(noticias)} notícias encontradas")
            else:
                print(f"  -> Nenhuma notícia encontrada")
    
    if not todas_noticias:
        print("\nNenhuma notícia encontrada no total.")
        return
    
    print(f"\nTotal de notícias coletadas: {len(todas_noticias)}")
    
    # Salva em JSON se solicitado
    if args.salvar_json:
        scraper.salvar_json(todas_noticias, args.salvar_json)
    
    # Processa e insere no banco vetorial
    print("\nProcessando e inserindo no banco vetorial...")
    pipeline = ETLPipeline(model_name=args.modelo)
    pipeline.process_noticias(todas_noticias, table_name=args.tabela)



    # Palavras-chave definidas, inicia a pesquisa das URL no Google Custom Search
    print(f"\n{'='*70}")
    print("🔍 ETAPA 1: BUSCANDO URLs NAS REDES SOCIAIS")
    print(f"{'='*70}\n")
    
    # Mapeia redes sociais para seus scrapers
    scrapers_map = {
        'instagram': InstagramScraper,
        'linkedin': LinkedInScraper,
        'twitter': TwitterScraper
    }
    
    # Para cada palavra-chave
    for idx, palavra_chave in enumerate(palavras_chave_list, 1):
        print(f"\n{'─'*70}")
        print(f"📌 [{idx}/{len(palavras_chave_list)}] Processando: '{palavra_chave}'")
        print(f"{'─'*70}")
        
        # 1. Busca URLs no Google Custom Search
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_urls = f"posts_extraidos/{palavra_chave.replace(' ', '_')}_{timestamp}_urls.json"
        
        print(f"\n🔎 Buscando URLs para '{palavra_chave}' (últimos 7 dias)...")
        
        with GoogleScraper() as google:
            # Busca em todas as redes sociais dos últimos 7 dias
            resultados_google = google.buscar_todas_redes(
                palavra_chave=palavra_chave,
                max_resultados_por_rede=5,
                ordenar_por_data=True
            )
            
            # Salva URLs encontradas
            import json
            import os
            os.makedirs('posts_extraidos', exist_ok=True)
            
            with open(arquivo_urls, 'w', encoding='utf-8') as f:
                json.dump({
                    'palavra_chave': palavra_chave,
                    'data_busca': datetime.now().isoformat(),
                    'resultados': resultados_google
                }, f, ensure_ascii=False, indent=2)
            
            print(f"✅ URLs salvas em: {arquivo_urls}")
        
        # 2. Extrai conteúdo dos posts para cada rede social
        print(f"\n{'='*70}")
        print("📱 ETAPA 2: EXTRAINDO CONTEÚDO DOS POSTS")
        print(f"{'='*70}\n")
        
        for rede, urls_metadados in resultados_google.items():
            if not urls_metadados:
                print(f"\n⚠️ Nenhuma URL encontrada para {rede.upper()}")
                continue
            
            print(f"\n{'─'*70}")
            print(f"📱 Processando {rede.upper()}: {len(urls_metadados)} post(s)")
            print(f"{'─'*70}")
            
            # Seleciona o scraper apropriado
            scraper_class = scrapers_map.get(rede)
            if not scraper_class:
                print(f"❌ Scraper não disponível para {rede}")
                continue
            
            # Extrai conteúdo de cada post
            with scraper_class(headless=True) as scraper:
                for i, metadado in enumerate(urls_metadados, 1):
                    url = metadado['url']
                    print(f"\n  [{i}/{len(urls_metadados)}] Extraindo: {url}")
                    
                    try:
                        # Nome do arquivo baseado na palavra-chave e índice
                        arquivo_post = f"{palavra_chave.replace(' ', '_')}_{rede}_{i}_{timestamp}.json"
                        
                        # Extrai dados do post
                        resultado = scraper.processar_post(url, arquivo_post)
                        
                        if resultado:
                            print(f"  ✅ Post extraído: {arquivo_post}")
                            print(f"     Autor: {resultado.get('autor', 'N/A')}")
                            print(f"     Curtidas: {resultado.get('curtidas', 'N/A')}")
                            print(f"     Comentários: {resultado.get('comentarios', 'N/A')}")
                        else:
                            print(f"  ⚠️ Falha ao extrair post")
                    
                    except Exception as e:
                        print(f"  ❌ Erro ao processar URL: {e}")
                        continue
        
        print(f"\n✅ Palavra-chave '{palavra_chave}' processada com sucesso!\n")
    
    print(f"\n{'='*70}")
    print("✅ WORKFLOW CONCLUÍDO")
    print(f"{'='*70}")
    print(f"Total de palavras-chave processadas: {len(palavras_chave_list)}")
    print(f"Posts salvos em: posts_extraidos/")


if __name__ == "__main__":
    main()

