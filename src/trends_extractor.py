"""Módulo para extrair tendências do Google Trends."""
import time
import re
from typing import List, Optional
from playwright.sync_api import sync_playwright, Browser, Page


class GoogleTrendsExtractor:
    """Extrator de tendências do Google Trends."""
    
    def __init__(self, headless: bool = True):
        """
        Inicializa o extrator.
        
        Args:
            headless: Se True, executa o navegador em modo headless
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
    
    def __enter__(self):
        """Context manager entry."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.browser:
            self.browser.close()
        if hasattr(self, 'playwright'):
            self.playwright.stop()
    
    def gerar_url_trends(self, geo: str = "BR", hl: str = "pt-BR", 
                        hours: int = 168, category: int = 14) -> str:
        """
        Gera a URL do Google Trends parametrizada.
        
        Args:
            geo: Código do país (ex: 'BR', 'US')
            hl: Idioma da página (ex: 'pt-BR', 'en-US')
            hours: Últimas N horas (ex: 24, 168)
            category: Categoria de tendência (0 = Todas, 14 = Política, 10 = Legislação)
        
        Returns:
            URL completa como string
        """
        url = f"https://trends.google.com.br/trending?geo={geo}&hl={hl}&hours={hours}&category={category}"
        return url
    
    def extrair_tendencias(self, geo: str = "BR", hl: str = "pt-BR",
                          hours: int = 168, category: int = 14,
                          timeout: int = 30000) -> List[str]:
        """
        Extrai tendências do Google Trends.
        
        Args:
            geo: Código do país
            hl: Idioma da página
            hours: Últimas N horas
            category: Categoria de tendência
            timeout: Timeout em milissegundos
        
        Returns:
            Lista de palavras-chave/tendências
        """
        if not self.browser:
            raise RuntimeError("Extractor deve ser usado como context manager")
        
        url = self.gerar_url_trends(geo, hl, hours, category)
        page = self.browser.new_page()
        
        try:
            print(f"Acessando Google Trends: {url}")
            page.goto(url, wait_until="load", timeout=timeout)
            
            # Aguarda a tabela carregar - tenta múltiplos seletores possíveis
            try:
                page.wait_for_selector("table", timeout=timeout)
            except:
                # Tenta seletores alternativos
                try:
                    page.wait_for_selector(".enOdEe-wZVHld-zg7Cn", timeout=5000)
                except:
                    page.wait_for_selector("[role='table']", timeout=5000)
            
            time.sleep(3)  # Pausa para garantir carregamento completo
            
            # Extrai dados da coluna de tendências (coluna 2, índice 1)
            tendencias_raw = page.evaluate("""
                () => {
                    // Tenta múltiplos seletores
                    let tabela = document.querySelector('.enOdEe-wZVHld-zg7Cn');
                    if (!tabela) {
                        tabela = document.querySelector('table');
                    }
                    if (!tabela) {
                        tabela = document.querySelector('[role="table"]');
                    }
                    if (!tabela) return [];
                    
                    const linhas = tabela.querySelectorAll('tr');
                    const dados = [];
                    
                    // Pula o cabeçalho (índice 0) e processa as linhas
                    for (let i = 1; i < linhas.length; i++) {
                        const celulas = linhas[i].querySelectorAll('td');
                        if (celulas.length >= 2) {
                            // Coluna 2 (índice 1) contém o termo de tendência
                            const texto = celulas[1].textContent.trim();
                            if (texto && texto.length > 0) {
                                dados.push(texto);
                            }
                        }
                    }
                    
                    return dados;
                }
            """)
            
            # Limpa as tendências para extrair apenas o termo principal
            tendencias_limpas = self._limpar_tendencias(tendencias_raw if tendencias_raw else [])
            
            print(f"Encontradas {len(tendencias_limpas)} tendências.")
            return tendencias_limpas
            
        except Exception as e:
            print(f"Erro ao extrair tendências: {e}")
            return []
        finally:
            page.close()
    
    def _limpar_tendencias(self, tendencias_raw: List[str]) -> List[str]:
        """
        Limpa as tendências extraídas para obter apenas o termo principal.
        
        Remove informações como "100 mil+ pesquisas", "trending_up", "Ativa", etc.
        
        Args:
            tendencias_raw: Lista de tendências com informações extras
        
        Returns:
            Lista de termos limpos
        """
        tendencias_limpas = []
        
        for trend in tendencias_raw:
            if not trend:
                continue
            
            # Exemplo: "renato freitas100 mil+ pesquisas·trending_upAtiva·anteontem"
            # Queremos extrair apenas: "renato freitas"
            
            # Remove tudo a partir do primeiro número seguido de espaço ou "mil"
            # Isso captura padrões como "100 mil+", "20 mil+", "200+", etc.
            cleaned = re.sub(r'\d+\s*(mil\+|mil|milhões\+|milhões|pesquisas|pesquisa).*', '', trend, flags=re.IGNORECASE)
            
            # Se ainda tiver símbolos · ou •, remove tudo após eles
            if '·' in cleaned:
                cleaned = cleaned.split('·')[0]
            if '•' in cleaned:
                cleaned = cleaned.split('•')[0]
            
            # Remove palavras comuns de status que podem estar grudadas
            cleaned = re.sub(r'(trending_up|trending_down|Ativa|Inativa|timelapse|Durou|há).*', '', cleaned, flags=re.IGNORECASE)
            
            # Remove espaços extras e limpa
            cleaned = cleaned.strip()
            
            # Se ainda tiver conteúdo válido (mais de 2 caracteres), adiciona
            if cleaned and len(cleaned) > 2:
                tendencias_limpas.append(cleaned)
        
        return tendencias_limpas
    
    def extrair_tendencias_politicas(self, hours: int = 168) -> List[str]:
        """
        Extrai tendências políticas do Google Trends (categoria 14).
        
        Args:
            hours: Últimas N horas (padrão: 168 = 7 dias)
        
        Returns:
            Lista de palavras-chave políticas
        """
        return self.extrair_tendencias(
            geo="BR",
            hl="pt-BR",
            hours=hours,
            category=14  # Categoria: Política
        )

