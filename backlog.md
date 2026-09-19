# SuggestIT - Backlog & Görev Takibi

Bu dosya, SuggestIT projesinde planlanan, devam eden, tamamlanan ve özellikle **yarıda bırakılan / duraklatılan** işleri takip etmek amacıyla tutulmaktadır.

---

## 📌 Durumu: Devam Eden / Yarıda Bırakılanlar (In Progress & On Hold)
> *Bir iş yarıda kesildiğinde veya askıya alındığında nerede kalındığı ve sonraki adım buraya not düşülür.*

*Henüz aktif yarıda kalan iş bulunmuyor.*

---

## 📋 Yapılacaklar (To-Do / Backlog)

### Faz 1: Çekirdek Backend & Veri Entegrasyonu
- [ ] FastAPI proje iskeletinin (klasör yapısı, bağımlılıklar) oluşturulması
- [ ] IMDb Public URL (Ratings & Watchlist) CSV otomatik çekme ve ayrıştırma (parsing) servisi
- [ ] Letterboxd CSV içe aktarım ve RSS okuyucu servisi
- [ ] TMDB API istemcisi (Film/Dizi afiş, özet, tür, yönetmen meta verisi eşleme)
- [ ] Veritabanı şeması ve migration altyapısı (PostgreSQL / SQLite test ortamı)

### Faz 2: Taste Network Graph (Kullanıcı Karakter Ağ Grafiği)
- [ ] Kullanıcı izleme geçmişinden Graph verisi (Nodes: Tür, Yönetmen, Yapım; Edges: Ağırlık) çıkaran backend algoritması
- [ ] Kullanıcı için "Zevk Karakteri" unvanı/özeti üreten mantık
- [ ] Next.js üzerinde interaktif görselleştirme (D3.js / Cytoscape.js) prototipi

### Faz 3: Yapay Zeka Öneri Motoru & Çapraz Eşleşme
- [ ] Yapım özetleri ve tematik tonlar için Gemini Embeddings entegrasyonu
- [ ] Film ⇄ Dizi Çapraz Eşleşme (Cross-Domain Bridge) algoritması
- [ ] Düşük puanlı yapımlar için negatif filtreleme (ceza puanı mekanizması)
- [ ] LLM ile kişiselleştirilmiş "Neden İzlemelisin?" açıklama kartları

### Faz 4: Frontend (Next.js) & Kullanıcı Deneyimi
- [ ] Modern, koyu temalı (dark mode) film dashboard tasarımı
- [ ] IMDb URL bağlama ve Letterboxd yükleme onboarding ekranı
- [ ] Öneri akışı kartları ve filtreler (Süre, Platform, Tür, Yıl)

---

## ✅ Tamamlananlar (Done)
- [x] Proje klasörü (`SuggestIT`), `mimari.md`, `constant.md`, `notlar.md` ve `backlog.md` dosyalarının oluşturulması (2026-09-19)
- [x] Mimari kararların netleştirilmesi: FastAPI + Next.js, IMDb URL tabanlı çekim, Taste Network Graph ve Cross-Domain AI Motoru (2026-09-19)
