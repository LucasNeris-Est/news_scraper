"""Script para executar busca de URLs no Google."""
import argparse
import json
import sys
from src.scrapers.google_search import GoogleSearch


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description='Busca URLs de redes sociais no Google',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos de uso:
  python run_google_search.py --palavra-chave "blindagem" --rede instagram
  python run_google_search.py --palavra-chave "lula" --rede todas --max-resultados 5
  python run_google_search.py --palavra-chave "política" --salvar resultados.json
        '''
    )
    
    parser.add_argument('--palavra-chave', type=str, required=False, 
                       help='Palavra-chave para buscar')
    parser.add_argument('--rede', type=str, choices=['twitter', 'instagram', 'linkedin', 'todas'],
                       default='todas', help='Rede social para buscar (padrão: todas)')
    parser.add_argument('--max-resultados', type=int, default=10,
                       help='Número máximo de resultados por rede (padrão: 10)')
    parser.add_argument('--tempo-espera', type=int, default=2,
                       help='Tempo de espera entre buscas em segundos (padrão: 2)')
    parser.add_argument('--salvar', type=str, metavar='ARQUIVO',
                       help='Salvar resultados em arquivo JSON')
    
    args = parser.parse_args()
    
    # Se palavra-chave não foi fornecida, solicita interativamente
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
    
    # Usa GoogleSearch como context manager
    with GoogleSearch(tempo_espera=args.tempo_espera) as searcher:
        if args.rede == 'todas':
            # Busca em todas as redes
            resultados = searcher.buscar_todas_redes(palavra_chave, args.max_resultados)
        else:
            # Busca em rede específica
            urls = searcher.buscar_urls(palavra_chave, args.rede, args.max_resultados)
            resultados = {args.rede: urls}
        
        # Exibe resultados formatados
        _exibir_resultados(resultados)
        
        # Salva em arquivo se solicitado
        if args.salvar:
            _salvar_resultados(resultados, args.salvar)


def _exibir_resultados(resultados: dict):
    """Exibe os resultados da busca de forma formatada."""
    print("\n" + "="*60)
    print("📋 RESULTADOS DA BUSCA")
    print("="*60)
    
    total_urls = 0
    for rede, urls in resultados.items():
        print(f"\n{rede.upper()}:")
        if urls:
            for i, url in enumerate(urls, 1):
                print(f"  {i}. {url}")
            total_urls += len(urls)
        else:
            print("  Nenhuma URL encontrada")
    
    print(f"\n{'─'*60}")
    print(f"Total: {total_urls} URL(s) encontrada(s)")


def _salvar_resultados(resultados: dict, arquivo: str):
    """Salva os resultados em arquivo JSON."""
    try:
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        print(f"\n✅ Resultados salvos em: {arquivo}")
    except Exception as e:
        print(f"\n❌ Erro ao salvar arquivo: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
