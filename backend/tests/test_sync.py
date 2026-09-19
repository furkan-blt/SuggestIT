import sys
import os

# App dizinini Python yoluna ekle
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.csv_service import CSVService
from app.services.imdb_service import IMDbService

def test_imdb_csv():
    sample_csv = """Const,Your Rating,Date Rated,Title,URL,Title Type,IMDb Rating,Runtime (mins),Year,Genres,Num Votes,Release Date,Directors
tt0111161,10,2024-01-15,The Shawshank Redemption,https://www.imdb.com/title/tt0111161/,movie,9.3,142,1994,"Drama",2900000,1994-10-14,"Frank Darabont"
tt0468569,9,2024-02-10,The Dark Knight,https://www.imdb.com/title/tt0468569/,movie,9.0,152,2008,"Action, Crime, Drama",2900000,2008-07-18,"Christopher Nolan"
tt0903747,10,2024-03-01,Breaking Bad,https://www.imdb.com/title/tt0903747/,tvSeries,9.5,49,2008,"Crime, Drama, Thriller",2200000,2008-01-20,"Vince Gilligan"
"""
    summary = CSVService.process_uploaded_csv(sample_csv, platform="imdb")
    print("\n--- IMDb CSV Testi Sonucu ---")
    print(f"Toplam Yapım: {summary.total_items}")
    print(f"Film Sayısı: {summary.movies_count}")
    print(f"Dizi Sayısı: {summary.series_count}")
    print(f"Ortalama Puan: {summary.avg_user_rating}")
    assert summary.total_items == 3
    assert summary.movies_count == 2
    assert summary.series_count == 1
    assert summary.avg_user_rating == 9.67
    print("[OK] IMDb CSV ayristirmasi BASARILI!")

def test_letterboxd_csv():
    sample_lb_csv = """Date,Name,Year,Letterboxd URI,Rating
2024-01-10,Inception,2010,https://boxd.it/1sz2,4.5
2024-01-12,Interstellar,2014,https://boxd.it/336K,5.0
2024-01-15,Tenet,2020,https://boxd.it/l76s,3.5
"""
    summary = CSVService.process_uploaded_csv(sample_lb_csv, platform="letterboxd")
    print("\n--- Letterboxd CSV Testi Sonucu ---")
    print(f"Toplam Yapim: {summary.total_items}")
    print(f"Ortalama Puan (10 uzerinden): {summary.avg_user_rating}")
    assert summary.total_items == 3
    # 4.5*2=9.0, 5.0*2=10.0, 3.5*2=7.0 -> ort: 26/3 = 8.67
    assert summary.avg_user_rating == 8.67
    print("[OK] Letterboxd CSV ayristirmasi BASARILI!")

def test_imdb_url_normalization():
    url, target = IMDbService.normalize_imdb_url("ur12345678", "ratings")
    assert url == "https://www.imdb.com/user/ur12345678/ratings/"
    assert target == "ratings"
    
    url2, target2 = IMDbService.normalize_imdb_url("https://www.imdb.com/user/ur87654321/watchlist/", "auto")
    assert target2 == "watchlist"
    print("[OK] IMDb URL normalizasyonu BASARILI!")

if __name__ == "__main__":
    print("SuggestIT Backend Testleri Baslatiliyor...")
    test_imdb_csv()
    test_letterboxd_csv()
    test_imdb_url_normalization()
    print("\n[SUCCESS] Tum Faz 1 Cekirdek Testleri Basariyla Gecti!")

