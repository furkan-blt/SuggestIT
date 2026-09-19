import os
import re
import logging
from typing import Dict, List, Optional, Tuple
import requests

from app.schemas.models import TitleItem

logger = logging.getLogger(__name__)

# Popüler yapımlar için akıllı yerel metadata sözlüğü (Offline ve API anahtarsız çalışma desteği)
CURATED_METADATA: Dict[str, Dict[str, List[str]]] = {
    "inception": {"genres": ["Sci-Fi", "Action", "Thriller"], "directors": ["Christopher Nolan"]},
    "interstellar": {"genres": ["Sci-Fi", "Drama", "Adventure"], "directors": ["Christopher Nolan"]},
    "the dark knight": {"genres": ["Action", "Crime", "Drama"], "directors": ["Christopher Nolan"]},
    "oppenheimer": {"genres": ["Biography", "Drama", "History"], "directors": ["Christopher Nolan"]},
    "tenet": {"genres": ["Sci-Fi", "Action", "Thriller"], "directors": ["Christopher Nolan"]},
    "dunkirk": {"genres": ["War", "Action", "Drama"], "directors": ["Christopher Nolan"]},
    "memento": {"genres": ["Mystery", "Thriller"], "directors": ["Christopher Nolan"]},
    "prestige": {"genres": ["Drama", "Mystery", "Sci-Fi"], "directors": ["Christopher Nolan"]},
    "the prestige": {"genres": ["Drama", "Mystery", "Sci-Fi"], "directors": ["Christopher Nolan"]},
    "fight club": {"genres": ["Drama", "Thriller"], "directors": ["David Fincher"]},
    "se7en": {"genres": ["Crime", "Drama", "Mystery"], "directors": ["David Fincher"]},
    "seven": {"genres": ["Crime", "Drama", "Mystery"], "directors": ["David Fincher"]},
    "zodiac": {"genres": ["Crime", "Drama", "Mystery"], "directors": ["David Fincher"]},
    "the social network": {"genres": ["Biography", "Drama"], "directors": ["David Fincher"]},
    "gone girl": {"genres": ["Drama", "Mystery", "Thriller"], "directors": ["David Fincher"]},
    "pulp fiction": {"genres": ["Crime", "Drama"], "directors": ["Quentin Tarantino"]},
    "kill bill": {"genres": ["Action", "Crime"], "directors": ["Quentin Tarantino"]},
    "inglourious basterds": {"genres": ["Adventure", "Drama", "War"], "directors": ["Quentin Tarantino"]},
    "django unchained": {"genres": ["Drama", "Western"], "directors": ["Quentin Tarantino"]},
    "dune": {"genres": ["Sci-Fi", "Adventure", "Action"], "directors": ["Denis Villeneuve"]},
    "dune: part two": {"genres": ["Sci-Fi", "Adventure", "Action"], "directors": ["Denis Villeneuve"]},
    "blade runner 2049": {"genres": ["Sci-Fi", "Mystery", "Drama"], "directors": ["Denis Villeneuve"]},
    "arrival": {"genres": ["Sci-Fi", "Drama", "Mystery"], "directors": ["Denis Villeneuve"]},
    "sicario": {"genres": ["Action", "Crime", "Drama"], "directors": ["Denis Villeneuve"]},
    "prisoners": {"genres": ["Crime", "Drama", "Mystery"], "directors": ["Denis Villeneuve"]},
    "the matrix": {"genres": ["Sci-Fi", "Action"], "directors": ["Lana Wachowski", "Lilly Wachowski"]},
    "parasite": {"genres": ["Drama", "Thriller", "Comedy"], "directors": ["Bong Joon-ho"]},
    "the shawshank redemption": {"genres": ["Drama"], "directors": ["Frank Darabont"]},
    "the godfather": {"genres": ["Crime", "Drama"], "directors": ["Francis Ford Coppola"]},
    "breaking bad": {"genres": ["Crime", "Drama", "Thriller"], "directors": ["Vince Gilligan"]},
    "better call saul": {"genres": ["Crime", "Drama"], "directors": ["Vince Gilligan", "Peter Gould"]},
    "materialists": {"genres": ["Romance", "Comedy"], "directors": ["Celine Song"]},
    "cold war": {"genres": ["Drama", "Music", "Romance"], "directors": ["Pawel Pawlikowski"]},
}

class TMDBService:
    API_KEY: Optional[str] = os.getenv("TMDB_API_KEY")
    BASE_URL: str = "https://api.themoviedb.org/3"
    _cache: Dict[str, Dict] = {}

    @classmethod
    def clean_title(cls, title: str) -> str:
        """Başlığı temizler ve standartlaştırır."""
        cleaned = title.lower().strip()
        cleaned = re.sub(r"[^\w\s:]", "", cleaned)
        return cleaned

    @classmethod
    def enrich_title(cls, item: TitleItem) -> TitleItem:
        """
        Film veya dizinin eksik olan tür ve yönetmen bilgilerini tamamlar.
        """
        # Zaten tür ve yönetmen bilgisi varsa dokunma
        if item.genres and item.directors:
            return item

        cleaned = cls.clean_title(item.title)

        # 1. Önce yerel sözlükten ara
        for key, meta in CURATED_METADATA.items():
            if key in cleaned or cleaned in key:
                if not item.genres:
                    item.genres = meta.get("genres", [])
                if not item.directors:
                    item.directors = meta.get("directors", [])
                return item

        # 2. TMDB API anahtarı tanımlıysa TMDB'den ara
        if cls.API_KEY:
            try:
                # Önbellekte var mı?
                if cleaned in cls._cache:
                    cached = cls._cache[cleaned]
                    if not item.genres:
                        item.genres = cached.get("genres", [])
                    if not item.directors:
                        item.directors = cached.get("directors", [])
                    return item

                search_url = f"{cls.BASE_URL}/search/multi"
                resp = requests.get(
                    search_url,
                    params={"api_key": cls.API_KEY, "query": item.title, "year": item.year},
                    timeout=5
                )
                if resp.status_code == 200:
                    results = resp.json().get("results", [])
                    if results:
                        first = results[0]
                        media_type = first.get("media_type", "movie")
                        media_id = first.get("id")

                        # Detayları çek
                        detail_url = f"{cls.BASE_URL}/{media_type}/{media_id}"
                        detail_resp = requests.get(
                            detail_url,
                            params={"api_key": cls.API_KEY, "append_to_response": "credits"},
                            timeout=5
                        )
                        if detail_resp.status_code == 200:
                            data = detail_resp.json()
                            genres = [g["name"] for g in data.get("genres", [])]
                            directors = [
                                crew["name"]
                                for crew in data.get("credits", {}).get("crew", [])
                                if crew.get("job") == "Director"
                            ]
                            cls._cache[cleaned] = {"genres": genres, "directors": directors}
                            if not item.genres:
                                item.genres = genres
                            if not item.directors:
                                item.directors = directors
            except Exception as e:
                logger.warning(f"TMDB API sorgu hatası ({item.title}): {e}")

        # Bilgi bulunamadıysa genel varsayılan atama
        if not item.genres:
            item.genres = ["Cinema"]
        if not item.directors:
            item.directors = ["Bilinmeyen Yönetmen"]

        return item

    @classmethod
    def enrich_all(cls, items: List[TitleItem]) -> List[TitleItem]:
        """Tüm yapım listesini zenginleştirir."""
        return [cls.enrich_title(item) for item in items]
