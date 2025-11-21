"""Exemplo de uso do scraper de notícias com vetorização."""
from src.scrapers.g1_scraper import G1Scraper
from src.etl_pipeline import ETLPipeline


def exemplo_basico():
    """Exemplo básico de uso."""
    palavras_chave = "tecnologia"
    limite = 5
    
    print(f"Buscando notícias com palavras-chave: {palavras_chave}")
    
    # Extrai notícias
    with G1Scraper(headless=True) as scraper:
        noticias = scraper.buscar_e_extrair(palavras_chave, limite=limite)
    
    if not noticias:
        print("Nenhuma notícia encontrada.")
        return
    
    print(f"\n{len(noticias)} notícias extraídas.")
    
    # Opcional: salvar em JSON
    scraper.salvar_json(noticias, "noticias_g1.json")
    
    # Processa e insere no banco vetorial
    pipeline = ETLPipeline(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    pipeline.process_noticias(
        noticias,
        table_name="noticias_g1",
        db_batch_size=500,
        encode_batch_size=128
    )


if __name__ == "__main__":
    exemplo_basico()

