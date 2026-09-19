# SuggestIT - Değişmezler & Çekirdek İlkeler (Constants)

Bu dosya, projenin mimari ve iş modeli açısından **tartışmaya kapalı, temel ve değişmez ilkelerini (Ground Truth)** içerir. Proje boyunca alınacak tüm teknik ve tasarımsal kararlar buradaki kurallarla çelişmemelidir.

---

## 1. Çekirdek Amaç & Vizyon
- **Tek Odak Noktası:** Kullanıcının geçmiş izleme ve beğeni verisini (IMDb / Letterboxd) temel alarak, yüksek isabet oranına sahip, açıklanabilir ve kişiselleştirilmiş film/dizi önerileri sunmak.
- **Şeffaflık İlkesi ("Explainable AI"):** Her önerinin arkasında mutlaka kullanıcıya sunulan mantıklı bir "Neden bu önerildi?" açıklaması yer almalıdır (Örn: *"X yönetmenini ve neo-noir türünü sevdiğin için"*).

## 2. Veri & Kullanıcı Hakları
- **Platform Bağımsızlığı:** Sistem yalnızca tek bir platforma bağımlı kalmayacak; hem Letterboxd hem IMDb (ve ileride diğer servisler) birinci sınıf vatandaş (first-class citizen) olarak kabul edilecektir.
- **Kullanıcı Veri Mahremiyeti:** Kullanıcının içe aktardığı veya bağladığı izleme geçmişi verisi yalnızca kullanıcıya öneri üretmek ve analiz sağlamak için kullanılacaktır.

## 3. Mimari & Teknik Standartlar
- **Modülerlik & Genişletilebilirlik:** Öneri motoru (Recommendation Engine) veri kaynağından (Scraper / CSV Parser / API) tamamen izole olmalıdır. Veri kaynağı değişse bile öneri mantığı bozulmamalıdır.
- **Kesintisiz Deneyim:** Harici servisler (Letterboxd, IMDb, TMDB vb.) çökse, yavaşlasa veya erişim kısıtlaması koysa dahi sistem kendi veritabanındaki önbellek ve temel verilerle çalışmaya devam edebilmelidir.
- **Kademeli Yükleme & Performans:** Sayfa açılışında ağır yapay zeka hesaplamaları kullanıcıyı bekletmemeli; öneriler asenkron olarak üretilip önbelleğe (cache) alınmalıdır.
