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
    # Para testar com parâmetros hardcoded, descomente e ajuste:
    import sys
    sys.argv = [
        'run_linkedin_scraper.py',
        '--url', 'https://pt.linkedin.com/posts/poder360_o-deputado-nikolas-ferreira-pl-mg-publicou-activity-7404344139573854208-zvl5',
        '--arquivo', 'post_linkedin_09-12-2025_22-11.json',  
        '--headless',
    ]
# Exemplos de URLs de posts do LinkedIn para teste:
#https://pt.linkedin.com/posts/neuber-hyppolito_fqm-conven%C3%A7%C3%A3o-activity-6892992648224079872-3zd3
#https://pt.linkedin.com/posts/gustavo-pires-3baa60163_o-politeia-%C3%A9-um-projeto-de-ensino-pesquisa-activity-7344554706058280960-etk2
#https://pt.linkedin.com/posts/veja-com_ge-aerospace-decola-em-banco-de-provas-de-activity-7404138106347724800-1kCD
#https://pt.linkedin.com/posts/poder360_por-291-a-148-a-câmara-dos-deputados-activity-7404465157395173376-jhrR
#https://pt.linkedin.com/posts/estadao_o-perigo-dos-precedentes-acordão-no-congresso-activity-7404459465971953666-2cZw
#https://pt.linkedin.com/posts/veja-com_veja-pensamentododia-activity-7404459914552819712-BQZ5
#https://pt.linkedin.com/posts/poder360_o-deputado-nikolas-ferreira-pl-mg-publicou-activity-7404344139573854208-zvl5
    main()    