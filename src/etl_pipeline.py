"""Pipeline ETL para processar notícias e alimentar o banco vetorial."""
import json
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import torch

from .vector_db import VectorDB
from .text_processing import process_noticia_to_chunks


class ETLPipeline:
    """Pipeline para extrair, transformar e carregar notícias no banco vetorial."""
    
    def __init__(self, model_name: str = "BAAI/bge-m3",
                 device: Optional[str] = None):
        """
        Inicializa o pipeline ETL.
        
        Args:
            model_name: Nome do modelo de embeddings
            device: Dispositivo ('cuda' ou 'cpu'). Se None, detecta automaticamente
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model: Optional[SentenceTransformer] = None
        self.dimension: Optional[int] = None
    
    def load_model(self):
        """Carrega o modelo de embeddings."""
        print(f"Carregando modelo '{self.model_name}' para o dispositivo '{self.device}'...")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        
        # Obtém a dimensão do modelo
        test_embedding = self.model.encode(["test"])
        self.dimension = len(test_embedding[0])
        print(f"Modelo carregado. Dimensão dos embeddings: {self.dimension}")
    
    def process_noticias(self, noticias: List[Dict[str, str]], 
                        table_name: str,
                        db_batch_size: int = 500,
                        encode_batch_size: int = 128):
        """
        Processa notícias: chunking, vetorização e inserção no banco.
        
        Args:
            noticias: Lista de notícias extraídas
            table_name: Nome da tabela no banco
            db_batch_size: Tamanho do lote para inserção no banco
            encode_batch_size: Tamanho do lote para vetorização
        """
        if not self.model:
            self.load_model()
        
        print(f"\nProcessando {len(noticias)} notícias...")
        
        # Gera chunks de todas as notícias
        all_chunks = []
        for noticia in noticias:
            chunks = process_noticia_to_chunks(noticia)
            all_chunks.extend(chunks)
        
        if not all_chunks:
            print("Nenhum chunk válido gerado.")
            return
        
        print(f"  |-> {len(all_chunks)} chunks gerados de {len(noticias)} notícias.")
        
        # Gera embeddings
        print(f"  |-> Gerando embeddings (Batch Size: {encode_batch_size})...")
        texts_to_embed = [chunk['chunk_text'] for chunk in all_chunks]
        
        embeddings = self.model.encode(
            texts_to_embed,
            show_progress_bar=True,
            batch_size=encode_batch_size
        )
        
        # Prepara dados para inserção
        data_for_db = []
        for i, chunk in enumerate(all_chunks):
            metadata = chunk.get('metadata', {})
            metadata.update({
                "document_id": chunk.get("document_id"),
                "chunk_index": chunk.get("chunk_index")
            })
            
            metadata_json = json.dumps(metadata, ensure_ascii=False)
            data_for_db.append(
                (chunk['chunk_text'], metadata_json, embeddings[i].tolist())
            )
        
        # Insere no banco
        print(f"  |-> Inserindo {len(data_for_db)} registros no banco de dados...")
        with VectorDB() as db:
            db.create_table(table_name, self.dimension)
            db.batch_insert(table_name, data_for_db, batch_size=db_batch_size)
        
        print(f"  |-> Processamento concluído!")

