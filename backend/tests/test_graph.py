import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.models import TitleItem
from app.services.graph_service import GraphService
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_complete_pattern_graph():
    titles = [
        TitleItem(title="Inception", year=2010, user_rating=9.5),
        TitleItem(title="Interstellar", year=2014, user_rating=9.0),
        TitleItem(title="The Dark Knight", year=2008, user_rating=10.0),
        TitleItem(title="Fight Club", year=1999, user_rating=8.5),
        TitleItem(title="Breaking Bad", year=2008, user_rating=10.0, title_type="tvSeries"),
        TitleItem(title="The Godfather", year=1972, user_rating=10.0),
        TitleItem(title="Kötü Film", year=2023, user_rating=3.0), # Düşük puanlı yapım
    ]

    graph = GraphService.generate_graph(titles)

    print("\n--- Pattern Tabanli Taste Network Graph Testi ---")
    print(f"Sinematik Arketip: {graph.archetype.title}")
    print(f"Toplam Dugum: {graph.total_nodes}")
    print(f"Toplam Baglanti: {graph.total_edges}")

    node_types = {n.type for n in graph.nodes}
    print(f"Ağdaki Düğüm Tipleri: {node_types}")

    # 1. 'Cinema' adında sahte bir düğüm asla olmamalı!
    labels = [n.label.lower() for n in graph.nodes]
    assert "cinema" not in labels, "HATA: Sahte 'Cinema' düğümü bulundu!"

    # 2. Tüm yapımlar ağda yer almalı (7 yapımın 7'si de dahil edilmeli)
    title_nodes = [n for n in graph.nodes if n.type == "title"]
    assert len(title_nodes) == len(titles), f"HATA: Bazı yapımlar elendi! Beklenen {len(titles)}, bulunan {len(title_nodes)}"

    # 3. Decade (Dönem) pattern'i ağda olmalı
    assert "decade" in node_types, "HATA: Dönem/Yıl pattern düğümü bulunamadı!"

    # 4. Format (Dizi) pattern'i ağda olmalı
    assert "format" in node_types, "HATA: Dizi format düğümü bulunamadı!"

    print("[OK] Tum yapimlarin eksiksiz temsili ve Cinema dugumunun kaldirildigi dogrulandi!")

def test_preview_endpoint():
    resp = client.get("/api/v1/graph/preview")
    assert resp.status_code == 200
    assert "Kapsamlı Zevk Haritası" in resp.text
    print("[OK] Preview sayfasi testi BASARILI!")

if __name__ == "__main__":
    print("Guncel Taste Graph Testleri Baslatiliyor...")
    test_complete_pattern_graph()
    test_preview_endpoint()
    print("\n[SUCCESS] Tum Testler Basariyla Gecti!")
