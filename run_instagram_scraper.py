"""Script para executar o scraper do Instagram."""
from src.scrapers.instagram_scraper import InstagramScraper
import argparse


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(description='Scraper de posts do Instagram')
    parser.add_argument('--url', type=str, required=True, help='URL do post do Instagram')
    parser.add_argument('--arquivo', type=str, default='post_instagram.json', help='Nome do arquivo de saída')
    parser.add_argument('--headless', action='store_true', default=True, help='Executar navegador em modo headless')
    
    args = parser.parse_args()
    
    print(f"📱 Scraper do Instagram")
    print(f"🔗 URL: {args.url}")
    print(f"💾 Arquivo de saída: {args.arquivo}\n")
    
    try:
        with InstagramScraper(headless=args.headless) as scraper:
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
    # Para testar com parâmetros hardcoded, descomente e ajuste:
    import sys
    sys.argv = [
        'run_instagram_scraper.py',
        '--url', 'https://www.instagram.com/p/DSFQiuUgJDO/',
        '--arquivo', 'post_instagram_09-12-2025_22-11.json',  
        '--headless',
    ]
    main()    
    
# Exemplos de URLs de posts do Instagram para teste:
#https://www.instagram.com/p/DSG89SFjAXq/
#https://www.instagram.com/p/DSGxI5TjR8q/
#https://www.instagram.com/p/DSBhdTeE07d/
#https://www.instagram.com/p/DSHn3VvkcnP/
#https://www.instagram.com/p/DSFQiuUgJDO/