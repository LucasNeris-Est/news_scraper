-- Migração: Adiciona campo 'trend' à tabela post_analyses
-- Execute este script se você já tem um banco de dados existente

-- Adiciona coluna 'trend' se ela não existir
ALTER TABLE post_analyses 
ADD COLUMN IF NOT EXISTS trend VARCHAR(100);

-- Comentário na coluna
COMMENT ON COLUMN post_analyses.trend IS 'Tendência ou categoria do post (ex: politics, health, technology)';

