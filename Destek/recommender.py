# -*- coding: utf-8 -*-
"""
Akıllı Öneri Motoru — v2 algoritma
=====================================
Eski mimari: TÜM yüksek puanlı yapımların vektörleri tek bir
"Zevk Ağırlık Merkezi"nde ortalanıyordu. Sorun: kullanıcı hem atmosferik
cyberpunk-mystery hem de klasik mafya-draması seviyorsa, tek merkez bu
ikisinin ARASINDA bir yerde (ör. "ortalama gerilim filmi") oturur —
kullanıcının GERÇEKTEN sevmediği bir bölgede. Çok yönlü zevk, ortalamayla
yok ediliyor.

Yeni mimari: Tek merkez yerine, graf üzerindeki topluluklardan (Louvain)
türeyen ÇOK merkezli (multi-centroid) zevk uzayı. Her topluluk kendi
vektör merkezine sahip; bir aday, en yakın olduğu merkeze göre puanlanır.
Buna ek olarak:
  - Graf yakınlık bonusu: aday, kullanıcının kimliğini tanımlayan
    yüksek-PageRank düğümlere (yönetmen/tür) bağlıysa ekstra puan alır.
  - Yumuşak negatif filtre: sert eleme yerine, sevilmeyen yapımlara
    anlamsal benzerlik oranında CEZA puanı düşülür.
  - Çapraz medya (dizi<->film) eşlemesi: tür vektörü yerine ayrı bir
    "anlatı DNA'sı" (tempo/karakter-odaklılık gibi ton etiketleri) alt
    vektörüyle yapılır, böylece medya tipi farkı benzerliği bozmaz.
  - MMR yeniden sıralama: en üst N aday, sadece alaka değil çeşitlilik
    de gözetilerek son listeye indirgenir (10 tane neredeyse aynı film
    önermemek için).
"""

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

# Anlatı DNA'sı için "yapısal" etiketler (tür değil, TON/TEMPO bilgisi) —
# TMDb keywords + LLM ile otomatik çıkarılabilir; burada sabit bir sözlük
# olarak alınıyor.
NARRATIVE_TAGS = {
    "slow-burn", "fast-paced", "atmospheric", "moral-ambiguity", "existential",
    "tension", "investigation", "lighthearted", "feel-good", "whimsical",
}


def _text_field(item: dict) -> str:
    # Yapılandırılmış etiketler (keywords/tür) serbest metinden (overview)
    # çok daha temiz/güvenilir bir sinyal — bu yüzden ağırlıkları daha
    # yüksek. (Prod. notunda belirtildiği gibi TF-IDF yerine gerçek bir
    # embedding modeline geçildiğinde bu manuel tekrar hilesi kalkar;
    # overview + keywords + genre ayrı ayrı embed edilip ağırlıklı
    # ortalamayla birleştirilir.)
    keywords_text = " ".join(item["keywords"])
    genres_text = " ".join(item["genres"])
    return " ".join([
        keywords_text, keywords_text, keywords_text,  # keywords 3x
        genres_text, genres_text,                      # tür 2x
        item["director"], item["director"],             # yönetmen 2x
        item["overview"],                                # overview 1x
    ])


def _narrative_text(item: dict) -> str:
    tags = [k for k in item["keywords"] if k in NARRATIVE_TAGS]
    return " ".join(tags) if tags else "neutral"


class TasteVectorSpace:
    """TF-IDF tabanlı vektör uzayı (prod. notu: bu sınıfın tek yapması
    gereken iş `vectorize(texts) -> np.ndarray`; TF-IDF yerine çok dilli
    bir sentence-transformer (ör. paraphrase-multilingual-mpnet) ya da
    OpenAI/Voyage embedding API'si takılabilir — geri kalan algoritma
    değişmeden çalışır)."""

    def __init__(self, all_items: list):
        self.items = {it["id"]: it for it in all_items}
        texts = [_text_field(it) for it in all_items]
        narr_texts = [_narrative_text(it) for it in all_items]

        self.vec = TfidfVectorizer(min_df=1)
        self.matrix = self.vec.fit_transform(texts)

        self.narr_vec = TfidfVectorizer(min_df=1)
        self.narr_matrix = self.narr_vec.fit_transform(narr_texts)

        self.id_index = {it["id"]: i for i, it in enumerate(all_items)}

    def embedding(self, item_id):
        return self.matrix[self.id_index[item_id]]

    def narrative_embedding(self, item_id):
        return self.narr_matrix[self.id_index[item_id]]


def build_cluster_centroids(space: TasteVectorSpace, communities: list, G) -> dict:
    """Her Louvain topluluğundaki 'title' düğümlerinden, puan-ağırlıklı
    centroid çıkarır. Topluluk çok küçükse (<2 title) o topluluk atlanır."""
    centroids = {}
    for idx, community in enumerate(communities):
        title_ids = [n[1] for n in community if G.nodes[n]["kind"] == "title"]
        if len(title_ids) < 2:
            continue
        vecs, weights = [], []
        for tid in title_ids:
            rating = G.nodes[("title", tid)]["rating"]
            vecs.append(space.embedding(tid).toarray()[0])
            weights.append((rating / 10.0) ** 2)
        weights = np.array(weights)
        centroid = np.average(np.vstack(vecs), axis=0, weights=weights)
        centroids[idx] = dict(vector=centroid, title_ids=title_ids,
                               confidence=min(1.0, len(title_ids) / 4))
    return centroids


def negative_profile(space: TasteVectorSpace, disliked_items: list):
    vecs, penalties = [], []
    for it in disliked_items:
        if it["id"] not in space.id_index:
            continue
        vecs.append(space.embedding(it["id"]).toarray()[0])
        penalties.append((5 - it["user_rating"]) / 4.0)  # 1->1.0, 4->0.25
    return vecs, penalties


def score_candidates(space: TasteVectorSpace, centroids: dict, watched_by_id: dict,
                      candidates: list, G, pagerank: dict,
                      neg_vecs, neg_penalties,
                      lambda_graph: float = 0.15, lambda_neg: float = 0.35,
                      lambda_novelty: float = 0.05) -> list:
    results = []
    watched_vecs = {tid: space.embedding(tid).toarray()[0] for tid in watched_by_id}

    for cand in candidates:
        if cand["id"] not in space.id_index:
            continue
        cvec = space.embedding(cand["id"]).toarray()[0].reshape(1, -1)
        cnarr = space.narrative_embedding(cand["id"]).toarray()[0].reshape(1, -1)

        # 1) En yakın merkezle semantik benzerlik (çok merkezli zevk uzayı)
        best_cluster, best_sim = None, -1.0
        for cid, c in centroids.items():
            sim = cosine_similarity(cvec, c["vector"].reshape(1, -1))[0, 0]
            sim *= c["confidence"]
            if sim > best_sim:
                best_sim, best_cluster = sim, cid

        # 1b) Çapraz medya: aynı skor, ama medya tipi farklıysa anlatı-DNA
        # benzerliğiyle de kontrol edilip max'ı alınıyor (dizi<->film köprüsü)
        cross_media_bonus = 0.0
        if best_cluster is not None:
            member_ids = centroids[best_cluster]["title_ids"]
            different_media = [tid for tid in member_ids
                                if watched_by_id[tid]["media_type"] != cand["media_type"]]
            if different_media:
                narr_sims = [
                    cosine_similarity(cnarr, space.narrative_embedding(tid).toarray()[0].reshape(1, -1))[0, 0]
                    for tid in different_media
                ]
                cross_media_bonus = 0.1 * max(narr_sims)

        # 2) Graf yakınlığı: aday, kullanıcının yüksek-PageRank düğümleriyle
        #    (tür/yönetmen) ne kadar örtüşüyor?
        shared_nodes = []
        for gval in cand["genres"]:
            n = ("genre", gval)
            if n in pagerank:
                shared_nodes.append(pagerank[n])
        dnode = ("director", cand["director"])
        if dnode in pagerank:
            shared_nodes.append(pagerank[dnode] * 1.5)  # yönetmen eşleşmesi daha güçlü sinyal
        graph_bonus = lambda_graph * sum(shared_nodes)

        # 3) Yumuşak negatif ceza
        penalty = 0.0
        if neg_vecs:
            sims = cosine_similarity(cvec, np.vstack(neg_vecs))[0]
            penalty = lambda_neg * float(np.max(sims * np.array(neg_penalties)))

        # 4) Keşif bonusu: izlenenlerin hiçbirine aşırı yakın değilse (tekrar
        #    değil, aynı damarda YENİ bir şey) küçük bir bonus
        watched_sims = cosine_similarity(cvec, np.vstack(list(watched_vecs.values())))[0]
        novelty = lambda_novelty * (1 - float(np.max(watched_sims)))

        final_score = best_sim + graph_bonus + cross_media_bonus - penalty + novelty

        results.append(dict(
            id=cand["id"], title=cand["title"], media_type=cand["media_type"],
            score=round(float(final_score), 4),
            best_cluster=best_cluster,
            semantic_sim=round(float(best_sim), 4),
            graph_bonus=round(float(graph_bonus), 4),
            cross_media_bonus=round(float(cross_media_bonus), 4),
            penalty=round(float(penalty), 4),
            novelty=round(float(novelty), 4),
            vector=cvec[0],
        ))

    results.sort(key=lambda r: r["score"], reverse=True)
    return results


def mmr_rerank(scored: list, top_n: int = 5, diversity: float = 0.3) -> list:
    """Maximal Marginal Relevance: en üst N sonucu seçerken, zaten seçilmiş
    sonuçlara aşırı benzeyen adayları geriye iter. `diversity` (0-1) ne
    kadar yüksekse çeşitlilik o kadar öncelikli."""
    if not scored:
        return []
    selected, remaining = [scored[0]], scored[1:]
    while remaining and len(selected) < top_n:
        best_idx, best_val = None, -1e9
        for i, cand in enumerate(remaining):
            sim_to_selected = max(
                cosine_similarity(cand["vector"].reshape(1, -1), s["vector"].reshape(1, -1))[0, 0]
                for s in selected
            )
            mmr_val = (1 - diversity) * cand["score"] - diversity * sim_to_selected
            if mmr_val > best_val:
                best_val, best_idx = mmr_val, i
        selected.append(remaining.pop(best_idx))
    return selected


def explain(result: dict, centroids: dict, G, watched_by_id: dict) -> str:
    """Deterministik 'neden izlemelisin' gerekçesi — gerçek graf/skor
    sinyallerinden üretilir, LLM'e bu ham gerekçe JSON olarak verilip
    doğal bir cümleye çevrilebilir (mimari.md'deki LLM açıklama katmanı)."""
    facts = []
    if result["best_cluster"] is not None and result["semantic_sim"] > 0:
        member_titles = [watched_by_id[t]["title"] for t in centroids[result["best_cluster"]]["title_ids"]]
        facts.append(f"tema/ton olarak en çok '{', '.join(member_titles[:2])}' kümenle örtüşüyor")
    if result["graph_bonus"] > 0.05:
        facts.append("senin zevkinde merkezi bir tür/yönetmenle doğrudan bağlantılı")
    if result["cross_media_bonus"] > 0:
        facts.append("izlediğin bir yapımla aynı anlatı temposunu (dizi<->film) taşıyor")
    if result["novelty"] > 0.05:
        facts.append("bildiğin damarda ama henüz keşfetmediğin bir açıdan")
    if result["penalty"] > 0.1:
        facts.append("(uyarı: sevmediğin bazı temalarla örtüşme var)")
    if not facts:
        facts.append("genel zevk profilinle orta düzey uyum gösteriyor")
    return "; ".join(facts)
