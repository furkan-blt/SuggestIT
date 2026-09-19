import os
import re
import logging
from typing import Dict, List, Optional
import requests

from app.schemas.models import TitleItem

logger = logging.getLogger(__name__)

# Popüler yapımlar için genişletilmiş metadata sözlüğü
CURATED_METADATA: Dict[str, Dict[str, List[str]]] = {
    "inception": {"genres": ["Sci-Fi", "Action", "Thriller"], "directors": ["Christopher Nolan"]},
    "interstellar": {"genres": ["Sci-Fi", "Drama", "Adventure"], "directors": ["Christopher Nolan"]},
    "the dark knight": {"genres": ["Action", "Crime", "Drama"], "directors": ["Christopher Nolan"]},
    "oppenheimer": {"genres": ["Biography", "Drama", "History"], "directors": ["Christopher Nolan"]},
    "tenet": {"genres": ["Sci-Fi", "Action", "Thriller"], "directors": ["Christopher Nolan"]},
    "dunkirk": {"genres": ["War", "Action", "Drama"], "directors": ["Christopher Nolan"]},
    "memento": {"genres": ["Mystery", "Thriller"], "directors": ["Christopher Nolan"]},
    "the prestige": {"genres": ["Drama", "Mystery", "Sci-Fi"], "directors": ["Christopher Nolan"]},
    "prestige": {"genres": ["Drama", "Mystery", "Sci-Fi"], "directors": ["Christopher Nolan"]},
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
    "cold war": {"genres": ["Drama", "Romance", "Music"], "directors": ["Pawel Pawlikowski"]},
    "blue heron": {"genres": ["Drama"], "directors": ["Sophie Barthes"]},
    "novocaine": {"genres": ["Action", "Thriller"], "directors": ["Dan Berk", "Robert Olsen"]},
    "the president's cake": {"genres": ["Drama", "Comedy"], "directors": ["Hasan Hadi"]},
    "anora": {"genres": ["Comedy", "Drama", "Romance"], "directors": ["Sean Baker"]},
    "conclave": {"genres": ["Drama", "Thriller", "Mystery"], "directors": ["Edward Berger"]},
    "the brutalist": {"genres": ["Drama"], "directors": ["Brady Corbet"]},
    "substance": {"genres": ["Horror", "Sci-Fi", "Drama"], "directors": ["Coralie Fargeat"]},
    "the substance": {"genres": ["Horror", "Sci-Fi", "Drama"], "directors": ["Coralie Fargeat"]},
    "wicked": {"genres": ["Musical", "Fantasy", "Romance"], "directors": ["Jon M. Chu"]},
    "gladiator ii": {"genres": ["Action", "Adventure", "Drama"], "directors": ["Ridley Scott"]},
    "gladiator": {"genres": ["Action", "Adventure", "Drama"], "directors": ["Ridley Scott"]},
    "alien": {"genres": ["Sci-Fi", "Horror"], "directors": ["Ridley Scott"]},
    "blade runner": {"genres": ["Sci-Fi", "Thriller"], "directors": ["Ridley Scott"]},
    "taxi driver": {"genres": ["Crime", "Drama"], "directors": ["Martin Scorsese"]},
    "goodfellas": {"genres": ["Biography", "Crime", "Drama"], "directors": ["Martin Scorsese"]},
    "the wolf of wall street": {"genres": ["Biography", "Comedy", "Crime"], "directors": ["Martin Scorsese"]},
    "shutter island": {"genres": ["Mystery", "Thriller"], "directors": ["Martin Scorsese"]},
    "whiplash": {"genres": ["Drama", "Music"], "directors": ["Damien Chazelle"]},
    "la la land": {"genres": ["Comedy", "Drama", "Music"], "directors": ["Damien Chazelle"]},
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
        Film veya dizinin eksik olan tür ve yönetmen bilgilerini organik olarak tamamlar.
        Asla sahte 'Cinema' veya 'Genel' gibi jenerik etiketler eklemez.
        """
        if item.genres and item.directors:
            return item

        cleaned = cls.clean_title(item.title)

        # 1. Önce yerel sözlükten ara
        for key, meta in CURATED_METADATA.items():
            if key == cleaned or key in cleaned or cleaned in key:
                if not item.genres and meta.get("genres"):
                    item.genres = list(meta["genres"])
                if not item.directors and meta.get("directors"):
                    item.directors = list(meta["directors"])
                return item

        # 2. TMDB API anahtarı tanımlıysa doğrudan TMDB'den sorgula
        if cls.API_KEY:
            try:
                if cleaned in cls._cache:
                    cached = cls._cache[cleaned]
                    if not item.genres and cached.get("genres"):
                        item.genres = list(cached["genres"])
                    if not item.directors and cached.get("directors"):
                        item.directors = list(cached["directors"])
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
                            if not item.genres and genres:
                                item.genres = genres
                            if not item.directors and directors:
                                item.directors = directors
            except Exception as e:
                logger.warning(f"TMDB API sorgu hatası ({item.title}): {e}")

        # Tür veya yönetmen bulunamadıysa boş bırakılır; asla 'Cinema' gibi yapay düğüm eklenmez
        if item.genres is None:
            item.genres = []
        if item.directors is None:
            item.directors = []

        return item

    @classmethod
    def enrich_all(cls, items: List[TitleItem]) -> List[TitleItem]:
        """Tüm yapım listesini zenginleştirir."""
        return [cls.enrich_title(item) for item in items]
