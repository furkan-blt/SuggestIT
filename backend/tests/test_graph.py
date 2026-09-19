import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.models import TitleItem
from app.services.graph_service import GraphService
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_graph_service_generation():
    titles = [
        TitleItem(title="Inception", year=2010, user_rating=9.5),
        TitleItem(title="Interstellar", year=2014, user_rating=9.0),
        TitleItem(title="The Dark Knight", year=2008, user_rating=10.0),
        TitleItem(title="Fight Club", year=1999, user_rating=8.5),
        TitleItem(title="Se7en", year=1995, user_rating=9.0),
        TitleItem(title="Breaking Bad", year=2008, user_rating=10.0, title_type="tvSeries"),
    ]

    graph = GraphService.generate_graph(titles)

    print("\n--- Taste Network Graph Testi ---")
    print(f"Sinematik Arketip: {graph.archetype.title}")
    print(f"Slogan: {graph.archetype.tagline}")
    print(f"Baskin Turler: {graph.archetype.dominant_genres}")
    print(f"Toplam Dugum (Nodes): {graph.total_nodes}")
    print(f"Toplam Baglanti (Edges): {graph.total_edges}")

    assert graph.total_nodes > 0
    assert graph.total_edges > 0
    assert graph.archetype.title != ""
    assert len(graph.archetype.dominant_genres) > 0
    print("[OK] GraphService veri uretim testi BASARILI!")

def test_graph_endpoints():
    # 1. Preview HTML uç noktası
    html_resp = client.get("/api/v1/graph/preview")
    assert html_resp.status_code == 200
    assert "SuggestIT - Taste Network Graph" in html_resp.text
    print("[OK] /api/v1/graph/preview HTML arayuzu testi BASARILI!")

    # 2. Graph generate API uç noktası
    payload = [
        {"title": "Inception", "year": 2010, "user_rating": 9.5},
        {"title": "Dune", "year": 2021, "user_rating": 9.0}
    ]
    api_resp = client.post("/api/v1/graph/generate", json=payload)
    assert api_resp.status_code == 200
    data = api_resp.json()
    assert "archetype" in data
    assert len(data["nodes"]) > 0
    print("[OK] /api/v1/graph/generate API testi BASARILI!")

if __name__ == "__main__":
    print("Taste Network Graph Testleri Baslatiliyor...")
    test_graph_service_generation()
    test_graph_endpoints()
    print("\n[SUCCESS] Tum Faz 2 Taste Graph Testleri Kusursuz Gecti!")
