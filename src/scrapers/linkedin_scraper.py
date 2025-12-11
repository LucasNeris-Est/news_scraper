"""Scraper específico para o LinkedIn."""
from bs4 import BeautifulSoup
from typing import Dict
from datetime import datetime
import time
import re
from ..posts_scraper import PostsScraper


class LinkedInScraper(PostsScraper):
    """Scraper para posts do LinkedIn."""
    
    BASE_URL = "https://www.linkedin.com"
    
    def __init__(self, headless: bool = True, **kwargs):
        """Inicializa o LinkedInScraper com wait_until='networkidle'."""
        super().__init__(headless=headless, wait_until="networkidle", **kwargs)
    
    def extrair_dados_post(self, legenda: str) -> Dict[str, any]:
        """
        Extrai dados específicos de um post do LinkedIn a partir da legenda capturada.
        
        Args:
            legenda: Texto completo capturado da página
        
        Returns:
            Dicionário com autor, legenda_limpa, curtidas, data_post
        """
        print(f"🔍 Extraindo dados específicos do LinkedIn da legenda...")
        
        try:
            # Remove trechos de cabeçalho e rodapé da interface do LinkedIn
            legenda_limpa = legenda
            
            if legenda_limpa:
                # Remove cabeçalho padrão do LinkedIn
                cabecalhos_remover = [
                    "Pular para conteúdo principal LinkedIn Artigos Pessoas Learning Vagas Jogos Entrar Cadastre-se agora",
                    "Pular para conteúdo principal LinkedIn Artigos Pessoas Learning Vagas Jogos Entrar Inscreva-se agora",
                ]
                for cabecalho in cabecalhos_remover:
                    if cabecalho in legenda_limpa:
                        legenda_limpa = legenda_limpa.replace(cabecalho, "").strip()
                
                # Remove cabeçalho: tudo antes do timestamp (ex: "1 d", "1 sem")
                # Padrão: Remove tudo até encontrar "\n\n{tempo}\n\n" ou "\n{tempo}\n"
                match_inicio = re.search(r'\n+(\d+\s*(?:[hdwmy]|sem|dia|hora))\n+', legenda_limpa)
                if match_inicio:
                    # Pega tudo após o timestamp
                    inicio_conteudo = match_inicio.end()
                    legenda_limpa = legenda_limpa[inicio_conteudo:].strip()
                
                # Marcadores de fim de conteúdo
                marcadores_fim = [
                    "Ver perfil  Seguir",
                    "Conferir tópicos",
                    "Ver todos",
                    "Sign in to view more content",
                    "Join now",
                    "Sign in",
                    "Create your free account",
                    "Agree & Join",
                    "© 2025 LinkedIn",
                    "© 2024 LinkedIn",
                    "LinkedIn and third parties",
                ]
                
                for marcador in marcadores_fim:
                    if marcador in legenda_limpa:
                        legenda_limpa = legenda_limpa.split(marcador)[0].strip()
                        break
            
            # Remove comentários (tudo após "Gostei\nComentar\nCompartilhe")
            if legenda_limpa and "Gostei\nComentar\nCompartilhe" in legenda_limpa:
                legenda_limpa = legenda_limpa.split("Gostei\nComentar\nCompartilhe")[0].strip()
            
            # Limpa a legenda: remove emojis, caracteres especiais e \n
            if legenda_limpa:
                # Remove emojis (caracteres Unicode não-ASCII acima de \u1F600)
                legenda_limpa = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF]+', '', legenda_limpa)
                
                # Substitui múltiplas quebras de linha por espaço
                legenda_limpa = re.sub(r'\n+', ' ', legenda_limpa)
                
                # Remove espaços múltiplos
                legenda_limpa = re.sub(r'\s+', ' ', legenda_limpa)
                
                # Remove termos do LinkedIn que podem ter sobrado
                termos_linkedin = [
                    r'\bmais\b\s+\d+',  # "mais 215"
                    r'\d+\s+comentários',  # "23 comentários"
                ]
                for termo in termos_linkedin:
                    legenda_limpa = re.sub(termo, '', legenda_limpa, flags=re.IGNORECASE)
                
                # Remove espaços múltiplos novamente
                legenda_limpa = re.sub(r'\s+', ' ', legenda_limpa)
                
                # Remove caracteres especiais mantendo apenas letras, números e pontuação básica
                legenda_limpa = re.sub(r'[^\w\s.,!?;:()\-\'"áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]', '', legenda_limpa)
                
                legenda_limpa = legenda_limpa.strip()
            
            # Extrai autor da primeira linha da legenda ou da URL
            autor = None
            if legenda_limpa:
                linhas = legenda_limpa.split('\n')
                for linha in linhas[:10]:  # Verifica as primeiras linhas
                    linha_limpa = linha.strip()
                    # Procura por padrão "Publicação de Nome Sobrenome" ou "Nome Sobrenome" no início
                    if linha_limpa.startswith("Publicação de "):
                        autor = linha_limpa.replace("Publicação de ", "").strip()
                        break
                    # Verifica se parece com um nome (tem espaço, não muito longo, não é menu)
                    if (linha_limpa and ' ' in linha_limpa and len(linha_limpa) < 50 and 
                        not linha_limpa.startswith('#') and 
                        linha_limpa not in ['Pular para conteúdo principal', 'LinkedIn', 'Artigos', 'Pessoas', 'Learning', 'Vagas', 'Jogos']):
                        # Pode ser o nome do autor
                        autor = linha_limpa.replace('Verified', '').strip()
                        # Se encontrou algo que parece um nome, para
                        if autor and len(autor.split()) >= 2:  # Pelo menos 2 palavras (nome e sobrenome)
                            break
            
            # Extrai curtidas/likes da legenda
            curtidas = None
            if legenda_limpa:
                # Procura por padrões de curtidas/likes (formato: "110\n13 Comments\nLike")
                curtidas_patterns = [
                    r'\n(\d+(?:[,\.]\d+)*)\n\d+\s*Comments?\s*\nLike',  # Padrão LinkedIn: número antes de "X Comments\nLike"
                    r'(\d+(?:[,\.]\d+)*)\s*reactions?',
                    r'(\d+(?:[,\.]\d+)*)\s*likes?',
                    r'(\d+(?:[,\.]\d+)*)\s*reações',
                    r'(\d+(?:[,\.]\d+)*)\s*curtidas?',
                ]
                
                for pattern in curtidas_patterns:
                    match = re.search(pattern, legenda_limpa, re.IGNORECASE)
                    if match:
                        try:
                            numero_str = match.group(1).replace(',', '').replace('.', '')
                            curtidas = int(numero_str)
                            break
                        except:
                            curtidas = match.group(1)
                            break
            
            # Extrai comentários da legenda
            comentarios = None
            if legenda_limpa:
                # Procura por padrões de comentários (formato: "13 Comments")
                comentarios_patterns = [
                    r'(\d+(?:[,\.]\d+)*)\s*Comments?',
                    r'(\d+(?:[,\.]\d+)*)\s*Comentários?',
                    r'(\d+(?:[,\.]\d+)*)\s*Comment',
                ]
                
                for pattern in comentarios_patterns:
                    match = re.search(pattern, legenda_limpa, re.IGNORECASE)
                    if match:
                        try:
                            numero_str = match.group(1).replace(',', '').replace('.', '')
                            comentarios = int(numero_str)
                            break
                        except:
                            comentarios = match.group(1)
                            break
            
            # Extrai data de publicação (formato relativo: 2d, 1w, 3h, etc)
            data_post = None
            if legenda_limpa:
                # Procura por padrões de tempo relativo
                data_patterns = [
                    r'(\d+[hdwmy])',  # 2d, 1w, 3h, 4m, 1y
                    r'(\d+\s*(?:hour|day|week|month|year)s?\s*ago)',
                    r'(\d+\s*(?:hora|dia|semana|mês|ano)s?\s*atrás)',
                ]
                
                for pattern in data_patterns:
                    match = re.search(pattern, legenda_limpa.lower())
                    if match:
                        data_post = match.group(1)
                        break
            
            dados = {
                "author": autor,
                "text": legenda_limpa,
                "likes": curtidas,
                "comments": comentarios,
                "date_post": data_post
            }
            
            print(f"✓ Dados extraídos:")
            print(f"   - Autor: {autor or 'Não encontrado'}")
            print(f"   - Legenda: {legenda_limpa[:50] + '...' if legenda_limpa and len(legenda_limpa) > 50 else legenda_limpa or 'Não encontrada'}")
            print(f"   - Curtidas: {curtidas or 'Não encontrado'}")
            print(f"   - Comentários: {comentarios or 'Não encontrado'}")
            print(f"   - Data: {data_post or 'Não encontrada'}")
            
            return dados
            
        except Exception as e:
            print(f"✗ Erro ao extrair dados: {e}")
            import traceback
            traceback.print_exc()
            return {
                "autor": None,
                "legenda": "",
                "curtidas": None,
                "comentarios": None,
                "data_post": None
            }
    
    def processar_post(self, url: str, arquivo_saida: str = "post_linkedin.json") -> Dict:
        """
        Processa um post completo do LinkedIn: captura texto e extrai dados.
        
        Args:
            url: URL do post do LinkedIn
            arquivo_saida: Nome do arquivo JSON de saída (timestamp será adicionado automaticamente)
        
        Returns:
            Dicionário com todos os dados do post
        """
        print(f"\n{'='*60}")
        print(f"💼 PROCESSANDO POST DO LINKEDIN")
        print(f"{'='*60}\n")
        
        # Extrai autor da URL (formato: /posts/nome-sobrenome-id_...)
        autor_url = None
        match_url = re.search(r'/posts/([^_/]+)', url)
        if match_url:
            # Converte hífens em espaços e capitaliza cada palavra
            autor_slug = match_url.group(1)
            # Remove números no final do slug (ex: gustavo-pires-3baa60163 -> gustavo-pires)
            autor_slug = re.sub(r'-[\da-f]+$', '', autor_slug)
            # Converte para nome legível
            autor_url = ' '.join(word.capitalize() for word in autor_slug.split('-'))
            print(f"📝 Autor extraído da URL: {autor_url}")
        
        # Adiciona timestamp ao nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_base, extensao = arquivo_saida.rsplit('.', 1) if '.' in arquivo_saida else (arquivo_saida, 'json')
        arquivo_com_timestamp = f"{nome_base}_{timestamp}.{extensao}"
        
        # 1. Captura o texto completo da página
        texto_completo = self.capturar_texto_rede_social(url)
        
        # 2. Extrai dados específicos do LinkedIn a partir do texto capturado
        dados_especificos = self.extrair_dados_post(texto_completo)
        
        # 3. Usa o autor da URL se não foi encontrado no texto
        autor_final = autor_url
        
        # 4. Salva tudo em JSON (inclui comentarios nos dados adicionais)
        resultado = self.salvar_json(
            texto_capturado=texto_completo,
            url=url,
            legenda=dados_especificos.get("text", ""),
            curtidas=dados_especificos.get("likes"),
            data_post=dados_especificos.get("date_post"),
            autor=autor_final,
            arquivo=arquivo_com_timestamp,
            comentarios=dados_especificos.get("comments"),
            social_network="linkedin"
        )
        
        print(f"\n{'='*60}")
        print(f"✅ PROCESSAMENTO CONCLUÍDO")
        print(f"{'='*60}\n")
        
        return resultado
