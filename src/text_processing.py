"""Funções para processamento e chunking de texto."""
import re
import unicodedata
from typing import List, Dict
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter


def slugify_column_name(name: str) -> str:
    """Limpa e padroniza um nome de coluna para ser seguro para SQL."""
    if not name:
        return "coluna_desconhecida"
    
    text = unicodedata.normalize('NFD', str(name)).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '_', text).strip('_')
    
    if not text:
        return "coluna_desconhecida"
    
    return text


def parse_and_clean_html_content(content_soup: BeautifulSoup) -> str:
    """Extrai texto puro de um objeto BeautifulSoup, removendo tags indesejadas."""
    if not content_soup:
        return ""
    
    for tag in content_soup(['script', 'style', 'a', 'img']):
        tag.decompose()
    
    for p in content_soup.find_all('p'):
        p.replace_with(p.get_text() + '\n')
    
    cleaned_text = content_soup.get_text(separator=' ', strip=True)
    return cleaned_text.replace('\n ', '\n').replace(' \n', '\n')


def clean_text(text: str) -> str:
    """Aplica limpeza final em textos para remover ruídos comuns."""
    if not text:
        return ""
    
    text = re.sub(r'^\s*[\.]{5,}\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'\.{5,}', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def chunk_recursive_langchain(raw_text: str, document_id: str, **kwargs) -> List[Dict]:
    """
    Divide o texto usando o RecursiveCharacterTextSplitter da LangChain.
    
    Args:
        raw_text: Texto a ser dividido
        document_id: Identificador do documento original
        **kwargs: Argumentos adicionais (chunk_size, chunk_overlap)
    
    Returns:
        Lista de dicionários com os chunks
    """
    chunk_size = kwargs.get('chunk_size', 600)
    chunk_overlap = kwargs.get('chunk_overlap', 60)
    
    splitter = RecursiveCharacterTextSplitter(
        separators=[
            "\n\n",
            "\n",
            ". ",
            ";",
            ",",
            " "
        ],
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False
    )
    
    chunks_text = splitter.split_text(raw_text)
    final_chunks = []
    
    for i, chunk in enumerate(chunks_text):
        if len(chunk.strip()) > 50:
            final_chunks.append({
                "document_id": document_id,
                "chunk_index": i,
                "chunk_text": chunk.strip()
            })
    
    return final_chunks


def process_noticia_to_chunks(noticia: Dict[str, str]) -> List[Dict]:
    """
    Processa uma notícia e retorna seus chunks.
    
    Args:
        noticia: Dicionário com os dados da notícia
    
    Returns:
        Lista de chunks com metadados
    """
    # Combina título, subtítulo e conteúdo
    partes = []
    if noticia.get('titulo'):
        partes.append(noticia['titulo'])
    if noticia.get('subtitulo'):
        partes.append(noticia['subtitulo'])
    if noticia.get('conteudo'):
        partes.append(noticia['conteudo'])
    
    texto_completo = "\n\n".join(partes)
    texto_completo = clean_text(texto_completo)
    
    if not texto_completo:
        return []
    
    document_id = noticia.get('link', 'unknown')
    chunks = chunk_recursive_langchain(texto_completo, document_id)
    
    # Adiciona metadados da notícia a cada chunk
    for chunk in chunks:
        chunk['metadata'] = {
            "titulo": noticia.get('titulo'),
            "subtitulo": noticia.get('subtitulo'),
            "autor": noticia.get('autor'),
            "data": noticia.get('data'),
            "link": noticia.get('link'),
            "data_extracao": noticia.get('data_extracao')
        }
    
    return chunks

