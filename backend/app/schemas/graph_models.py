from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class GraphNode(BaseModel):
    id: str = Field(..., description="Düğümün benzersiz kimliği (örn: 'genre_sci-fi', 'dir_christopher_nolan')")
    label: str = Field(..., description="Kullanıcıya gösterilecek isim")
    type: str = Field(..., description="'genre', 'director' veya 'title'")
    weight: float = Field(1.0, description="Düğümün ağırlığı / önem derecesi")
    size: int = Field(20, description="Görselleştirme boyutu")
    color: str = Field("#ffffff", description="Görselleştirme rengi")
    rating: Optional[float] = Field(None, description="Ortalama puan veya film puanı")
    year: Optional[int] = Field(None, description="Yapım yılı (title için)")

class GraphEdge(BaseModel):
    source: str = Field(..., description="Kaynak düğüm ID'si")
    target: str = Field(..., description="Hedef düğüm ID'si")
    relation: str = Field("connected_to", description="'has_genre', 'directed_by', 'co_genre'")
    weight: float = Field(1.0, description="Bağlantının gücü")

class TasteArchetype(BaseModel):
    title: str = Field(..., description="Kullanıcının Sinematik Arketip Unvanı")
    tagline: str = Field(..., description="Kısa çarpıcı slogan")
    description: str = Field(..., description="Detaylı zevk analizi açıklaması")
    dominant_genres: List[str] = Field(default_factory=list, description="En çok izlenen ve sevilen türler")
    favorite_directors: List[str] = Field(default_factory=list, description="Öne çıkan yönetmenler")
    cinematic_era: str = Field("Modern Sinema", description="En yoğun izlenen dönem (örn. 2010'lar)")
    total_watched: int = Field(0, description="Analiz edilen toplam yapım")
    average_rating: Optional[float] = Field(None, description="Ortalama verilen puan")

class NetworkGraphResponse(BaseModel):
    archetype: TasteArchetype
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int
