"""Classe base para scrapers de posts de redes sociais."""
from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright, Browser, Page
from typing import Optional, Dict, List
from datetime import datetime
import json
import time
import os


class PostsScraper(ABC):
    """Classe base abstrata para scrapers de posts de redes sociais."""
    
    def __init__(
        self, 
        headless: bool = True,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
        timeout_navegacao: int = 30000,
        tempo_carregamento: int = 3,
        wait_until: str = "domcontentloaded"
    ):
        """
        Inicializa o scraper com configurações do navegador.
        
        Args:
            headless: Se True, executa o navegador em modo headless (sem interface gráfica)
            viewport_width: Largura da janela do navegador em pixels
            viewport_height: Altura da janela do navegador em pixels
            timeout_navegacao: Timeout máximo para navegação em milissegundos
            tempo_carregamento: Tempo de espera para carregamento completo da página em segundos
            wait_until: Estratégia de espera do Playwright ("domcontentloaded", "load", "networkidle")
        """
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.timeout_navegacao = timeout_navegacao
        self.tempo_carregamento = tempo_carregamento
        self.wait_until = wait_until
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    def __enter__(self):
        """
        Context manager entry - Inicializa o Playwright e lança o navegador.
        
        Returns:
            Self para uso no bloco with
        """
        print("🚀 Iniciando navegador...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        print("✓ Navegador iniciado com sucesso")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - Fecha o navegador e para o Playwright.
        
        Args:
            exc_type: Tipo da exceção (se houver)
            exc_val: Valor da exceção (se houver)
            exc_tb: Traceback da exceção (se houver)
        """
        print("🔒 Fechando navegador...")
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("✓ Navegador fechado com sucesso")
    
    def close_popups(
        self, 
        page: Page, 
        tempo_espera: int = 2,
        seletores_customizados: Optional[List[str]] = None,
        timeout_por_seletor: int = 1000,
        mensagem_sucesso: str = "  ✓ Popup encontrado e fechado",
        mensagem_nao_encontrado: str = "  ℹ Nenhum popup detectado"
    ) -> bool:
        """
        Tenta identificar e fechar popups comuns na página de forma genérica.
        
        Args:
            page: Página do Playwright
            tempo_espera: Tempo de espera após fechar o popup (em segundos)
            seletores_customizados: Lista de seletores CSS personalizados para fechar popups
            timeout_por_seletor: Timeout em ms para verificar visibilidade de cada seletor
            mensagem_sucesso: Mensagem exibida quando popup é fechado
            mensagem_nao_encontrado: Mensagem exibida quando nenhum popup é encontrado
        
        Returns:
            True se um popup foi fechado, False caso contrário
        """
        popup_fechado = False
        
        # Define seletores padrão se nenhum customizado for fornecido
        seletores_fechar = seletores_customizados or [
            'button[aria-label*="close" i]',
            'button[aria-label*="fechar" i]',
            'button[aria-label*="dismiss" i]',
            '[class*="close" i]',
            '[class*="dismiss" i]',
            'button:has-text("×")',
            'button:has-text("Close")',
            'svg[aria-label="Close"]',
            'button:has(svg[aria-label="Close"])',
        ]
        
        print("🔍 Verificando popups...")
        
        for seletor in seletores_fechar:
            try:
                if page.locator(seletor).first.is_visible(timeout=timeout_por_seletor):
                    print(mensagem_sucesso)
                    page.locator(seletor).first.click()
                    popup_fechado = True
                    time.sleep(1)
                    break
            except:
                continue
        
        if popup_fechado:
            time.sleep(tempo_espera)
        else:
            print(mensagem_nao_encontrado)
        
        return popup_fechado
    
    def capturar_texto_rede_social(
        self, 
        url: str,
        tentar_ctrl_cv: bool = True
    ) -> str:
        """
        Acessa URL da rede social, fecha popups e captura todo o texto da página.
        Utiliza Ctrl+A e Ctrl+C para copiar o texto.
        
        Args:
            url: URL do post da rede social
            tentar_ctrl_cv: Se True, tenta capturar usando Ctrl+A/C/V
        
        Returns:
            String com o texto capturado da página
        """
        if not self.browser:
            raise RuntimeError("Scraper deve ser usado como context manager (use 'with')")
        
        print(f"🌐 Acessando URL: {url}")
        
        # Cria uma nova página com viewport configurado
        page = self.browser.new_page(
            viewport={'width': self.viewport_width, 'height': self.viewport_height}
        )
        
        try:
            # Navega para a URL
            print(f"📡 Navegando para: {url}")
            page.goto(url, wait_until=self.wait_until, timeout=self.timeout_navegacao)
            
            # Tenta fechar popups
            self.close_popups(page, tempo_espera=1)
            
            # Aguarda carregamento completo
            print(f"⏳ Aguardando carregamento completo ({self.tempo_carregamento}s)...")
            time.sleep(self.tempo_carregamento)
            
            texto_pagina = ""
            
            if tentar_ctrl_cv:
                # Seleciona todo o texto da página (Ctrl+A)
                print("📋 Selecionando todo o texto (Ctrl+A)...")
                page.keyboard.press('Control+A')
                time.sleep(1)
                
                # Copia o texto selecionado (Ctrl+C)
                print("📄 Copiando texto (Ctrl+C)...")
                page.keyboard.press('Control+C')
                time.sleep(1)
            
            # Captura o texto da página usando innerText
            # (clipboard pode não funcionar em headless)
            print("✂️ Extraindo texto da página...")
            texto_pagina = page.evaluate('document.body.innerText')
            
            print(f"✓ Texto capturado: {len(texto_pagina)} caracteres")
            
            return texto_pagina
            
        except Exception as e:
            print(f"✗ Erro ao capturar texto: {e}")
            import traceback
            traceback.print_exc()
            return ""
        
        finally:
            page.close()
    
    def salvar_json(
        self,
        texto_capturado: str,
        url: str,
        legenda: str = "",
        curtidas: Optional[int] = None,
        data_post: Optional[str] = None,
        autor: Optional[str] = None,
        arquivo: str = "post_capturado.json",
        comentarios: Optional[int] = None,
        retweets: Optional[int] = None,
        visualizacoes: Optional[int] = None
    ) -> Dict:
        """
        Salva o texto capturado em formato JSON com metadados do post.
        
        Args:
            texto_capturado: Texto completo capturado da página
            url: URL original do post
            legenda: Legenda/descrição do post
            curtidas: Quantidade de curtidas do post
            data_post: Data de publicação do post (ISO format)
            autor: Autor/username do post
            arquivo: Nome do arquivo JSON de saída
            comentarios: Quantidade de comentários do post
            retweets: Quantidade de retweets do post (Twitter/X)
            visualizacoes: Quantidade de visualizações do post (Twitter/X)
        
        Returns:
            Dicionário com os dados salvos
        """
        dados_post = {
            "url": url,
            "autor": autor,
            "legenda": legenda,
            "curtidas": curtidas,
            "comentarios": comentarios,
            "data_post": data_post,
            "data_extracao": datetime.now().isoformat()
        }
        
        # Adiciona retweets apenas se fornecido (específico do Twitter)
        if retweets is not None:
            dados_post["retweets"] = retweets
        
        # Adiciona visualizações apenas se fornecido (específico do Twitter)
        if visualizacoes is not None:
            dados_post["visualizacoes"] = visualizacoes
        
        try:
            # Cria a pasta posts_extraidos se não existir
            pasta_saida = "posts_extraidos"
            os.makedirs(pasta_saida, exist_ok=True)
            
            # Adiciona a pasta ao caminho do arquivo
            caminho_completo = os.path.join(pasta_saida, arquivo)
            
            with open(caminho_completo, 'w', encoding='utf-8') as f:
                json.dump(dados_post, f, ensure_ascii=False, indent=2)
            
            print(f"\n✓ Post salvo em: {os.path.abspath(caminho_completo)}")
            print(f"📊 Informações:")
            print(f"   - Autor: {autor or 'Não informado'}")
            print(f"   - Curtidas: {curtidas or 'Não informado'}")
            print(f"   - Comentários: {comentarios or 'Não informado'}")
            if retweets is not None:
                print(f"   - Retweets: {retweets or 'Não informado'}")
            if visualizacoes is not None:
                print(f"   - Visualizações: {visualizacoes or 'Não informado'}")
            print(f"   - Data: {data_post or 'Não informado'}")
            
            return dados_post
            
        except Exception as e:
            print(f"✗ Erro ao salvar JSON: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    @abstractmethod
    def extrair_dados_post(self, url: str) -> Dict[str, any]:
        """
        Extrai dados específicos do post da rede social.
        
        Args:
            url: URL do post
        
        Returns:
            Dicionário com autor, legenda, curtidas, data_post extraídos da página
        """
        pass
    
    @abstractmethod
    def processar_post(self, url: str, arquivo_saida: str = "post_capturado.json") -> Dict:
        """
        Processa um post completo: captura texto e extrai dados específicos.
        
        Args:
            url: URL do post
            arquivo_saida: Nome do arquivo JSON de saída
        
        Returns:
            Dicionário com todos os dados do post
        """
        pass
