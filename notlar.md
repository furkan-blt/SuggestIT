# SuggestIT - Karşılıklı Çalışma & Teknik Notlar (Notlar)

Bu dosya, proje sürecinde yaptığımız beyin fırtınalarını, teknik araştırmaları, karar süreçlerini ve henüz netleşmemiş fikir alışverişlerini canlı olarak tuttuğumuz alandır.

---

## 📌 Alınan Kararlar (2026-09-19)

1. **Teknoloji Yığını Onayı:**
   - Backend: **Python (FastAPI)**
   - Frontend: **Next.js (React + TypeScript)**
   - Veritabanı: **PostgreSQL + pgvector**

2. **IMDb Entegrasyon Stratejisi:**
   - Doğrudan web scraping yerine **Kullanıcı URL'si üzerinden otomatik çekim** kararlaştırıldı.
   - Kullanıcının herkese açık (public) **Ratings** ve **Watchlist** linkleri alınacak; arkasındaki yerleşik CSV export mekanizmasıyla arka planda tek tıkla indirilecek.

3. **Özgün Değer Katmanı - Taste Network Graph (Kullanıcı Karakter Ağ Grafiği):**
   - Kullanıcının film/dizi izleme ve beğenme verilerinden kişisel bir grafik ağı (Nodes: Türler, Yönetmenler, Başlıklar; Edges: Puan ve izleme sıklığı ağırlıkları) üretilecek.
   - Görselleştirme: Frontend'de D3.js veya Cytoscape.js ile interaktif, yaşayan bir evren olarak sunulacak.

4. **Yapay Zeka ve Çapraz Eşleşme (Cross-Domain Bridge):**
   - Dizi bitiren kullanıcıya dizi hissi veren filmler; film sevene benzer tonda mini diziler eşleştirilecek.
   - Semantik Vektörler (Gemini Embeddings) + Negatif Filtreleme (düşük puanlıların sevilmeyen unsurlarını eleme) + LLM destekli "Neden İzlemelisin?" metinleri.

---

## 💡 Sonraki Fikir Alışverişleri & Araştırma Konuları
- Network Graph için node ağırlıklandırma formülü (Örn: `Ağırlık = (İzleme Sayısı * 0.4) + (Ortalama Puan * 0.6)`).
- TMDB API anahtarının backend'e entegrasyonu ve cache mekanizması.
- IMDb URL formatlarının regex ile doğrulanması (`imdb.com/user/ur.../ratings` vb.).