"""Script para executar o scraper do Twitter."""
import argparse
from src.scrapers.twitter_scraper import TwitterScraper


def main():
    parser = argparse.ArgumentParser(description='Scraper de posts do Twitter/X')
    parser.add_argument('--url', type=str, required=False, help='URL do post do Twitter')
    parser.add_argument('--arquivo', type=str, default='post_twitter.json', 
                       help='Nome do arquivo de saída (padrão: post_twitter.json)')
    parser.add_argument('--headless', action='store_true',  default=True,
                       help='Executar navegador em modo headless (sem interface gráfica)')
    
    args = parser.parse_args()
    
    # Se URL não foi fornecida via argumento, solicita interativamente
    url = args.url
    if not url:
        url = input("Digite a URL do post do Twitter: ").strip()
        if not url:
            print("❌ URL é obrigatória!")
            import sys
            sys.exit(1)
    
    # Usa o TwitterScraper como context manager
    with TwitterScraper(headless=args.headless, tempo_carregamento=3) as scraper:
        resultado = scraper.processar_post(url, args.arquivo)
        
        if resultado:
            print("\n✅ Scraping concluído com sucesso!")
        else:
            print("\n❌ Erro ao processar o post")


if __name__ == "__main__":
    # Para testar com parâmetros hardcoded, descomente e ajuste:
    import sys
    sys.argv = [
        'run_twitter_scraper.py',
        '--url', 'https://x.com/sbtrio/status/1998467687366959419',
        '--arquivo', 'post_twitter_09-12-2025_22-11.json',  
        '--headless',
    ]
    
    main()    