"""Módulo para integração com PostgreSQL e PGVector."""
import os
import json
from typing import List, Tuple, Optional
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()


class VectorDB:
    """Classe para gerenciar conexão e operações com PostgreSQL + PGVector."""
    
    def __init__(self, host: Optional[str] = None, port: Optional[str] = None,
                 database: Optional[str] = None, user: Optional[str] = None,
                 password: Optional[str] = None):
        """
        Inicializa a conexão com o banco de dados.
        
        Args:
            host: Host do PostgreSQL (ou usa DB_HOST do .env)
            port: Porta do PostgreSQL (ou usa DB_PORT do .env)
            database: Nome do banco (ou usa DB_NAME_POSTGRES do .env)
            user: Usuário (ou usa DB_USER do .env)
            password: Senha (ou usa DB_PASS do .env)
        """
        self.host = host or os.getenv("DB_HOST")
        self.port = port or os.getenv("DB_PORT")
        self.database = database or os.getenv("DB_NAME_POSTGRES")
        self.user = user or os.getenv("DB_USER")
        self.password = password or os.getenv("DB_PASS")
        self.conn: Optional[psycopg2.extensions.connection] = None
    
    def connect(self):
        """Estabelece conexão com o banco de dados."""
        try:
            self.conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            print(f"Conexão com PostgreSQL ({self.host}:{self.port}) bem-sucedida.")
        except psycopg2.OperationalError as e:
            print(f"Erro ao conectar ao PostgreSQL: {e}")
            raise
    
    def close(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def create_table(self, table_name: str, dimension: int):
        """
        Cria uma tabela com suporte a vetores.
        
        Args:
            table_name: Nome da tabela
            dimension: Dimensão dos vetores
        """
        if not self.conn:
            raise RuntimeError("Conexão não estabelecida. Chame connect() primeiro.")
        
        with self.conn.cursor() as cursor:
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            create_table_sql = sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
                    id SERIAL PRIMARY KEY,
                    document TEXT,
                    metadata JSONB,
                    embedding VECTOR({})
                );
            """).format(
                sql.Identifier(table_name),
                sql.Literal(dimension)
            )
            
            cursor.execute(create_table_sql)
            self.conn.commit()
            print(f"Tabela '{table_name}' criada com sucesso.")
    
    def get_existing_links(self, table_name: str) -> set:
        """
        Retorna um conjunto com todos os links já existentes na tabela.
        
        Args:
            table_name: Nome da tabela
        
        Returns:
            Conjunto de links (URLs) já existentes
        """
        if not self.conn:
            raise RuntimeError("Conexão não estabelecida.")
        
        try:
            with self.conn.cursor() as cursor:
                # Verifica se a tabela existe
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = %s
                    );
                """, (table_name,))
                
                if not cursor.fetchone()[0]:
                    return set()
                
                # Busca todos os links únicos no metadata
                cursor.execute(sql.SQL("""
                    SELECT DISTINCT metadata->>'link' 
                    FROM {} 
                    WHERE metadata->>'link' IS NOT NULL
                """).format(sql.Identifier(table_name)))
                
                links = {row[0] for row in cursor.fetchall() if row[0]}
                return links
        except Exception as e:
            print(f"  Erro ao buscar links existentes: {e}")
            return set()
    
    def batch_insert(self, table_name: str, data: List[Tuple[str, str, List[float]]], 
                     batch_size: int = 500, skip_duplicates: bool = True):
        """
        Insere dados em lote no banco, verificando duplicatas por link.
        
        Args:
            table_name: Nome da tabela
            data: Lista de tuplas (document, metadata_json, embedding)
            batch_size: Tamanho do lote para inserção
            skip_duplicates: Se True, pula registros com links já existentes
        """
        if not self.conn:
            raise RuntimeError("Conexão não estabelecida.")
        
        if not data:
            return
        
        # Filtra duplicatas se solicitado
        if skip_duplicates:
            existing_links = self.get_existing_links(table_name)
            filtered_data = []
            skipped = 0
            
            for item in data:
                try:
                    metadata = json.loads(item[1])
                    link = metadata.get('link')
                    
                    if link and link in existing_links:
                        skipped += 1
                        continue
                    
                    filtered_data.append(item)
                except (json.JSONDecodeError, KeyError):
                    # Se não conseguir parsear o metadata, insere mesmo assim
                    filtered_data.append(item)
            
            if skipped > 0:
                print(f"  |-> {skipped} registros pulados (links já existentes).")
            
            data = filtered_data
        
        if not data:
            print(f"  |-> Nenhum registro novo para inserir.")
            return
        
        insert_sql = sql.SQL("""
            INSERT INTO {} (document, metadata, embedding) 
            VALUES %s
        """).format(sql.Identifier(table_name))
        
        total_inserted = 0
        
        try:
            with self.conn.cursor() as cursor:
                for i in range(0, len(data), batch_size):
                    batch = data[i:i + batch_size]
                    execute_values(cursor, insert_sql, batch)
                    total_inserted += len(batch)
            
            self.conn.commit()
            print(f"  |-> {total_inserted} registros inseridos na tabela '{table_name}'.")
        except Exception as e:
            print(f"  Erro na inserção em lote: {e}")
            self.conn.rollback()
            raise
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

