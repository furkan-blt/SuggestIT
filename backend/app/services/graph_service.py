from collections import Counter, defaultdict
import logging
from typing import List, Dict, Tuple, Optional

from app.schemas.models import TitleItem
from app.schemas.graph_models import (
    GraphNode,
    GraphEdge,
    TasteArchetype,
    NetworkGraphResponse,
)
from app.services.tmdb_service import TMDBService

logger = logging.getLogger(__name__)

GENRE_COLORS: Dict[str, str] = {
    "sci-fi": "#00f2fe",      # Neon Cyan
    "action": "#ff0844",      # Crimson
    "crime": "#ff4e50",       # Red-Orange
    "thriller": "#7928ca",    # Deep Neon Purple
    "mystery": "#9b51e0",     # Electric Violet
    "drama": "#f39c12",       # Warm Gold
    "adventure": "#00e676",   # Vibrant Green
    "romance": "#ff758c",     # Soft Rose
    "comedy": "#f857a6",      # Hot Pink
    "horror": "#4a00e0",      # Dark Velvet
    "biography": "#f6d365",   # Sun Yellow
    "history": "#d35400",     # Rust Amber
    "war": "#7f8c8d",         # Steel Grey
}

DEFAULT_GENRE_COLOR = "#00d2ff"
DIRECTOR_COLOR = "#f9d423"   # Golden Yellow
TITLE_COLOR = "#ffffff"      # Bright White

class GraphService:
    @staticmethod
    def determine_archetype(
        top_genres: List[Tuple[str, int, float]],
        top_directors: List[Tuple[str, int]],
        era: str,
        total_items: int,
        overall_avg: float
    ) -> TasteArchetype:
        """Kullanıcının izleme karakterini ve sinematik arketipini belirler."""
        genre_names = [g[0].lower() for g in top_genres[:3]]
        director_names = [d[0] for d in top_directors[:2]]

        # Varsayılanlar
        title = "Sinematik Gezgin"
        tagline = "Farklı türler ve hikayeler arasında dengeli bir kurgu arayışı."
        desc = "Tek bir türe saplanıp kalmayan, iyi yazılmış her hikayeye şans veren açık fikirli bir sinemasever."

        if any(g in genre_names for g in ["sci-fi", "mystery"]) and any(g in genre_names for g in ["thriller", "action"]):
            title = "Zihin Bükücü & Kozmik Gerilim Meraklısı"
            tagline = "Zaman döngüleri, varoluşsal paradokslar ve yüksek kurgusal zeka peşinde."
            desc = (
                f"Film zevkinizin merkezinde {top_genres[0][0]} ve {top_genres[1][0] if len(top_genres) > 1 else 'kurgusal gizem'} var. "
                "Kolay tahmin edilebilir sonlardan hoşlanmıyor; sizi düşündüren, şaşırtan ve teoriler kurduran yapımlara yüksek puan veriyorsunuz."
            )
        elif any(g in genre_names for g in ["crime", "thriller"]) and "drama" in genre_names:
            title = "Neo-Noir & Kusursuz Suç Dedektifi"
            tagline = "Karanlık sokaklar, ahlaki gri alanlar ve kusursuz suç kurguları."
            desc = (
                "Karakterlerin iyi ve kötü arasında parçalandığı, atmosferik ve soğuk kurguları seviyorsunuz. "
                "Fincher, Gilligan veya Tarantino tarzı ritmik gerilimler sizin sinematik konfor alanınız."
            )
        elif "drama" in genre_names and any(g in genre_names for g in ["biography", "history"]):
            title = "İnsan Doğası & Tarihsel Derinlik Kaşifi"
            tagline = "Karakter çatışmaları, gerçek hayat hikayeleri ve felsefi alt metinler."
            desc = (
                "Sizin için bir filmin gücü patlamalardan değil, karakterin ruhsal derinliğinden ve dönemsel gerçekliğinden gelir. "
                "Yüksek oyunculuk performansları ve vurucu finaller sizin için vazgeçilmez."
            )
        elif any(g in genre_names for g in ["adventure", "sci-fi", "action"]):
            title = "Epik Vizyon & Görsel Dünya Gezgini"
            tagline = "Büyüleyici evrenler, dev prodüksiyonlar ve nefes kesen yolculuklar."
            desc = (
                "Perdede devasa dünyalar kurulmasını seviyorsunuz. Görsel ihtişam, atmosferik müzikler ve destansı çatışmalar "
                "puanlama kriterlerinizin en tepesinde yer alıyor."
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
        Kullanıcının film/dizi listesinden Taste Network Graph verisini üretir.
        """
        if not titles:
            raise ValueError("Grafik üretmek için en az bir film/dizi başlığı gereklidir.")

        # 1. Eksik tür ve yönetmenleri zenginleştir
        enriched_titles = TMDBService.enrich_all(titles)

        # 2. İstatistikleri topla
        genre_ratings: Dict[str, List[float]] = defaultdict(list)
        director_counts: Counter = Counter()
        year_counts: Counter = Counter()
        all_ratings: List[float] = []

        for item in enriched_titles:
            rating = item.user_rating if item.user_rating is not None else 7.5
            all_ratings.append(rating)
            if item.year:
                decade = f"{(item.year // 10) * 10}'ler"
                year_counts[decade] += 1

            for g in item.genres:
                g_clean = g.strip().capitalize()
                genre_ratings[g_clean].append(rating)

            for d in item.directors:
                d_clean = d.strip()
                if d_clean and d_clean.lower() != "bilinmeyen yönetmen":
                    director_counts[d_clean] += 1

        overall_avg = round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 7.5
        dominant_era = year_counts.most_common(1)[0][0] if year_counts else "Modern Sinema"

        # Tür skorları: count * 1.5 + avg_rating * 1.0
        genre_stats = []
        for g_name, r_list in genre_ratings.items():
            g_count = len(r_list)
            g_avg = sum(r_list) / g_count
            score = (g_count * 1.5) + (g_avg * 1.0)
            genre_stats.append((g_name, g_count, g_avg, score))

        # En güçlü türler (Skora göre sıralı)
        genre_stats.sort(key=lambda x: x[3], reverse=True)
        top_genres = genre_stats[:8]  # Grafiği boğmamak için en güçlü 8 tür

        # En çok izlenen ilk 6 yönetmen
        top_directors = director_counts.most_common(6)

        # Karakter arketipi üret
        archetype = cls.determine_archetype(
            [(g[0], g[1], g[2]) for g in top_genres],
            top_directors,
            dominant_era,
            len(enriched_titles),
            overall_avg
        )

        # 3. Düğümleri (Nodes) Oluştur
        nodes: List[GraphNode] = []
        node_ids = set()

        # A. Tür Düğümleri
        for g_name, g_count, g_avg, score in top_genres:
            node_id = f"genre_{g_name.lower()}"
            color = GENRE_COLORS.get(g_name.lower(), DEFAULT_GENRE_COLOR)
            # Boyut: En az 28, en fazla 55 px
            size = min(55, max(28, int(24 + (g_count * 2.5))))
            nodes.append(GraphNode(
                id=node_id,
                label=g_name,
                type="genre",
                weight=round(score, 1),
                size=size,
                color=color,
                rating=round(g_avg, 1)
            ))
            node_ids.add(node_id)

        # B. Yönetmen Düğümleri
        for d_name, d_count in top_directors:
            node_id = f"dir_{d_name.lower().replace(' ', '_')}"
            size = min(45, max(22, int(18 + (d_count * 4))))
            nodes.append(GraphNode(
                id=node_id,
                label=d_name,
                type="director",
                weight=float(d_count),
                size=size,
                color=DIRECTOR_COLOR
            ))
            node_ids.add(node_id)

        # C. Kilit Yapım Düğümleri (Puanı yüksek olan veya öne çıkan yapımlar)
        # Puanı en yüksek olan yapımlardan ilk 15-20 tanesi
        sorted_titles = sorted(
            enriched_titles,
            key=lambda x: (x.user_rating or 0.0),
            reverse=True
        )
        selected_titles = sorted_titles[:15]

        for item in selected_titles:
            # Temiz bir ID oluştur
            t_id = f"title_{item.title.lower()[:15].strip().replace(' ', '_')}"
            if t_id not in node_ids:
                rating_val = item.user_rating if item.user_rating is not None else 8.0
                size = min(32, max(16, int(14 + (rating_val * 1.5))))
                nodes.append(GraphNode(
                    id=t_id,
                    label=item.title,
                    type="title",
                    weight=rating_val,
                    size=size,
                    color=TITLE_COLOR,
                    rating=item.user_rating,
                    year=item.year
                ))
                node_ids.add(t_id)

        # 4. Kenarları (Edges) Oluştur
        edges: List[GraphEdge] = []
        edge_pairs = set()

        # Film -> Tür ve Film -> Yönetmen bağları
        for item in selected_titles:
            t_id = f"title_{item.title.lower()[:15].strip().replace(' ', '_')}"
            if t_id not in node_ids:
                continue

            # Tür bağları
            for g in item.genres:
                g_id = f"genre_{g.strip().lower()}"
                if g_id in node_ids:
                    pair = (t_id, g_id)
                    if pair not in edge_pairs:
                        edges.append(GraphEdge(
                            source=t_id,
                            target=g_id,
                            relation="has_genre",
                            weight=1.5
                        ))
                        edge_pairs.add(pair)

            # Yönetmen bağları
            for d in item.directors:
                d_id = f"dir_{d.strip().lower().replace(' ', '_')}"
                if d_id in node_ids:
                    pair = (t_id, d_id)
                    if pair not in edge_pairs:
                        edges.append(GraphEdge(
                            source=t_id,
                            target=d_id,
                            relation="directed_by",
                            weight=2.0
                        ))
                        edge_pairs.add(pair)

        # Tür -> Tür ortak bağları (Aynı filmlerde sıkça beraber geçen türler)
        co_genre_counter: Counter = Counter()
        for item in enriched_titles:
            clean_genres = [g.strip().capitalize() for g in item.genres if f"genre_{g.strip().lower()}" in node_ids]
            for i in range(len(clean_genres)):
                for j in range(i + 1, len(clean_genres)):
                    g1, g2 = sorted([clean_genres[i], clean_genres[j]])
                    co_genre_counter[(g1, g2)] += 1

        for (g1, g2), count in co_genre_counter.most_common(6):
            g1_id = f"genre_{g1.lower()}"
            g2_id = f"genre_{g2.lower()}"
            if g1_id in node_ids and g2_id in node_ids:
                pair = (g1_id, g2_id)
                if pair not in edge_pairs:
                    edges.append(GraphEdge(
                        source=g1_id,
                        target=g2_id,
                        relation="co_genre",
                        weight=min(3.0, 1.0 + (count * 0.3))
                    ))
                    edge_pairs.add(pair)

        return NetworkGraphResponse(
            archetype=archetype,
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges)
        )
