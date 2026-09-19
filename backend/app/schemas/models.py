from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

class SyncUrlRequest(BaseModel):
    url: str = Field(..., description="Kullanıcının IMDb ratings veya watchlist herkese açık URL'si")
    target: Optional[str] = Field("auto", description="'ratings', 'watchlist' veya 'auto'")

class TitleItem(BaseModel):
    imdb_id: Optional[str] = Field(None, description="IMDb ID'si (örn. tt1375666)")
    title: str = Field(..., description="Yapım başlığı")
    year: Optional[int] = Field(None, description="Çıkış yılı")
    title_type: Optional[str] = Field("movie", description="movie, tvSeries, tvMiniSeries, documentary vb.")
    user_rating: Optional[float] = Field(None, description="Kullanıcının verdiği puan (1-10)")
    imdb_rating: Optional[float] = Field(None, description="IMDb genel puanı")
    in_watchlist: bool = Field(False, description="Watchlist'te mi?")
    genres: Optional[List[str]] = Field(default_factory=list, description="Türler")
    directors: Optional[List[str]] = Field(default_factory=list, description="Yönetmenler")
    date_added: Optional[str] = Field(None, description="Eklenme veya puanlama tarihi")
    source: str = Field("imdb", description="Veri kaynağı (imdb, letterboxd)")

class SyncSummary(BaseModel):
    status: str = "success"
    platform: str
    target: str
    total_items: int
    movies_count: int
    series_count: int
    avg_user_rating: Optional[float] = None
    items: List[TitleItem]

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
