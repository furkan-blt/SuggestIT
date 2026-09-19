from collections import Counter, defaultdict
import logging
from typing import List, Dict, Tuple, Optional, Set

from app.schemas.models import TitleItem
from app.schemas.graph_models import (
    GraphNode,
    GraphEdge,
    TasteArchetype,
    NetworkGraphResponse,
)
from app.services.tmdb_service import TMDBService

logger = logging.getLogger(__name__)

# Tür Renk Paleti (Neon / Cyberpunk estetiği)
GENRE_COLORS: Dict[str, str] = {
    "sci-fi": "#00f2fe",      # Neon Cyan
    "action": "#ff0844",      # Crimson Red
    "crime": "#ff4e50",       # Red-Orange
    "thriller": "#7928ca",    # Deep Neon Purple
    "mystery": "#9b51e0",     # Electric Violet
    "drama": "#f39c12",       # Warm Gold
    "adventure": "#00e676",   # Vibrant Green
    "romance": "#ff758c",     # Soft Rose
    "comedy": "#f857a6",      # Hot Pink
    "horror": "#8e44ad",      # Dark Velvet
    "biography": "#f6d365",   # Sun Yellow
    "history": "#d35400",     # Rust Amber
    "war": "#7f8c8d",         # Steel Grey
    "music": "#a8ff78",       # Lime Glow
    "fantasy": "#4facfe",     # Sky Blue
    "animation": "#fa709a",   # Peach Glow
}

DEFAULT_GENRE_COLOR = "#00d2ff"
DIRECTOR_COLOR = "#f9d423"   # Golden Yellow
DECADE_COLOR = "#a18cd1"     # Soft Purple / Lavender
FORMAT_COLOR = "#ff9a9e"     # Coral Pink

class GraphService:
    @staticmethod
    def get_decade_info(year: Optional[int]) -> Tuple[str, str]:
        """Yıla göre dönemsel pattern etiketini ve ID'sini döner."""
        if not year:
            return "decade_unknown", "Bilinmeyen Dönem"
        if year >= 2020:
            return "decade_2020s", "2020'ler (Yeni Çıkışlar)"
        elif year >= 2010:
            return "decade_2010s", "2010'lar"
        elif year >= 2000:
            return "decade_2000s", "2000'ler (Milenyum)"
        elif year >= 1990:
            return "decade_1990s", "90'lar Klasikleri"
        elif year >= 1980:
            return "decade_1980s", "80'ler"
        else:
            return "decade_classic", "Klasik Dönem (<1980)"

    @classmethod
    def determine_archetype(
        cls,
        top_genres: List[Tuple[str, int, float]],
        top_directors: List[Tuple[str, int]],
        era: str,
        total_items: int,
        overall_avg: float
    ) -> TasteArchetype:
        """Kullanıcının izleme karakterini ve sinematik arketipini belirler."""
        genre_names = [g[0].lower() for g in top_genres[:3]]
        director_names = [d[0] for d in top_directors[:2]]

        title = "Sinematik Gezgin"
        tagline = "Farklı türler ve dönemler arasında çok yönlü bir izleme çizgisi."
        desc = "Tek bir türe veya döneme saplanıp kalmayan, hikaye çeşitliliğine değer veren açık fikirli bir izleyici."

        if any(g in genre_names for g in ["sci-fi", "mystery"]) and any(g in genre_names for g in ["thriller", "action"]):
            title = "Zihin Bükücü & Kozmik Gerilim Meraklısı"
            tagline = "Zaman döngüleri, varoluşsal paradokslar ve yüksek kurgusal zeka peşinde."
            desc = (
                f"Film zevkinizin merkezinde {top_genres[0][0] if top_genres else 'Sci-Fi'} ve kurgusal gizem var. "
                "Kolay tahmin edilebilir sonlardan hoşlanmıyor; sizi düşündüren, şaşırtan ve teoriler kurduran yapımlara odaklanıyorsunuz."
            )
        elif any(g in genre_names for g in ["crime", "thriller"]) and "drama" in genre_names:
            title = "Neo-Noir & Kusursuz Suç Dedektifi"
            tagline = "Karanlık sokaklar, ahlaki gri alanlar ve kusursuz suç kurguları."
            desc = (
                "Karakterlerin iyi ve kötü arasında parçalandığı atmosferik ve soğuk kurguları seviyorsunuz. "
                "Psikolojik derinliği olan ritmik gerilimler ve suç dramaları sinematik konfor alanınız."
            )
        elif "drama" in genre_names and any(g in genre_names for g in ["biography", "history", "romance"]):
            title = "İnsan Doğası & Derin Hikaye Kaşifi"
            tagline = "Karakter çatışmaları, duygusal gerçeklik ve felsefi alt metinler."
            desc = (
                "Sizin için bir yapımın gücü yüksek aksiyondan değil, karakterin ruhsal derinliğinden ve dönemsel gerçekliğinden gelir. "
                "Vurucu finaller ve güçlü oyunculuklar sizin için vazgeçilmez."
            )
        elif any(g in genre_names for g in ["adventure", "action", "fantasy"]):
            title = "Epik Vizyon & Görsel Dünya Gezgini"
            tagline = "Büyüleyici evrenler, dev prodüksiyonlar ve nefes kesen yolculuklar."
            desc = (
                "Perdede devasa dünyalar kurulmasını seviyorsunuz. Görsel ihtişam, atmosferik anlatım ve destansı çatışmalar "
                "zevkinizin en belirleyici taşları."
            )

        return TasteArchetype(
            title=title,
            tagline=tagline,
            description=desc,
            dominant_genres=[g[0] for g in top_genres[:4]],
            favorite_directors=director_names,
            cinematic_era=era,
            total_watched=total_items,
            average_rating=overall_avg,
        )

    @classmethod
    def generate_graph(cls, titles: List[TitleItem]) -> NetworkGraphResponse:
        """
        Kullanıcının izlediği TÜM yapımları içeren, organik örüntülerle 
        (v2 algoritması: PageRank, Louvain toplulukları) örülmüş eksiksiz 
        Taste Network Graph verisini üretir.
        """
        if not titles:
            raise ValueError("Grafik üretmek için en az bir film/dizi başlığı gereklidir.")

        # 1. Eksik metadata bilgilerini organik tamamla
        enriched_titles = TMDBService.enrich_all(titles)

        # 2. V2 algoritması için dict listesine çevir
        watched_list = []
        for idx, item in enumerate(enriched_titles):
            # Eğer gün/zaman bilgisi yoksa None verelim (yeni eklenenler için)
            days_watched = 30 # Default varsayım
            
            # Genres ve keywords ayarla
            genres = [g.strip().capitalize() for g in item.genres if g.strip()]
            if not genres:
                genres = ["Unknown"]
            
            directors = [d.strip() for d in item.directors if d.strip()]
            director = directors[0] if directors else "Unknown"
            
            dec_id, dec_label = cls.get_decade_info(item.year)
            
            watched_list.append({
                "id": f"t_{idx}", # Geçici ID
                "title": item.title,
                "media_type": "series" if "tv" in (item.title_type or "").lower() or "series" in (item.title_type or "").lower() else "movie",
                "genres": genres,
                "director": director,
                "decade": dec_label,
                "keywords": [], # Eğer keywords eklersek buradan alır (TMDbService'e eklenebilir)
                "user_rating": item.user_rating if item.user_rating is not None else 7.0,
                "days_since_watched": days_watched,
                "original_item": item # Orijinal veriyi sakla
            })

        # 3. Yeni Algoritmayı Çalıştır
        from app.services.graph_builder import build_taste_graph, analyze_graph, generate_persona
        
        G = build_taste_graph(watched_list)
        analysis = analyze_graph(G)
        pagerank = analysis["pagerank"]
        communities = analysis["communities"]

        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []
        node_ids: Set[str] = set()

        # Düğümleri (Nodes) Oluştur
        for node, data in G.nodes(data=True):
            n_kind = data.get("kind")
            n_label = data.get("label", str(node))
            node_id_str = str(node[1]) if isinstance(node, tuple) else str(node)
            final_node_id = f"{n_kind}_{node_id_str}".replace(" ", "_")
            
            # Boyutu PageRank'e göre belirle (basit bir çarpanla normalize et)
            pr_score = pagerank.get(node, 0.001)
            # Default boyutlar
            base_size = 20
            color = "#cbd5e1"
            rating = None
            year = None

            if n_kind == "title":
                rating = data.get("rating")
                if rating is not None:
                    if rating >= 8.0:
                        color = "#ffffff"
                        base_size = min(30, max(18, int(14 + (rating * 1.2))))
                    elif rating >= 6.0:
                        color = "#cbd5e1"
                        base_size = 15
                    else:
                        color = "#ff6b6b"
                        base_size = 12
                else:
                    color = "#94a3b8"
                    base_size = 14
            elif n_kind == "genre":
                color = GENRE_COLORS.get(n_label.lower(), DEFAULT_GENRE_COLOR)
                base_size = min(60, max(25, int(20 + pr_score * 1000)))
            elif n_kind == "director":
                color = DIRECTOR_COLOR
                base_size = min(45, max(20, int(15 + pr_score * 800)))
            elif n_kind == "decade":
                color = DECADE_COLOR
                base_size = min(40, max(20, int(15 + pr_score * 800)))
            else:
                base_size = min(30, max(15, int(10 + pr_score * 500)))

            nodes.append(GraphNode(
                id=final_node_id,
                label=n_label,
                type=n_kind,
                weight=pr_score * 100,
                size=base_size,
                color=color,
                rating=rating,
                year=year
            ))
            node_ids.add(final_node_id)

        # Kenarları (Edges) Oluştur
        for u, v, data in G.edges(data=True):
            u_kind = G.nodes[u].get("kind")
            v_kind = G.nodes[v].get("kind")
            
            u_id = f"{u_kind}_{str(u[1])}".replace(" ", "_") if isinstance(u, tuple) else str(u)
            v_id = f"{v_kind}_{str(v[1])}".replace(" ", "_") if isinstance(v, tuple) else str(v)
            
            edges.append(GraphEdge(
                source=u_id,
                target=v_id,
                relation="connected",
                weight=data.get("weight", 1.0)
            ))

        # En baskın topluluğa (community) göre arketip belirle
        best_persona = None
        largest_size = 0
        all_personas = []
        for idx, comm in enumerate(communities):
            persona = generate_persona(G, comm)
            if persona and persona["valence"] == "positive":
                all_personas.append(persona)
                if persona["size"] > largest_size:
                    largest_size = persona["size"]
                    best_persona = persona

        if best_persona:
            llm_facts = best_persona["llm_prompt_facts"]
            archetype = TasteArchetype(
                title=best_persona["rule_based_title"],
                tagline="Graf analiziyle bulunan en belirgin topluluk",
                description=f"Senin zevk kümelerinde en baskın yapı {best_persona['size']} filmle bu topluluk. Ortalama puanı: {best_persona['avg_rating']}",
                dominant_genres=llm_facts.get("dominant_genres", []),
                favorite_directors=[llm_facts.get("signature_director")] if llm_facts.get("signature_director") else [],
                cinematic_era="Modern",
                total_watched=len(titles),
                average_rating=llm_facts.get("avg_rating")
            )
        else:
            # Fallback
            archetype = TasteArchetype(
                title="Çok Yönlü İzleyici",
                tagline="Belirgin bir küme bulunamadı",
                description="Zevkin oldukça çeşitli ve tek bir alana toplanmamış.",
                dominant_genres=[],
                favorite_directors=[],
                cinematic_era="Bilinmiyor",
                total_watched=len(titles),
                average_rating=7.0
            )

        return NetworkGraphResponse(
            archetype=archetype,
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges)
        )
