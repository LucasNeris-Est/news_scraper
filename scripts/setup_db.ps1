# Script PowerShell para configurar o banco de dados

Write-Host "🚀 Iniciando container PostgreSQL com PGVector..." -ForegroundColor Green
docker-compose up -d

Write-Host "⏳ Aguardando banco de dados ficar pronto..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "✅ Verificando conexão..." -ForegroundColor Cyan
docker-compose exec -T postgres psql -U postgres -d news_db -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"

Write-Host "✅ Banco de dados configurado e pronto para uso!" -ForegroundColor Green

