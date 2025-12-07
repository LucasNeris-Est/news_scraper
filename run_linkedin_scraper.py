"""Script para executar o scraper do LinkedIn."""
from src.scrapers.linkedin_scraper import LinkedInScraper
import argparse
import sys


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description='Scraper de posts do LinkedIn')
    parser.add_argument('--url', type=str, required=False, help='URL do post do LinkedIn')
    parser.add_argument('--arquivo', type=str, default='post_linkedin.json', help='Nome do arquivo de saída')
    parser.add_argument('--headless', action='store_true', default=True, help='Executar navegador em modo headless')
    
    args = parser.parse_args()
    
    # Se URL não for fornecida via argumento, pede interativamente
    if not args.url:
        print("URL não fornecida. Por favor, forneça a URL do post do LinkedIn:")
        url = input("URL: ").strip()
        if not url:
            print("❌ Erro: URL é obrigatória!")
            sys.exit(1)
        args.url = url
    
    print(f"💼 Scraper do LinkedIn")
    print(f"🔗 URL: {args.url}")
    print(f"💾 Arquivo de saída: {args.arquivo}\n")
    
    try:
        with LinkedInScraper(headless=args.headless) as scraper:
            # Processa o post completo
            resultado = scraper.processar_post(args.url, arquivo_saida=args.arquivo)
            
            if resultado:
                print(f"\n✅ Scraping concluído com sucesso!")
            else:
                print("\n⚠️ Nenhum dado foi capturado.")
    
    except Exception as e:
        print(f"\n❌ Erro durante o scraping: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
