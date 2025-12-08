"""Script para executar busca avançada usando Google Custom Search API."""
import argparse
import json
import sys
import os
from src.scrapers.google_avancado import GoogleAvancado


def main():
    """Função principal do script."""
    parser = argparse.ArgumentParser(
        description='Busca avançada de URLs usando Google Custom Search API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Exemplos de uso:
  python run_google_avancado.py --palavra-chave "pec da blindagem" --rede instagram
  python run_google_avancado.py --palavra-chave "lula" --rede todas --max-resultados 5
  python run_google_avancado.py --palavra-chave "política" --data-inicio 2025-01-01 --ordenar-por-data
  python run_google_avancado.py --palavra-chave "eleições" --dias-anteriores 7 --detalhes

Configuração:
  Defina as variáveis de ambiente:
    GOOGLE_API_KEY - Sua chave da Google Custom Search API
    GOOGLE_CX - ID do seu Custom Search Engine
  
  Ou use argumentos:
    --api-key "sua_chave"
    --cx "seu_cx_id"
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
    parser.add_argument('--detalhes', action='store_true',
                       help='Retorna metadados completos (título, snippet, data)')
    parser.add_argument('--salvar', type=str, metavar='ARQUIVO',
                       help='Salvar resultados em arquivo JSON')
    parser.add_argument('--api-key', type=str,
                       help='Google API Key (ou use GOOGLE_API_KEY env var)')
    parser.add_argument('--cx', type=str,
                       help='Custom Search Engine ID (ou use GOOGLE_CX env var)')
    
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
    
    # Verifica credenciais
    api_key = args.api_key or os.getenv('GOOGLE_API_KEY')
    cx = args.cx or os.getenv('GOOGLE_CX')
    
    if not api_key or not cx:
        print("\n❌ ERRO: Credenciais não configuradas!")
        print("\nConfigure as variáveis de ambiente:")
        print("  set GOOGLE_API_KEY=sua_chave")
        print("  set GOOGLE_CX=seu_cx_id")
        print("\nOu use os argumentos --api-key e --cx")
        print("\nObtenha suas credenciais em:")
        print("  API Key: https://console.cloud.google.com/apis/credentials")
        print("  CX ID: https://programmablesearchengine.google.com/")
        sys.exit(1)
    
    try:
        # Usa GoogleAvancado como context manager
        with GoogleAvancado(api_key=api_key, cx=cx) as searcher:
            if args.rede == 'todas':
                # Busca em todas as redes
                if args.detalhes:
                    print("\n⚠️ Modo detalhes não disponível para 'todas' as redes")
                    print("Use --rede [twitter|instagram|linkedin] para detalhes\n")
                
                resultados = searcher.buscar_todas_redes(
                    palavra_chave,
                    args.max_resultados,
                    data_inicio=args.data_inicio,
                    ordenar_por_data=args.ordenar_por_data
                )
            else:
                # Busca em rede específica
                if args.detalhes:
                    # Busca com detalhes
                    resultados_detalhados = searcher.buscar_com_detalhes(
                        palavra_chave,
                        args.rede,
                        args.max_resultados,
                        data_inicio=args.data_inicio,
                        ordenar_por_data=args.ordenar_por_data,
                        dias_anteriores=args.dias_anteriores
                    )
                    resultados = {args.rede: resultados_detalhados}
                else:
                    # Busca simples (apenas URLs)
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
            
            # Exibe resultados formatados (se não for modo detalhes)
            if not args.detalhes:
                _exibir_resultados(resultados)
            
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
        
        # Verifica se são URLs simples ou dados detalhados
        if dados and isinstance(dados[0], dict):
            # Dados detalhados (já foram exibidos)
            total_urls += len(dados)
        elif dados:
            # URLs simples
            for i, url in enumerate(dados, 1):
                print(f"  {i}. {url}")
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
    main()
