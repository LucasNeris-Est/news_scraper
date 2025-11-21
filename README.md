# Scraper de Notícias com Vetorização

Sistema modular para extrair notícias de diferentes sites, processá-las em chunks e armazená-las em um banco vetorial PostgreSQL com PGVector.

## Estrutura do Projeto

```
src/
├── news_scraper.py      # Classe base abstrata para scrapers
├── scrapers/
│   ├── __init__.py
│   └── g1_scraper.py    # Scraper específico para G1
├── text_processing.py   # Funções de chunking e limpeza de texto
├── vector_db.py         # Integração com PostgreSQL + PGVector
├── etl_pipeline.py      # Pipeline ETL completo
└── main.py              # Script principal CLI
```

## Instalação

### Opção 1: Usando Docker (Recomendado)

1. Instale as dependências:
```bash
pip install -e .
```

2. Configure as variáveis de ambiente criando um arquivo `.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME_POSTGRES=news_db
DB_USER=postgres
DB_PASS=postgres
```

3. Inicie o container PostgreSQL com PGVector:

**Linux/Mac:**
```bash
chmod +x scripts/setup_db.sh
./scripts/setup_db.sh
```

**Windows (PowerShell):**
```powershell
.\scripts\setup_db.ps1
```

**Ou manualmente:**
```bash
docker-compose up -d
```

O container já vem com a extensão `vector` pré-instalada e será criada automaticamente na inicialização.

4. Verifique se o container está rodando:
```bash
docker-compose ps
```

### Opção 2: Instalação Manual

1. Instale as dependências:
```bash
pip install -e .
```

2. Configure as variáveis de ambiente criando um arquivo `.env`:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME_POSTGRES=seu_banco
DB_USER=seu_usuario
DB_PASS=sua_senha
```

3. Instale PostgreSQL e a extensão PGVector manualmente, depois execute:
```sql
CREATE EXTENSION vector;
```

## Uso Básico

### Via Script Python

```python
from src.scrapers.g1_scraper import G1Scraper
from src.etl_pipeline import ETLPipeline

# Extrai notícias
with G1Scraper(headless=True) as scraper:
    noticias = scraper.buscar_e_extrair("tecnologia", limite=5)

# Processa e insere no banco vetorial
pipeline = ETLPipeline(model_name="sentence-transformers/all-MiniLM-L6-v2")
pipeline.process_noticias(noticias, table_name="noticias_g1")
```

### Via CLI

```bash
python -m src.main --palavras-chave "tecnologia" --limite 5 --tabela noticias_g1
```

## Adicionando Novos Scrapers

Para adicionar um novo site, crie uma classe que herda de `NewsScraper`:

```python
from src.news_scraper import NewsScraper

class MeuSiteScraper(NewsScraper):
    def buscar_links(self, palavras_chave: str, limite: int = 5) -> List[str]:
        # Implemente a busca de links
        pass
    
    def extrair_conteudo(self, url: str) -> Dict[str, str]:
        # Implemente a extração de conteúdo
        pass
```

## Modelos de Embeddings

O sistema suporta qualquer modelo do Sentence Transformers. Exemplos:

- `sentence-transformers/all-MiniLM-L6-v2` (384 dimensões, rápido)
- `sentence-transformers/LaBSE` (768 dimensões, multilíngue)
- `BAAI/bge-m3` (1024 dimensões, avançado)

## Estrutura do Banco de Dados

Cada tabela criada tem a seguinte estrutura:

```sql
CREATE TABLE nome_tabela (
    id SERIAL PRIMARY KEY,
    document TEXT,
    metadata JSONB,
    embedding VECTOR(dimension)
);
```

O campo `metadata` contém informações como título, autor, data, link, etc.

## Docker

### Comandos Úteis

**Iniciar o banco de dados:**
```bash
docker-compose up -d
```

**Parar o banco de dados:**
```bash
docker-compose down
```

**Parar e remover volumes (apaga os dados):**
```bash
docker-compose down -v
```

**Ver logs:**
```bash
docker-compose logs -f postgres
```

**Acessar o banco via psql:**
```bash
docker-compose exec postgres psql -U postgres -d news_db
```

**Verificar se a extensão vector está instalada:**
```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

