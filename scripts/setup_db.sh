#!/bin/bash
# Script para configurar o banco de dados

echo "🚀 Iniciando container PostgreSQL com PGVector..."
docker-compose up -d

echo "⏳ Aguardando banco de dados ficar pronto..."
sleep 5

echo "✅ Verificando conexão..."
docker-compose exec -T postgres psql -U postgres -d news_db -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

echo "✅ Banco de dados configurado e pronto para uso!"

