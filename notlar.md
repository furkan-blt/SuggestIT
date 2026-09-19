# SuggestIT - Karşılıklı Çalışma & Teknik Notlar (Notlar)

Bu dosya, proje sürecinde yaptığımız beyin fırtınalarını, teknik araştırmaları, karar süreçlerini ve canlı test sonuçlarını tuttuğumuz alandır.

---

## 📌 Mimari İlkeler & Kararlar (2026-09-19)

### 1. Eksiksiz Temsil (Zero-Exclusion İlkesi)
- **Kural:** Kullanıcının izlediği **tüm yapımlar (puanı 1 de olsa 10 da olsa) ağda yer alır.**
- **Görsel Ayrışma:**
  - Yüksek puanlılar (8-10): Parlak beyaz (#ffffff), büyük düğüm, yüksek çekim gücü.
  - Orta puanlılar (6-7.9): Normal açık gri (#cbd5e1).
  - Düşük puanlılar (<6): Kırmızımsı-pembe (#ff6b6b) - kullanıcının sevilmeyenler / negatif zevk alanını net gösteren düğümler.

### 2. Anti-Jenerik & Örüntü (Pattern) Tabanlı Bağlama
- **Kural:** "Cinema" gibi yapay, anlamsız şemsiye düğümler kesinlikle yasaklandı ve kaldırıldı.
- **Doğal Örüntüler (Patterns):**
  - **Tür Örüntüleri (Genre):** Sci-Fi, Crime, Drama, Thriller vb.
  - **Dönem / Yıl Örüntüleri (Decades):** `2020'ler`, `2010'lar`, `2000'ler`, `90'lar Klasikleri`, `80'ler`, `Klasik Dönem (<1980)`.
  - **Yönetmen Örüntüleri (Director):** Christopher Nolan, David Fincher, Quentin Tarantino, Denis Villeneuve vb.
  - **Format Örüntüsü (Format):** Dizi Dünyası (tvSeries, miniSeries).
  - Her yapım mutlaka ait olduğu **tür, dönem, yönetmen veya format** düğümlerine organik olarak bağlanır; türü bilinmese dahi dönemine ve yönetmenine bağlanarak havada kalmaz.