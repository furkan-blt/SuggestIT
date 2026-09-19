# -*- coding: utf-8 -*-
"""
Taste Network Graph — v2 algoritma
====================================
Eski mimari: Tür(hub) -> Alt-tür/Yönetmen -> Yapım şeklinde sabit,
3 seviyeli bir yıldız (star) şemasıydı. Her kullanıcı için aynı iskelet
kuruluyor, sadece etiketler değişiyordu — bu yüzden "yüzeysel" görünüyor.

Yeni mimari: TEK bir ağırlıklı, çok ilişkili (multi-relational) graf.
Şema önceden sabitlenmiyor; graf hangi düğümlerin gerçekten merkezi
olduğunu (PageRank), hangi düğümlerin iki farklı zevk kümesini
birbirine bağladığını (betweenness) ve hangi düğüm gruplarının organik
olarak bir "zevk kümesi" oluşturduğunu (Louvain community detection)
kendisi keşfediyor. Aynı iskelet + değişen veri değil; veri + gerçek
graf topolojisinden çıkan bir yapı.
"""

import math
import networkx as nx
from collections import defaultdict

# ---------------------------------------------------------------------
# 1. Kenar ağırlığı: ham "izlenme sayısı" yerine puan + güven + zaman
# ---------------------------------------------------------------------

def _rating_weight(rating: float, p: float = 2.0) -> float:
    """Yüksek puanları orantısız güçlendirir (p>1): bir 9/10, bir 6/10'un
    ~2.25 katı değil, ~3.4 katı ağırlık taşır. Böylece graf "izlenen her şey"
    değil "gerçekten sevilen şey" ağırlıklı kurulur."""
    return (max(rating, 0) / 10.0) ** p


def _recency_factor(days_since_watched, half_life_days: float = 400.0) -> float:
    """Yakın zamanda izlenen yapımlar hafifçe daha ağır basar (güncel zevki
    yansıtsın diye) ama taban 0.7'de kalır — eski klasikler asla ezilmez."""
    if days_since_watched is None:
        return 1.0
    decay = math.exp(-days_since_watched / half_life_days)
    return 0.7 + 0.3 * decay


def edge_weight(title: dict) -> float:
    return _rating_weight(title["user_rating"]) * _recency_factor(title["days_since_watched"])


# ---------------------------------------------------------------------
# 2. Graf inşası
# ---------------------------------------------------------------------

def build_taste_graph(watched_titles: list, shrinkage_k: float = 1.5) -> nx.Graph:
    """
    Düğüm tipleri: title, genre, director, decade, keyword
    Kenar: title -> {genre, director, decade, keyword}, ağırlık = edge_weight(title)

    Bayesian shrinkage: bir öznitelik (ör. bir tür) sadece 1 yapımdan
    geliyorsa, o tek yapımın puanı ne olursa olsun düğüm "aşırı güvenilir"
    görünmesin diye n/(n+k) ile küçültülür. n arttıkça (daha çok kanıt)
    güven 1'e yaklaşır.
    """
    G = nx.Graph()

    attr_incoming = defaultdict(list)  # (attr_type, attr_value) -> [edge weights]

    for t in watched_titles:
        if t.get("user_rating") is None:
            continue
        w = edge_weight(t)
        title_node = ("title", t["id"])
        G.add_node(title_node, kind="title", label=t["title"], media_type=t["media_type"],
                   rating=t["user_rating"])

        attrs = [("genre", g) for g in t["genres"]]
        attrs.append(("director", t["director"]))
        attrs.append(("decade", t["decade"]))
        attrs.extend(("keyword", k) for k in t["keywords"])

        for atype, aval in attrs:
            anode = (atype, aval)
            if not G.has_node(anode):
                G.add_node(anode, kind=atype, label=aval)
            G.add_edge(title_node, anode, weight=w)
            attr_incoming[anode].append(w)

    # Öznitelik düğümlerinin kendi "ağırlığı" (persona/boyut için) —
    # shrinkage uygulanmış toplam
    for anode, weights in attr_incoming.items():
        n = len(weights)
        confidence = n / (n + shrinkage_k)
        G.nodes[anode]["node_weight"] = sum(weights) * confidence
        G.nodes[anode]["evidence_count"] = n

    return G


# ---------------------------------------------------------------------
# 3. Yapısal analiz: merkezlik, köprü düğümler, topluluklar
# ---------------------------------------------------------------------

def analyze_graph(G: nx.Graph) -> dict:
    if G.number_of_edges() == 0:
        return dict(pagerank={}, betweenness={}, communities=[])

    pagerank = nx.pagerank(G, weight="weight")
    betweenness = nx.betweenness_centrality(G, weight="weight", normalized=True)

    # networkx >=3.3: gerçek Louvain algoritması yerleşik
    communities = nx.algorithms.community.louvain_communities(G, weight="weight", seed=42)
    return dict(pagerank=pagerank, betweenness=betweenness, communities=communities)


def bridge_nodes(G: nx.Graph, betweenness: dict, top_n: int = 3, min_evidence: int = 2) -> list:
    """İki farklı zevk kümesini birbirine bağlayan, sadece 'title' olmayan
    düğümler. Bunlar UI'da özel olarak vurgulanmalı: kullanıcıya kendi
    zevkinin altındaki gizli bağlantıyı gösterirler
    (örn: 'Villeneuve hem cyberpunk hem de suç-dram sevgini birbirine bağlıyor')."""
    candidates = [
        (node, score) for node, score in betweenness.items()
        if G.nodes[node]["kind"] != "title" and G.nodes[node].get("evidence_count", 0) >= min_evidence
    ]
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:top_n]


# ---------------------------------------------------------------------
# 4. Karakter özeti (persona) — kural tabanlı + LLM'e devredilebilir çerçeve
# ---------------------------------------------------------------------

_MOOD_PHRASES = {
    "atmospheric": "Atmosferik",
    "slow-burn": "Yavaş Yanan Gerilim",
    "moral-ambiguity": "Gri Alan Ahlakı",
    "existential": "Varoluşsal",
    "dystopia": "Distopik",
    "identity": "Kimlik Sorgulayan",
    "family": "Aile Trajedisi",
    "power": "İktidar Mücadelesi",
    "tragedy": "Trajik",
    "investigation": "Soruşturma Odaklı",
    "lighthearted": "Hafif Tonlu",
    "feel-good": "Keyifli",
    "tension": "Gerilim Yüklü",
    "descent": "Çöküş Anlatısı",
    "linguistics": "Dilbilimsel",
    "neo-noir": "Neo-Noir",
    "whimsical": "Tuhaf/Şaşırtıcı",
    "fast-paced": "Hızlı Tempolu",
}

_NOUN_BY_GENRE = {
    "Sci-fi": "Kurgu Meraklısı",
    "Mystery": "Gizem Avcısı",
    "Crime": "Suç Draması Tutkunu",
    "Drama": "Dram Okuru",
    "History": "Tarih Meraklısı",
    "War": "Savaş Anlatısı İzleyicisi",
}


def _top_labels(G, nodes, kind, limit=2):
    items = [(n, G.nodes[n].get("node_weight", 0)) for n in nodes if G.nodes[n]["kind"] == kind]
    items.sort(key=lambda x: x[1], reverse=True)
    return [G.nodes[n]["label"] for n, _ in items[:limit]]


def generate_persona(G: nx.Graph, community: set, min_titles: int = 2) -> dict:
    """Her topluluk için deterministik bir 'ham gerçek' seti üretir
    (baskın tür, baskın ton/keyword, temsilci düğümler, ortalama puan).
    Bu ham gerçekler ya kural tabanlı şablonla ya da (mimari.md'deki
    'Python deterministic + LLM interpretation' örüntüsüyle uyumlu şekilde)
    bir LLM'e verilip mizahi bir başlığa çevrilebilir.

    ÖNEMLİ: valence (positive/avoid) hesaplanır. Düşük puanlı yapımların
    kümelediği bir topluluk (ör. sevilmeyen komedi tonu) kullanıcının
    KİMLİĞİ olarak sunulmaz — bunun yerine 'kaçındığın kalıp' olarak
    ayrı gösterilmesi gerekir. Persona başlıkları sadece valence='positive'
    kümeler için üretilir."""
    title_nodes = [n for n in community if G.nodes[n]["kind"] == "title"]
    if len(title_nodes) < min_titles:
        return None

    ratings = [G.nodes[n]["rating"] for n in title_nodes]
    avg_rating = sum(ratings) / len(ratings)
    valence = "positive" if avg_rating >= 6 else "avoid"

    genres = _top_labels(G, community, "genre", limit=2)
    keywords = _top_labels(G, community, "keyword", limit=2)
    directors = _top_labels(G, community, "director", limit=1)
    titles = [G.nodes[n]["label"] for n in title_nodes]

    mood = " & ".join(_MOOD_PHRASES.get(k, k.title()) for k in keywords) or "Kendine Özgü"
    noun = _NOUN_BY_GENRE.get(genres[0], "Anlatı") if genres else "Anlatı"
    rule_based_title = f"{mood} {noun}" if valence == "positive" else f"Kaçındığın kalıp: {mood} {noun}"

    llm_prompt_facts = {
        "valence": valence,
        "avg_rating": round(avg_rating, 1),
        "dominant_genres": genres,
        "dominant_moods": keywords,
        "signature_director": directors[0] if directors else None,
        "representative_titles": titles[:4],
    }

    return dict(
        rule_based_title=rule_based_title,
        llm_prompt_facts=llm_prompt_facts,  # n8n/LLM katmanına bu JSON gönderilir
        valence=valence,
        avg_rating=round(avg_rating, 1),
        size=len(title_nodes),
    )
