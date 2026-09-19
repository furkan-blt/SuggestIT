import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.api.routes import generate_taste_graph, generate_recommendations
import asyncio

async def run_tests():
    print("--- V2 Taste Graph Test ---")
    mock_titles = [
        {
            "imdb_id": "tt123",
            "title": "Blade Runner 2049",
            "year": 2017,
            "title_type": "movie",
            "user_rating": 9,
            "genres": ["Sci-Fi", "Drama"],
            "directors": ["Denis Villeneuve"],
            "source": "mock"
        },
        {
            "imdb_id": "tt124",
            "title": "Arrival",
            "year": 2016,
            "title_type": "movie",
            "user_rating": 9,
            "genres": ["Sci-Fi", "Mystery"],
            "directors": ["Denis Villeneuve"],
            "source": "mock"
        },
        {
            "imdb_id": "tt125",
            "title": "The Godfather",
            "year": 1972,
            "title_type": "movie",
            "user_rating": 10,
            "genres": ["Crime", "Drama"],
            "directors": ["Francis Ford Coppola"],
            "source": "mock"
        },
        {
            "imdb_id": "tt126",
            "title": "Just Go with It",
            "year": 2011,
            "title_type": "movie",
            "user_rating": 3,
            "genres": ["Comedy", "Romance"],
            "directors": ["Dennis Dugan"],
            "source": "mock"
        }
    ]

    graph = await generate_taste_graph(mock_titles)
    print(f"Toplam Düğüm (Nodes): {graph.total_nodes}")
    print(f"Toplam Bağlantı (Edges): {graph.total_edges}")
    print(f"Baskın Arketip Başlığı: {graph.archetype.title}")
    
    print("\n--- V2 AI Recommender Test ---")
    recs = await generate_recommendations(mock_titles)
    print(f"Önerilen Sayısı: {len(recs['recommendations'])}")
    for i, rec in enumerate(recs['recommendations']):
        print(f"{i+1}. {rec['title']} (Skor: {rec['score']}) - {rec['reason']}")

    print("\n[SUCCESS] AI Motoru ve V2 Graph basariyla calisiyor!")

if __name__ == "__main__":
    asyncio.run(run_tests())
