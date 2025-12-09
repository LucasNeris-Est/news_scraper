"""Script para executar busca avançada usando Google Custom Search API."""
import argparse
import json
import sys
import os
from dotenv import load_dotenv
from src.scrapers.google_scraper import GoogleScraper

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description='Busca avançada de URLs usando Google Custom Search API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos de uso:
  python run_google_scraper.py --palavra-chave "pec da blindagem" --rede instagram
  python run_google_scraper.py --palavra-chave "lula" --rede todas --max-resultados 5
  python run_google_scraper.py --palavra-chave "política" --data-inicio 2025-01-01 --ordenar-por-data
  python run_google_scraper.py --palavra-chave "eleições" --dias-anteriores 7 --salvar resultados.json

Configuração:
  As credenciais são carregadas automaticamente do arquivo .env:
    GOOGLE_API_KEY - Sua chave da Google Custom Search API
    GOOGLE_CX - ID do seu Custom Search Engine
        '''
    )
    
    parser.add_argument('--palavra-chave', type=str, required=False,
                       help='Palavra-chave para buscar (correspondência exata)')
    parser.add_argument('--rede', type=str, 
                       choices=['twitter', 'instagram', 'linkedin', 'todas'],
                       default='todas',
                       help='Rede social para buscar (padrão: todas)')
    parser.add_argument('--max-resultados', type=int, default=10,
                       help='Número máximo de resultados por rede (padrão: 10, máx API: 10)')
    parser.add_argument('--data-inicio', type=str,
                       help='Data de início no formato YYYY-MM-DD (ex: 2025-01-01)')
    parser.add_argument('--data-fim', type=str,
                       help='Data de fim no formato YYYY-MM-DD')
    parser.add_argument('--dias-anteriores', type=int,
                       help='Restringe busca aos últimos N dias (ex: 7 para última semana)')
    parser.add_argument('--ordenar-por-data', action='store_true',
                       help='Ordena resultados por data (mais recentes primeiro)')
    parser.add_argument('--salvar', type=str, metavar='ARQUIVO',
                       help='Salvar resultados em arquivo JSON')
    
    args = parser.parse_args()
    
    # Solicita palavra-chave se não fornecida
    palavra_chave = args.palavra_chave
    if not palavra_chave:
        try:
            palavra_chave = input("Digite a palavra-chave para buscar: ").strip()
            if not palavra_chave:
                print("❌ Palavra-chave é obrigatória!")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n⚠️ Operação cancelada pelo usuário")
            sys.exit(0)
    
    # Verifica credenciais do arquivo .env
    api_key = os.getenv('GOOGLE_API_KEY')
    cx = os.getenv('GOOGLE_CX')
    
    if not api_key or not cx:
        print("\n❌ ERRO: Credenciais não encontradas no arquivo .env!")
        print("\nCertifique-se de que o arquivo .env contém:")
        print("  GOOGLE_API_KEY=sua_chave")
        print("  GOOGLE_CX=seu_cx_id")
        print("\nObtenha suas credenciais em:")
        print("  API Key: https://console.cloud.google.com/apis/credentials")
        print("  CX ID: https://programmablesearchengine.google.com/")
        sys.exit(1)
    
    try:
        # Usa GoogleScraper como context manager
        with GoogleScraper(api_key=api_key, cx=cx) as searcher:
            if args.rede == 'todas':
                # Busca em todas as redes
                resultados = searcher.buscar_todas_redes(
                    palavra_chave,
                    args.max_resultados,
                    data_inicio=args.data_inicio,
                    ordenar_por_data=args.ordenar_por_data
                )
            else:
                # Busca em rede específica
                urls = searcher.buscar_urls(
                    palavra_chave,
                    args.rede,
                    args.max_resultados,
                    data_inicio=args.data_inicio,
                    data_fim=args.data_fim,
                    ordenar_por_data=args.ordenar_por_data,
                    dias_anteriores=args.dias_anteriores
                )
                resultados = {args.rede: urls}
            
            # Salva em arquivo se solicitado
            if args.salvar:
                _salvar_resultados(resultados, args.salvar)
    
    except ValueError as e:
        print(f"\n❌ ERRO: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _exibir_resultados(resultados: dict):
    """Exibe os resultados da busca de forma formatada."""
    print(f"\n{'='*70}")
    print("📋 RESULTADOS DA BUSCA")
    print(f"{'='*70}")
    
    total_urls = 0
    for rede, dados in resultados.items():
        print(f"\n{rede.upper()}:")
        
        if dados:
            # Verifica se são URLs simples ou dados detalhados
            if isinstance(dados[0], str):
                # URLs simples
                for i, url in enumerate(dados, 1):
                    print(f"  {i}. {url}")
            else:
                # Dados detalhados (não exibe novamente, já foram mostrados)
                pass
            total_urls += len(dados)
        else:
            print("  Nenhuma URL encontrada")
    
    print(f"\n{'─'*70}")
    print(f"Total: {total_urls} URL(s) encontrada(s)")


def _salvar_resultados(resultados: dict, arquivo: str):
    """Salva os resultados em arquivo JSON."""
    try:
        # Adiciona metadados
        output = {
            'data_busca': __import__('datetime').datetime.now().isoformat(),
            'total_redes': len(resultados),
            'total_urls': sum(len(urls) for urls in resultados.values()),
            'resultados': resultados
        }
        
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Resultados salvos em: {arquivo}")
    except Exception as e:
        print(f"\n❌ Erro ao salvar arquivo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Para testar com parâmetros hardcoded, descomente e ajuste:
    import sys
    sys.argv = [
        'run_google_avancado.py',
        '--palavra-chave', 'lula',
        '--rede', 'todas',
        '--max-resultados', '2',
        '--ordenar-por-data',
        '--dias-anteriores', '7',
        '--salvar', 'resultados.json'
    ]
    
    main()
