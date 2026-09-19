import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "SuggestIT Core API"
    print("[OK] /api/v1/health endpoint testi BASARILI!")

def test_csv_upload_endpoint():
    sample_csv = "Const,Your Rating,Title,Title Type\ntt0111161,10,The Shawshank Redemption,movie\n"
    files = {"file": ("test.csv", sample_csv, "text/csv")}
    response = client.post("/api/v1/import/csv", files=files, data={"platform": "imdb"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_items"] == 1
    assert data["items"][0]["title"] == "The Shawshank Redemption"
    assert data["items"][0]["user_rating"] == 10.0
    print("[OK] /api/v1/import/csv endpoint testi BASARILI!")

if __name__ == "__main__":
    print("FastAPI Endpoint Testleri Baslatiliyor...")
    test_health()
    test_csv_upload_endpoint()
    print("\n[SUCCESS] Tum API Uç Nokta Testleri Kusursuz Gecti!")
