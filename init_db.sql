-- Script de inicialização do banco de dados
-- Este script é executado automaticamente pelo docker-compose
-- ou pode ser executado manualmente após conectar ao banco

-- Cria a extensão vector se ainda não existir
CREATE EXTENSION IF NOT EXISTS vector;

-- Verifica se a extensão foi criada
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Cria tabela para armazenar análises de posts
CREATE TABLE IF NOT EXISTS post_analyses (
    id SERIAL PRIMARY KEY,
    post_hash VARCHAR(64) UNIQUE NOT NULL,
    post_text TEXT NOT NULL,
    post_metadata JSONB,
    image_description TEXT,
    social_network VARCHAR(50),
    trend VARCHAR(100),
    risk_level VARCHAR(20) NOT NULL,
    risk_score DECIMAL(5,3) NOT NULL,
    bert_score DECIMAL(5,3) NOT NULL,
    confidence DECIMAL(5,3) NOT NULL,
    reasoning TEXT NOT NULL,
    relevant_sources JSONB,
    factors JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índice para busca rápida por hash
CREATE INDEX IF NOT EXISTS idx_post_hash ON post_analyses(post_hash);

-- Índice para busca por data
CREATE INDEX IF NOT EXISTS idx_created_at ON post_analyses(created_at);

-- Índice para busca por nível de risco
CREATE INDEX IF NOT EXISTS idx_risk_level ON post_analyses(risk_level);

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para atualizar updated_at
CREATE TRIGGER update_post_analyses_updated_at 
    BEFORE UPDATE ON post_analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

