# SuggestIT - Backlog & Görev Takibi

Bu dosya, SuggestIT projesinde planlanan, devam eden, tamamlanan ve özellikle **yarıda bırakılan / duraklatılan** işleri takip etmek amacıyla tutulmaktadır.

---

## 📌 Durumu: Devam Eden / Yarıda Bırakılanlar (In Progress & On Hold)
> *Bir iş yarıda kesildiğinde veya askıya alındığında nerede kalındığı ve sonraki adım buraya not düşülür.*

*Henüz aktif yarıda kalan iş bulunmuyor.*

---

## 📋 Yapılacaklar (To-Do / Backlog)

### Faz 1: Çekirdek Backend & Veri Entegrasyonu
- [x] FastAPI proje iskeletinin oluşturulması
- [x] IMDb Public URL veri çekme ve parsing servisinin yazılması (`imdb_service.py`)
- [x] IMDb & Letterboxd CSV içe aktarım ve normalizasyon servisinin yazılması (`csv_service.py`)
- [x] Letterboxd canlı URL / RSS veri çekme servisi (`letterboxd_service.py`)
- [x] TMDB API istemcisi ve metadata zenginleştirici (`tmdb_service.py`)

### Faz 2: Taste Network Graph (Kullanıcı Karakter Ağ Grafiği)
- [x] Kullanıcı izleme geçmişinden Graph verisi (Nodes: Tür, Yönetmen, Yapım; Edges: Ağırlık) çıkaran backend algoritması (`graph_service.py`)
- [x] Kullanıcı için "Sinematik Zevk Arketipi" (Zihin Bükücü, Neo-Noir vb.) unvanı üreten algoritma
- [x] D3.js ile interaktif, sürükle-bırak animasyonlu ağ görselleştirmesi (`/api/v1/graph/preview`)

### Faz 3: Yapay Zeka Öneri Motoru & Çapraz Eşleşme
- [ ] Yapım özetleri ve tematik tonlar için semantik embedding vektörleri
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
- [x] Git repository başlatılması, `.gitignore` ve profesyonel `README.md` hazırlanması, ilk commit'lerin atılması (2026-09-19)
- [x] FastAPI backend çekirdek mimarisinin kurulması (`main.py`, `routes.py`, `models.py`, `imdb_service.py`, `csv_service.py`, `letterboxd_service.py`) (2026-09-19)
- [x] Gerçek IMDb AWS WAF ve Letterboxd RSS canlı URL testlerinin tamamlanması (2026-09-19)
- [x] Faz 2 Taste Network Graph ve Zevk Arketipi motorunun inşası, D3.js canlı önizleme arayüzü (`/api/v1/graph/preview`) (2026-09-19)
