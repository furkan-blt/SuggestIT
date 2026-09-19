import re
import json
import logging
from typing import List, Optional, Tuple
import requests
from bs4 import BeautifulSoup

from app.schemas.models import TitleItem, SyncSummary

logger = logging.getLogger(__name__)

# IMDb bot filtrelerini tetiklememek için standart güncel tarayıcı başlıkları
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}

class IMDbService:
    @staticmethod
    def normalize_imdb_url(raw_url: str, target: str = "auto") -> Tuple[str, str]:
        """
        Kullanıcının girdiği URL'yi temizler ve hedefi (ratings veya watchlist) tespit eder.
        """
        raw_url = raw_url.strip()
        
        # Kullanıcı urID formatında girdiyse (örn: ur12345678)
        if re.match(r"^ur\d+$", raw_url):
            if target == "watchlist":
                return f"https://www.imdb.com/user/{raw_url}/watchlist/", "watchlist"
            return f"https://www.imdb.com/user/{raw_url}/ratings/", "ratings"
        
        # Liste ID'si ise (ls123456)
        if re.match(r"^ls\d+$", raw_url):
            return f"https://www.imdb.com/list/{raw_url}/", "list"

        # URL formatında
        if "watchlist" in raw_url:
            detected_target = "watchlist"
        elif "ratings" in raw_url:
            detected_target = "ratings"
        elif "/list/" in raw_url:
            detected_target = "list"
        else:
            detected_target = "ratings" if target != "watchlist" else "watchlist"
            
        return raw_url, detected_target

    @classmethod
    def fetch_url(cls, url: str) -> str:
        """Belirtilen URL'nin HTML içeriğini indirir."""
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"IMDb URL fetch hatası ({url}): {e}")
            raise ValueError(f"IMDb sayfasına erişilemedi ({str(e)}). Lütfen profilinizin 'Herkese Açık' (Public) olduğundan emin olun.")

    @classmethod
    def extract_from_next_data(cls, soup: BeautifulSoup, target: str) -> List[TitleItem]:
        """IMDb'nin sayfa içine gömdüğü __NEXT_DATA__ JSON nesnesinden veri çeker."""
        items: List[TitleItem] = []
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag or not script_tag.string:
            return items

        try:
            data = json.loads(script_tag.string)
            page_props = data.get("props", {}).get("pageProps", {})
            
            # Farklı IMDb sayfa tiplerinde veri yolları değişkenlik gösterebilir
            candidates = []
            
            # Yol 1: mainColumnData -> userTitleListItems veya similar
            main_col = page_props.get("mainColumnData", {})
            if "ratingsTitleList" in main_col:
                candidates = main_col["ratingsTitleList"].get("edges", [])
            elif "watchlistTitleList" in main_col:
                candidates = main_col["watchlistTitleList"].get("edges", [])
            elif "userTitleList" in main_col:
                candidates = main_col["userTitleList"].get("edges", [])

            # Yol 2: contentData veya direct listData
            if not candidates:
                list_data = page_props.get("contentData", {}).get("entityList", {}).get("items", [])
                for entry in list_data:
                    title_info = entry.get("title", {}) or entry
                    imdb_id = title_info.get("id") or entry.get("id")
                    title_name = title_info.get("titleText", {}).get("text") or title_info.get("primaryTitle")
                    if imdb_id and title_name:
                        items.append(TitleItem(
                            imdb_id=imdb_id,
                            title=title_name,
                            year=title_info.get("releaseYear", {}).get("year"),
                            title_type=title_info.get("titleType", {}).get("id", "movie"),
                            in_watchlist=(target == "watchlist"),
                            source="imdb"
                        ))

            # Candidate edges varsa gez
            for edge in candidates:
                node = edge.get("node", {})
                title_obj = node.get("title", {}) or node
                imdb_id = title_obj.get("id")
                title_name = title_obj.get("titleText", {}).get("text")
                year_val = title_obj.get("releaseYear", {}).get("year")
                title_type_val = title_obj.get("titleType", {}).get("id", "movie")
                
                user_rating_val = None
                if "userRating" in node:
                    user_rating_val = node.get("userRating", {}).get("value")
                elif "rating" in node:
                    user_rating_val = node.get("rating")
                
                if imdb_id and title_name:
                    items.append(TitleItem(
                        imdb_id=imdb_id,
                        title=title_name,
                        year=year_val,
                        title_type=title_type_val,
                        user_rating=user_rating_val,
                        in_watchlist=(target == "watchlist"),
                        source="imdb"
                    ))

        except Exception as err:
            logger.warning(f"__NEXT_DATA__ ayrıştırılırken hata: {err}")

        return items

    @classmethod
    def extract_from_html_dom(cls, soup: BeautifulSoup, target: str) -> List[TitleItem]:
        """Modern ve klasik IMDb HTML DOM yapısından başlıkları ayrıştırır (Fallback)."""
        items: List[TitleItem] = []
        
        # Modern IMDb liste öğeleri: ipc-metadata-list-summary-item
        list_items = soup.select("li.ipc-metadata-list-summary-item, div.lister-item")
        
        for li in list_items:
            try:
                # Başlık ve ID
                title_elem = li.select_one("a.ipc-title-link-wrapper, h3.lister-item-header a, a.ipc-title__text")
                if not title_elem:
                    continue
                
                raw_title = title_elem.get_text(strip=True)
                # "1. Inception" gibi sıra numaralarını temizle
                cleaned_title = re.sub(r"^\d+\.\s*", "", raw_title)
                
                href = title_elem.get("href", "")
                id_match = re.search(r"(tt\d+)", href)
                imdb_id = id_match.group(1) if id_match else None
                
                # Çıkış Yılı
                year = None
                year_elem = li.select_one(
                    "span.dli-title-metadata-item, "
                    "span.lister-item-year, "
                    "ul.ipc-inline-list li"
                )
                if year_elem:
                    year_match = re.search(r"\b(19\d\d|20\d\d)\b", year_elem.get_text())
                    if year_match:
                        year = int(year_match.group(1))

                # Puan (Kullanıcı puanı veya genel puan)
                user_rating = None
                rating_elem = li.select_one(
                    "div.dli-user-rating span, "
                    "span.ipc-rating-star--rating, "
                    "div.ratings-imdb-rating strong"
                )
                if rating_elem:
                    try:
                        user_rating = float(rating_elem.get_text(strip=True))
                    except ValueError:
                        pass

                # Tür (varsa)
                genres = []
                genre_elem = li.select_one("span.genre")
                if genre_elem:
                    genres = [g.strip() for g in genre_elem.get_text().split(",") if g.strip()]

                if cleaned_title:
                    items.append(TitleItem(
                        imdb_id=imdb_id,
                        title=cleaned_title,
                        year=year,
                        title_type="movie",
                        user_rating=user_rating,
                        in_watchlist=(target == "watchlist"),
                        genres=genres,
                        source="imdb"
                    ))
            except Exception as e:
                logger.debug(f"HTML item parse hatası: {e}")
                continue

        return items

    @classmethod
    def sync_from_url(cls, raw_url: str, target: str = "auto") -> SyncSummary:
        """Verilen URL'den IMDb verilerini çeker ve özetler."""
        url, detected_target = cls.normalize_imdb_url(raw_url, target)
        html_content = cls.fetch_url(url)
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 1. Önce __NEXT_DATA__ üzerinden dene
        items = cls.extract_from_next_data(soup, detected_target)
        
        # 2. Eğer çıkmadıysa HTML DOM ayrıştırması yap
        if not items:
            items = cls.extract_from_html_dom(soup, detected_target)

        # İstatistikleri hesapla
        movies_count = sum(1 for item in items if item.title_type in ["movie", "featureFilm", "tvMovie"])
        series_count = sum(1 for item in items if "tv" in (item.title_type or "").lower() or "series" in (item.title_type or "").lower())
        
        ratings_list = [item.user_rating for item in items if item.user_rating is not None]
        avg_rating = round(sum(ratings_list) / len(ratings_list), 2) if ratings_list else None

        return SyncSummary(
            status="success" if items else "warning",
            platform="imdb",
            target=detected_target,
            total_items=len(items),
            movies_count=movies_count,
            series_count=series_count,
            avg_user_rating=avg_rating,
            items=items
        )
