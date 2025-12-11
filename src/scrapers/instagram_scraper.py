"""Scraper específico para o Instagram."""
from bs4 import BeautifulSoup
from typing import Dict
from datetime import datetime
import time
from ..posts_scraper import PostsScraper


class InstagramScraper(PostsScraper):
    """Scraper para posts do Instagram."""
    
    BASE_URL = "https://www.instagram.com"
    
    def __init__(self, headless: bool = True, **kwargs):
        """Inicializa o InstagramScraper com wait_until='domcontentloaded'."""
        super().__init__(headless=headless, wait_until="domcontentloaded", **kwargs)
    
    def extrair_dados_post(self, legenda: str) -> Dict[str, any]:
        """
        Extrai dados específicos de um post do Instagram a partir da legenda capturada.
        
        Args:
            legenda: Texto completo capturado da página
        
        Returns:
            Dicionário com autor, legenda_limpa, curtidas, data_post
        """
        print(f"🔍 Extraindo dados específicos do Instagram da legenda...")
        
        try:
            import re
            
            # Limpa a legenda removendo trechos de login/signup e footer
            legenda_limpa = legenda
            if legenda_limpa:
                # Remove todo o trecho inicial de login/signup até o tempo (ex: 14h, 12h)
                # Padrão: Remove tudo até encontrar "{tempo}\n" seguido de conteúdo
                match_inicio = re.search(r'\d+[hdwmy]\n(.+)', legenda_limpa, re.DOTALL)
                if match_inicio:
                    legenda_limpa = match_inicio.group(1).strip()
                
                # Remove comentários: corta antes do primeiro padrão de comentário "{username} \n {tempo}\n"
                # Procura por padrão de comentário (username seguido de tempo em nova linha)
                match_comentario = re.search(r'\n([a-zA-Z0-9._]+)\s+\n(\d+[hdwmy])\n', legenda_limpa)
                if match_comentario:
                    legenda_limpa = legenda_limpa[:match_comentario.start()].strip()
                
                # Remove marcadores de fim
                marcadores_fim = [
                    "Log into like or comment.",
                    "Log in to like or comment.",
                    "See more posts",
                    "Meta\nAbout",
                ]
                
                for marcador in marcadores_fim:
                    if marcador in legenda_limpa:
                        legenda_limpa = legenda_limpa.split(marcador)[0].strip()
                        break
                
                # Remove emojis e caracteres especiais, mas mantém pontuação básica
                if legenda_limpa:
                    # Remove emojis (caracteres Unicode não-ASCII acima de \u1F600)
                    legenda_limpa = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF]+', '', legenda_limpa)
                    
                    # Substitui múltiplas quebras de linha por espaço
                    legenda_limpa = re.sub(r'\n+', ' ', legenda_limpa)
                    
                    # Remove espaços múltiplos
                    legenda_limpa = re.sub(r'\s+', ' ', legenda_limpa)
                    
                    # Remove mensagens de interface
                    legenda_limpa = re.sub(r'No comments yet\.?\s*Start the conversation\.?', '', legenda_limpa, flags=re.IGNORECASE)
                    
                    # Remove termos específicos do Instagram
                    termos_remover = [
                        r'\bLike\b', r'\bReply\b', r'\bView\b', r'\bView all\b',
                        r'\blikes\b', r'\bhours?\b', r'\bago\b', r'\bminutes?\b',
                        r'\bdays?\b', r'\bweeks?\b', r'\bmonths?\b', r'\byears?\b'
                    ]
                    for termo in termos_remover:
                        legenda_limpa = re.sub(termo, '', legenda_limpa, flags=re.IGNORECASE)
                    
                    # Remove espaços múltiplos novamente após remoção dos termos
                    legenda_limpa = re.sub(r'\s+', ' ', legenda_limpa)
                    
                    # Remove caracteres especiais mantendo apenas letras, números e pontuação básica
                    legenda_limpa = re.sub(r'[^\w\s.,!?;:()\-\'"áàâãéèêíïóôõöúçñÁÀÂÃÉÈÊÍÏÓÔÕÖÚÇÑ]', '', legenda_limpa)
                    
                    legenda_limpa = legenda_limpa.strip()
            
            # Extrai autor (username) da legenda
            autor = None
            if legenda:
                # Padrão 1: "Never miss a post from {autor}"
                match_never_miss = re.search(r'Never miss a post from ([^\n]+)', legenda)
                if match_never_miss:
                    autor = match_never_miss.group(1).strip()
                
                # Padrão 2: Procura por "{autor}\n•\nFollow" após "Log in"
                if not autor:
                    match_follow = re.search(r'Log in\n([^\n]+)\n•\nFollow', legenda)
                    if match_follow:
                        # Pega o último username antes de "•\nFollow"
                        linhas_antes_follow = match_follow.group(1).strip().split('\n')
                        if linhas_antes_follow:
                            autor = linhas_antes_follow[-1].strip()
                
                # Remove caracteres indesejados
                if autor:
                    autor = autor.replace('Verified', '').strip()
            
            # Extrai curtidas da legenda
            curtidas = None
            if legenda_limpa:
                # Procura por padrões de curtidas na legenda
                curtidas_patterns = [
                    r'(\d+(?:[,\.]\d+)*)\s*likes',
                    r'(\d+(?:[,\.]\d+)*)\s*curtidas',
                    r'(\d+(?:[,\.]\d+)*)\s*gostaram',
                    r'(\d+(?:[,\.]\d+)*)\s*like',
                ]
                
                for pattern in curtidas_patterns:
                    match = re.search(pattern, legenda_limpa.lower())
                    if match:
                        try:
                            numero_str = match.group(1).replace(',', '').replace('.', '')
                            curtidas = int(numero_str)
                            break
                        except:
                            curtidas = match.group(1)
                            break
            
            # Extrai data de publicação (formato relativo ou ISO)
            data_post = None
            if legenda:
                # Procura após o autor e "Follow" por padrões de tempo
                # Padrão: "{autor}\n \n{tempo}"
                match_tempo = re.search(r'Follow\n[^\n]*\n(\d+[hdwmy])', legenda)
                if match_tempo:
                    data_post = match_tempo.group(1)
                else:
                    # Procura por padrões de data gerais
                    data_patterns = [
                        r'(\d+[hdwmy])',  # 2d, 1w, 3h, 4m, 1y
                        r'(\d+\s*(?:hour|day|week|month|year)s?\s*ago)',
                        r'(\d+\s*(?:hora|dia|semana|mês|ano)s?\s*atrás)',
                        r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})',  # ISO format
                    ]
                    
                    for pattern in data_patterns:
                        match = re.search(pattern, legenda)
                        if match:
                            data_post = match.group(1)
                            break
            
            # Extrai comentários
            comentarios = []
            if legenda:
                # Padrão: {username}\n \n{tempo}\n{texto_comentario}\nLike\nReply
                comentarios_matches = re.finditer(
                    r'([a-zA-Z0-9._]+)\n\s+\n(\d+[hdwmy])\n(.+?)\nLike\nReply',
                    legenda,
                    re.DOTALL
                )
                
                primeiro_comentario = True
                for match in comentarios_matches:
                    username = match.group(1).strip()
                    tempo = match.group(2).strip()
                    texto = match.group(3).strip()
                    
                    # Ignora o primeiro comentário se for do autor do post (é a legenda)
                    if primeiro_comentario and autor and username == autor:
                        primeiro_comentario = False
                        continue
                    primeiro_comentario = False
                    
                    # Remove emojis e limpa o texto do comentário
                    texto_limpo = re.sub(r'[^\x00-\x7F\u00C0-\u024F\u1E00-\u1EFF]+', '', texto)
                    texto_limpo = re.sub(r'\n+', ' ', texto_limpo)
                    texto_limpo = re.sub(r'\s+', ' ', texto_limpo).strip()
                    
                    comentarios.append({
                        "author": username,
                        "time": tempo,
                        "text": texto_limpo
                    })
            
            dados = {
                "author": autor,
                "text": legenda_limpa,
                "likes": curtidas,
                "date_post": data_post,
                "comments": comentarios if comentarios else None
            }
            
            print(f"✓ Dados extraídos:")
            print(f"   - Autor: {autor or 'Não encontrado'}")
            print(f"   - Legenda: {legenda_limpa[:50] + '...' if legenda_limpa and len(legenda_limpa) > 50 else legenda_limpa or 'Não encontrada'}")
            print(f"   - Curtidas: {curtidas or 'Não encontrado'}")
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
                "data_post": None
            }
    
    def processar_post(self, url: str, arquivo_saida: str = "post_instagram.json") -> Dict:
        """
        Processa um post completo do Instagram: captura texto e extrai dados.
        
        Args:
            url: URL do post do Instagram
            arquivo_saida: Nome do arquivo JSON de saída (timestamp será adicionado automaticamente)
        
        Returns:
            Dicionário com todos os dados do post
        """
        print(f"\n{'='*60}")
        print(f"📱 PROCESSANDO POST DO INSTAGRAM")
        print(f"{'='*60}\n")
        
        # Adiciona timestamp ao nome do arquivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome_base, extensao = arquivo_saida.rsplit('.', 1) if '.' in arquivo_saida else (arquivo_saida, 'json')
        arquivo_com_timestamp = f"{nome_base}_{timestamp}.{extensao}"
        
        # 1. Captura o texto completo da página
        texto_completo = self.capturar_texto_rede_social(url)
        
        # 2. Extrai dados específicos do Instagram a partir do texto capturado
        dados_especificos = self.extrair_dados_post(texto_completo)
        
        # 3. Salva tudo em JSON
        resultado = self.salvar_json(
            texto_capturado=texto_completo,
            url=url,
            legenda=dados_especificos.get("text", ""),
            curtidas=dados_especificos.get("likes"),
            data_post=dados_especificos.get("date_post"),
            autor=dados_especificos.get("author"),
            comentarios=dados_especificos.get("comments"),
            arquivo=arquivo_com_timestamp,
            social_network="instagram"
        )
        
        print(f"\n{'='*60}")
        print(f"✅ PROCESSAMENTO CONCLUÍDO")
        print(f"{'='*60}\n")
        
        return resultado
