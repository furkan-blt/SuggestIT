import io
import csv
import logging
from typing import List, Tuple
from app.schemas.models import TitleItem, SyncSummary

logger = logging.getLogger(__name__)

class CSVService:
    @classmethod
    def parse_imdb_csv(cls, file_content: str) -> List[TitleItem]:
        """IMDb tarafından dışa aktarılan ratings.csv veya watchlist.csv dosyasını ayrıştırır."""
        items: List[TitleItem] = []
        reader = csv.DictReader(io.StringIO(file_content))
        
        for row in reader:
            # Sütun isimleri bazen 'Const' bazen 'const' olabilir
            imdb_id = row.get("Const") or row.get("const") or row.get("IMDb ID")
            title = row.get("Title") or row.get("title") or "Bilinmeyen Başlık"
            
            # Yıl
            year_val = None
            raw_year = row.get("Year") or row.get("year")
            if raw_year and raw_year.isdigit():
                year_val = int(raw_year)

            # Kullanıcı puanı
            user_rating = None
            raw_rating = row.get("Your Rating") or row.get("your_rating")
            if raw_rating:
                try:
                    user_rating = float(raw_rating)
                except ValueError:
                    pass

            # Tür
            title_type = row.get("Title Type") or row.get("title_type") or "movie"

            # Genres
            genres = []
            raw_genres = row.get("Genres") or row.get("genres")
            if raw_genres:
                genres = [g.strip() for g in raw_genres.split(",") if g.strip()]

            # Directors
            directors = []
            raw_directors = row.get("Directors") or row.get("directors")
            if raw_directors:
                directors = [d.strip() for d in raw_directors.split(",") if d.strip()]

            items.append(TitleItem(
                imdb_id=imdb_id,
                title=title,
                year=year_val,
                title_type=title_type,
                user_rating=user_rating,
                genres=genres,
                directors=directors,
                date_added=row.get("Date Rated") or row.get("Created"),
                source="imdb_csv"
            ))

        return items

    @classmethod
    def parse_letterboxd_csv(cls, file_content: str, list_type: str = "ratings") -> List[TitleItem]:
        """Letterboxd export CSV dosyasını (ratings.csv, watched.csv, watchlist.csv) ayrıştırır."""
        items: List[TitleItem] = []
        reader = csv.DictReader(io.StringIO(file_content))

        for row in reader:
            title = row.get("Name") or row.get("name") or "Bilinmeyen Başlık"
            
            year_val = None
            raw_year = row.get("Year") or row.get("year")
            if raw_year and raw_year.isdigit():
                year_val = int(raw_year)

            # Letterboxd 5 üzerinden puan verir (0.5 - 5.0) -> IMDb uyumluluğu için 10'luk sisteme çarparız (* 2)
            user_rating = None
            raw_rating = row.get("Rating") or row.get("rating")
            if raw_rating:
                try:
                    user_rating = float(raw_rating) * 2.0
                except ValueError:
                    pass

            is_watchlist = (list_type == "watchlist")

            items.append(TitleItem(
                imdb_id=None,  # Letterboxd CSV'sinde IMDb ID bulunmaz, TMDB eşlemesiyle çözülecektir
                title=title,
                year=year_val,
                title_type="movie",
                user_rating=user_rating,
                in_watchlist=is_watchlist,
                date_added=row.get("Date"),
                source="letterboxd_csv"
            ))

        return items

    @classmethod
    def process_uploaded_csv(cls, file_content: str, platform: str = "auto") -> SyncSummary:
        """Yüklenen CSV dosyasının formatını otomatik anlayıp işler."""
        first_line = file_content.splitlines()[0].lower() if file_content else ""
        
        detected_platform = platform
        if platform == "auto":
            if "letterboxd" in first_line or ("name" in first_line and "letterboxd uri" in first_line):
                detected_platform = "letterboxd"
            else:
                detected_platform = "imdb"

        if detected_platform == "letterboxd":
            list_type = "watchlist" if "watchlist" in first_line else "ratings"
            items = cls.parse_letterboxd_csv(file_content, list_type)
        else:
            items = cls.parse_imdb_csv(file_content)

        movies_count = sum(1 for item in items if item.title_type in ["movie", "featureFilm", "tvMovie"])
        series_count = sum(1 for item in items if "tv" in (item.title_type or "").lower() or "series" in (item.title_type or "").lower())
        
        ratings_list = [item.user_rating for item in items if item.user_rating is not None]
        avg_rating = round(sum(ratings_list) / len(ratings_list), 2) if ratings_list else None

        return SyncSummary(
            status="success",
            platform=detected_platform,
            target="csv_import",
            total_items=len(items),
            movies_count=movies_count,
            series_count=series_count,
            avg_user_rating=avg_rating,
            items=items
        )
