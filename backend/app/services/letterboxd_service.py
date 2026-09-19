import re
import logging
import xml.etree.ElementTree as ET
from typing import List, Tuple
import requests

from app.schemas.models import TitleItem, SyncSummary

logger = logging.getLogger(__name__)

LETTERBOXD_NS = {
    "letterboxd": "https://letterboxd.com",
    "tmdb": "https://themoviedb.org",
    "dc": "http://purl.org/dc/elements/1.1/"
}

class LetterboxdService:
    @staticmethod
    def extract_username(raw_input: str) -> str:
        """Kullanıcının girdiği URL veya kullanıcı adından temiz username çıkarır."""
        raw_input = raw_input.strip().rstrip("/")
        # Eğer tam url ise örn: https://letterboxd.com/dave/ veya letterboxd.com/dave
        match = re.search(r"letterboxd\.com/([a-zA-Z0-9_\-]+)", raw_input)
        if match:
            return match.group(1)
        # Sadece kullanıcı adı girilmişse
        return raw_input

    @classmethod
    def sync_from_username_or_url(cls, raw_input: str) -> SyncSummary:
        """Letterboxd kullanıcısının açık RSS beslemesinden izleme ve puanlama verilerini çeker."""
        username = cls.extract_username(raw_input)
        rss_url = f"https://letterboxd.com/{username}/rss/"

        try:
            response = requests.get(
                rss_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
                timeout=15
            )
            if response.status_code == 404:
                raise ValueError(f"'{username}' adında bir Letterboxd kullanıcısı bulunamadı.")
            response.raise_for_status()

            root = ET.fromstring(response.content)
            items_xml = root.findall(".//item")
            
            items: List[TitleItem] = []
            for it in items_xml:
                # Başlık
                t_elem = it.find("{https://letterboxd.com}filmTitle")
                if t_elem is None or not t_elem.text:
                    t_elem = it.find("title")
                title = t_elem.text if t_elem is not None else "Bilinmeyen Başlık"

                # Yıl
                year = None
                y_elem = it.find("{https://letterboxd.com}filmYear")
                if y_elem is not None and y_elem.text and y_elem.text.isdigit():
                    year = int(y_elem.text)

                # Puan (0.5 - 5.0 -> 10'luk sisteme çevir: rating * 2)
                user_rating = None
                r_elem = it.find("{https://letterboxd.com}memberRating")
                if r_elem is not None and r_elem.text:
                    try:
                        user_rating = round(float(r_elem.text) * 2.0, 1)
                    except ValueError:
                        pass

                # TMDB ID
                tmdb_elem = it.find("{https://themoviedb.org}movieId")
                tmdb_id = tmdb_elem.text if tmdb_elem is not None else None

                # İzleme/Puanlama Tarihi
                date_elem = it.find("pubDate")
                date_added = date_elem.text if date_elem is not None else None

                items.append(TitleItem(
                    title=title,
                    year=year,
                    title_type="movie",
                    user_rating=user_rating,
                    date_added=date_added,
                    source="letterboxd_rss"
                ))

            ratings_list = [item.user_rating for item in items if item.user_rating is not None]
            avg_rating = round(sum(ratings_list) / len(ratings_list), 2) if ratings_list else None

            return SyncSummary(
                status="success",
                platform="letterboxd",
                target="rss_url",
                total_items=len(items),
                movies_count=len(items),
                series_count=0,
                avg_user_rating=avg_rating,
                items=items
            )

        except ET.ParseError as pe:
            logger.error(f"Letterboxd RSS XML ayrıştırma hatası: {pe}")
            raise ValueError("Letterboxd verisi ayrıştırılamadı. Kullanıcı adı geçersiz olabilir.")
        except requests.exceptions.RequestException as e:
            logger.error(f"Letterboxd istek hatası: {e}")
            raise ValueError(f"Letterboxd'ye bağlanılamadı: {str(e)}")
