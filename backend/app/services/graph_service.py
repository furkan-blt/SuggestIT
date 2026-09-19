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
        Kullanıcının izlediği TÜM yapımları içeren, organik örüntülerle (Tür, Dönem, Yönetmen, Format)
        örülmüş eksiksiz Taste Network Graph verisini üretir.
        """
        if not titles:
            raise ValueError("Grafik üretmek için en az bir film/dizi başlığı gereklidir.")

        # 1. Eksik metadata bilgilerini organik tamamla
        enriched_titles = TMDBService.enrich_all(titles)

        # 2. İstatistikleri topla
        genre_ratings: Dict[str, List[float]] = defaultdict(list)
        director_counts: Counter = Counter()
        decade_counts: Counter = Counter()
        all_ratings: List[float] = []

        for item in enriched_titles:
            rating = item.user_rating if item.user_rating is not None else 7.0
            all_ratings.append(rating)

            # Dönem sayımı
            dec_id, dec_label = cls.get_decade_info(item.year)
            if dec_id != "decade_unknown":
                decade_counts[(dec_id, dec_label)] += 1

            # Tür sayımı (Gerçek türler)
            for g in item.genres:
                clean_g = g.strip().capitalize()
                # Kesinlikle 'Cinema' gibi yapay etiketleri alma
                if clean_g and clean_g.lower() not in ["cinema", "movie", "bilinmeyen", "unknown"]:
                    genre_ratings[clean_g].append(rating)

            # Yönetmen sayımı
            for d in item.directors:
                clean_d = d.strip()
                if clean_d and clean_d.lower() not in ["bilinmeyen yönetmen", "unknown director", "director"]:
                    director_counts[clean_d] += 1

        overall_avg = round(sum(all_ratings) / len(all_ratings), 2) if all_ratings else 7.0
        dominant_era = decade_counts.most_common(1)[0][0][1] if decade_counts else "Modern Sinema"

        # Tür skorları
        genre_stats = []
        for g_name, r_list in genre_ratings.items():
            g_count = len(r_list)
            g_avg = sum(r_list) / g_count
            score = (g_count * 1.5) + (g_avg * 1.0)
            genre_stats.append((g_name, g_count, g_avg, score))

        # En güçlü türler
        genre_stats.sort(key=lambda x: x[3], reverse=True)
        top_genres = genre_stats[:10]  # En popüler 10 tür düğümü

        # En çok izlenen yönetmenler (en az 1 filmi olanlar)
        top_directors = director_counts.most_common(10)

        # Karakter arketipi üret
        archetype = cls.determine_archetype(
            [(g[0], g[1], g[2]) for g in top_genres],
            top_directors,
            dominant_era,
            len(enriched_titles),
            overall_avg
        )

        nodes: List[GraphNode] = []
        node_ids: Set[str] = set()

        # A. Tür Düğümleri (Genre Pattern)
        for g_name, g_count, g_avg, score in top_genres:
            node_id = f"genre_{g_name.lower()}"
            color = GENRE_COLORS.get(g_name.lower(), DEFAULT_GENRE_COLOR)
            size = min(50, max(26, int(22 + (g_count * 2.0))))
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

        # B. Dönem / Yıl Düğümleri (Decade Pattern)
        for (dec_id, dec_label), d_count in decade_counts.items():
            if d_count >= 1:  # En az 1 filmi olan dönemler
                size = min(44, max(24, int(20 + (d_count * 1.5))))
                nodes.append(GraphNode(
                    id=dec_id,
                    label=dec_label,
                    type="decade",
                    weight=float(d_count),
                    size=size,
                    color=DECADE_COLOR
                ))
                node_ids.add(dec_id)

        # C. Yönetmen Düğümleri (Director Pattern)
        for d_name, d_count in top_directors:
            if d_count >= 1:
                node_id = f"dir_{d_name.lower().replace(' ', '_')}"
                size = min(38, max(20, int(18 + (d_count * 3))))
                nodes.append(GraphNode(
                    id=node_id,
                    label=d_name,
                    type="director",
                    weight=float(d_count),
                    size=size,
                    color=DIRECTOR_COLOR
                ))
                node_ids.add(node_id)

        # D. Dizi Dünyası Format Düğümü (varsa)
        has_series = any("tv" in (t.title_type or "").lower() or "series" in (t.title_type or "").lower() for t in enriched_titles)
        if has_series:
            nodes.append(GraphNode(
                id="format_series",
                label="Dizi Dünyası",
                type="format",
                weight=5.0,
                size=32,
                color=FORMAT_COLOR
            ))
            node_ids.add("format_series")

        # E. KULLANICININ İZLEDİĞİ TÜM YAPIMLAR (Hiçbir sınırlama yok!)
        for idx, item in enumerate(enriched_titles):
            rating_val = item.user_rating
            # Benzersiz ID oluştur
            safe_title = item.title.lower()[:20].strip().replace(" ", "_")
            t_id = f"title_{safe_title}_{item.year or idx}"

            # Puanına göre stil ve renk:
            # 8.0+: Parlak beyaz (#ffffff), büyük
            # 6.0 - 7.9: Normal gri-beyaz (#e2e8f0), orta
            # < 6.0: Kırmızımsı-pembe (#ff6b6b - negatif/düşük puan göstergesi), daha küçük
            # Puansız: Yumuşak mavi (#cbd5e1)
            if rating_val is not None:
                if rating_val >= 8.0:
                    node_color = "#ffffff"
                    node_size = min(26, max(18, int(14 + (rating_val * 1.2))))
                elif rating_val >= 6.0:
                    node_color = "#cbd5e1"
                    node_size = 15
                else:
                    node_color = "#ff6b6b"  # Düşük puan
                    node_size = 12
            else:
                node_color = "#94a3b8"
                node_size = 14

            nodes.append(GraphNode(
                id=t_id,
                label=item.title,
                type="title",
                weight=rating_val if rating_val is not None else 6.0,
                size=node_size,
                color=node_color,
                rating=rating_val,
                year=item.year
            ))
            node_ids.add(t_id)

        # 4. Kenarlar (Edges) - Yapımları Örüntülerle Bağlama
        edges: List[GraphEdge] = []
        edge_pairs: Set[Tuple[str, str]] = set()

        for idx, item in enumerate(enriched_titles):
            safe_title = item.title.lower()[:20].strip().replace(" ", "_")
            t_id = f"title_{safe_title}_{item.year or idx}"

            # 1. Tür Bağlantıları
            has_genre_link = False
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
                        has_genre_link = True

            # 2. Yönetmen Bağlantıları
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

            # 3. Dönem Bağlantısı (Decade Pattern)
            dec_id, _ = cls.get_decade_info(item.year)
            if dec_id in node_ids:
                pair = (t_id, dec_id)
                if pair not in edge_pairs:
                    # Eğer filmin türü yoksa dönem bağlantısı daha güçlü olsun ki yalnız kalmasın
                    w = 2.0 if not has_genre_link else 1.0
                    edges.append(GraphEdge(
                        source=t_id,
                        target=dec_id,
                        relation="from_decade",
                        weight=w
                    ))
                    edge_pairs.add(pair)

            # 4. Format Bağlantısı (Dizi ise Dizi Dünyasına)
            is_series = "tv" in (item.title_type or "").lower() or "series" in (item.title_type or "").lower()
            if is_series and "format_series" in node_ids:
                pair = (t_id, "format_series")
                if pair not in edge_pairs:
                    edges.append(GraphEdge(
                        source=t_id,
                        target="format_series",
                        relation="has_format",
                        weight=1.8
                    ))
                    edge_pairs.add(pair)

        # 5. Üst Düzey Örüntü Bağları (Tür ➔ Tür & Yönetmen ➔ Tür)
        # Türler arası ortak bağlar
        co_genre_counter: Counter = Counter()
        for item in enriched_titles:
            clean_genres = [g.strip().capitalize() for g in item.genres if f"genre_{g.strip().lower()}" in node_ids]
            for i in range(len(clean_genres)):
                for j in range(i + 1, len(clean_genres)):
                    g1, g2 = sorted([clean_genres[i], clean_genres[j]])
                    co_genre_counter[(g1, g2)] += 1

        for (g1, g2), count in co_genre_counter.most_common(8):
            g1_id = f"genre_{g1.lower()}"
            g2_id = f"genre_{g2.lower()}"
            if g1_id in node_ids and g2_id in node_ids:
                pair = (g1_id, g2_id)
                if pair not in edge_pairs:
                    edges.append(GraphEdge(
                        source=g1_id,
                        target=g2_id,
                        relation="co_genre",
                        weight=min(3.5, 1.2 + (count * 0.3))
                    ))
                    edge_pairs.add(pair)

        return NetworkGraphResponse(
            archetype=archetype,
            nodes=nodes,
            edges=edges,
            total_nodes=len(nodes),
            total_edges=len(edges)
        )
