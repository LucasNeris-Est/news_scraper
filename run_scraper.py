"""Script de entrada para executar o scraper."""
import sys
import argparse
from src.scrapers.g1_scraper import G1Scraper
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
            palavras_chave_list = trends.extrair_tendencias_politicas(hours=args.horas_trends)
        
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


if __name__ == "__main__":
    main()

