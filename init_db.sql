-- Script de inicialização do banco de dados
-- Este script é executado automaticamente pelo docker-compose
-- ou pode ser executado manualmente após conectar ao banco

-- Cria a extensão vector se ainda não existir
CREATE EXTENSION IF NOT EXISTS vector;

-- Verifica se a extensão foi criada
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

