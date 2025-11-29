"""Script principal para executar o pipeline completo."""
import argparse
from .scrapers.g1_scraper import G1Scraper
from .etl_pipeline import ETLPipeline


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description='Scraper de notícias com vetorização')
    parser.add_argument('--palavras-chave', type=str, required=True,
                       help='Palavras-chave para busca')
    parser.add_argument('--limite', type=int, default=5,
                       help='Número máximo de notícias (padrão: 5)')
    parser.add_argument('--modelo', type=str, 
                       default='sentence-transformers/all-MiniLM-L6-v2',
                       help='Modelo de embeddings (padrão: all-MiniLM-L6-v2)')
    parser.add_argument('--tabela', type=str, default='noticiasrag',
                       help='Nome da tabela no banco (padrão: noticias)')
    parser.add_argument('--salvar-json', type=str, default=None,
                       help='Salvar notícias em JSON (opcional)')
    
    args = parser.parse_args()
    
    print(f"Buscando notícias com palavras-chave: {args.palavras_chave}")
    
    # Extrai notícias
    with G1Scraper(headless=True) as scraper:
        noticias = scraper.buscar_e_extrair(args.palavras_chave, limite=args.limite)
    
    if not noticias:
        print("Nenhuma notícia encontrada.")
        return
    
    # Salva em JSON se solicitado
    if args.salvar_json:
        scraper.salvar_json(noticias, args.salvar_json)
    
    # Processa e insere no banco vetorial
    pipeline = ETLPipeline(model_name=args.modelo)
    pipeline.process_noticias(noticias, table_name=args.tabela)


if __name__ == "__main__":
    main()

