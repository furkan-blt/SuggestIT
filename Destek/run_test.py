# -*- coding: utf-8 -*-
import sys
from data import WATCHED, CANDIDATES, HELD_OUT
from graph_builder import build_taste_graph, analyze_graph, bridge_nodes, generate_persona
from recommender import TasteVectorSpace, build_cluster_centroids, negative_profile, score_candidates, mmr_rerank, explain

def main():
    watched_by_id = {t["id"]: t for t in WATCHED}
    disliked = [t for t in WATCHED if t["user_rating"] is not None and t["user_rating"] <= 4]

    print("=" * 70)
    print("1) GRAF İNŞASI")
    print("=" * 70)
    G = build_taste_graph(WATCHED)
    print(f"Düğüm sayısı: {G.number_of_nodes()}  |  Kenar sayısı: {G.number_of_edges()}")

    analysis = analyze_graph(G)
    pagerank = analysis["pagerank"]
    betweenness = analysis["betweenness"]
    communities = analysis["communities"]

    print(f"\nBulunan topluluk (küme) sayısı: {len(communities)}")
    for i, c in enumerate(communities):
        titles = sorted([G.nodes[n]["label"] for n in c if G.nodes[n]["kind"] == "title"])
        genres = sorted(set(G.nodes[n]["label"] for n in c if G.nodes[n]["kind"] == "genre"))
        if not titles:
            continue
        print(f"  Küme {i}: türler={genres}  |  başlıklar={titles}")

    print("\n--- En yüksek PageRank'e sahip 8 düğüm (gerçek merkezilik) ---")
    top_pr = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:8]
    for node, score in top_pr:
        kind, label = node[0], G.nodes[node]["label"]
        print(f"  [{kind:8s}] {label:28s} pagerank={score:.4f}")

    print("\n--- Köprü (bridge) düğümler: iki zevk kümesini birbirine bağlayan ---")
    for node, score in bridge_nodes(G, betweenness, top_n=3):
        print(f"  [{node[0]}] {G.nodes[node]['label']}  betweenness={score:.4f}")

    print("\n--- Karakter özeti (persona) her küme için ---")
    personas = []
    for i, c in enumerate(communities):
        p = generate_persona(G, c)
        if p is None:
            continue
        personas.append((i, p))
        tag = "[KİMLİK]" if p["valence"] == "positive" else "[KAÇINILAN KALIP]"
        print(f"  Küme {i} {tag} (ort. puan {p['avg_rating']}): \"{p['rule_based_title']}\"")
        print(f"           LLM'e gidecek ham veri: {p['llm_prompt_facts']}")

    print("\n" + "=" * 70)
    print("2) ÖNERİ MOTORU")
    print("=" * 70)

    all_items = WATCHED + CANDIDATES + HELD_OUT
    space = TasteVectorSpace(all_items)
    centroids = build_cluster_centroids(space, communities, G)
    print(f"Merkez (centroid) sayısı: {len(centroids)}")

    neg_vecs, neg_penalties = negative_profile(space, disliked)

    candidate_pool = CANDIDATES + HELD_OUT  # held-out'lar gerçek hayatta "puanı bilinmeyen" gibi davranıyor
    scored = score_candidates(space, centroids, watched_by_id, candidate_pool, G, pagerank,
                               neg_vecs, neg_penalties)

    print("\n--- Ham skorlar (tüm aday havuzu, azalan sırada) ---")
    for r in scored:
        flag = "  <-- HELD-OUT (gerçekte kullanıcı bunu 9-10 puanlamıştı)" if r["id"].startswith("h") else ""
        print(f"  {r['score']:+.3f}  {r['title']:26s} sem={r['semantic_sim']:.3f} "
              f"graph={r['graph_bonus']:.3f} cross={r['cross_media_bonus']:.3f} "
              f"neg={-r['penalty']:.3f} nov={r['novelty']:.3f}{flag}")

    top5 = mmr_rerank(scored, top_n=5, diversity=0.3)
    print("\n--- MMR ile çeşitlilik gözetilerek seçilen ilk 5 öneri ---")
    for rank, r in enumerate(top5, 1):
        reason = explain(r, centroids, G, watched_by_id)
        print(f"  {rank}. {r['title']} ({r['media_type']}) — skor {r['score']:.3f}")
        print(f"     Neden izlemelisin: {reason}")

    print("\n" + "=" * 70)
    print("3) LEAVE-K-OUT DOĞRULAMA (gerçek sevilen ama 'bilinmiyor' varsayılan 2 başlık)")
    print("=" * 70)
    ranks = {r["id"]: i + 1 for i, r in enumerate(scored)}
    for h in HELD_OUT:
        r = ranks.get(h["id"])
        total = len(scored)
        print(f"  '{h['title']}' -> {total} adaylık havuzda sıra: {r}  "
              f"({'ÜST %30' if r and r <= max(1, total*0.3) else 'düşük sıra'})")

    print("\n--- Negatif filtre kontrolü: düşük puanlı komedi profiliyle örtüşen adaylar cezalanmalı ---")
    for r in scored:
        if r["id"] in ("c5", "c6"):
            print(f"  {r['title']}: penalty={r['penalty']:.3f}  final_score={r['score']:.3f}")

if __name__ == "__main__":
    main()
