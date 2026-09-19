# SuggestIT - Değişmezler & Çekirdek İlkeler (Constants)

Bu dosya, projenin mimari ve iş modeli açısından **tartışmaya kapalı, temel ve değişmez ilkelerini (Ground Truth)** içerir. Proje boyunca alınacak tüm teknik ve tasarımsal kararlar buradaki kurallarla çelişmemelidir.

---

## 1. Çekirdek Amaç & Vizyon
- **Tek Odak Noktası:** Kullanıcının geçmiş izleme ve beğeni verisini (IMDb / Letterboxd) temel alarak, yüksek isabet oranına sahip, açıklanabilir ve kişiselleştirilmiş film/dizi önerileri sunmak.
- **Şeffaflık İlkesi ("Explainable AI"):** Her önerinin arkasında mutlaka kullanıcıya sunulan mantıklı bir "Neden bu önerildi?" açıklaması yer almalıdır (Örn: *"X yönetmenini ve neo-noir türünü sevdiğin için"*).

## 2. Taste Network Graph (Zevk Ağı) Değişmezleri
- **Eksiksiz Temsil Kuralı:** Kullanıcının izlediği **tüm yapımlar (puanı ne olursa olsun) ağda yer almalıdır.** Yüksek puanlılarla sınırlama yapılamaz; kullanıcının 2 puan verdiği yapım da onun sinema karakterinin (negatif zevk alanının) bir parçasıdır. Puanlar düğümün boyutunu, parlaklığını veya rengini etkileyebilir ancak yapımı ağdan silemez.
- **Organik Bağlantı Kuralı (Anti-Jenerik İlkesi):** Sisteme sahte, anlamsız veya jenerik şemsiye düğümler (Örn: *"Cinema"*, *"Movie"* vb.) **kesinlikle eklenemez.** Her yapım gerçek **türler (genres)**, **yönetmenler** veya **yapım türü (Dizi / Film)** gibi somut örüntülerle (pattern) ağa bağlanmalıdır.

## 3. Veri & Kullanıcı Hakları
- **Platform Bağımsızlığı:** Sistem yalnızca tek bir platforma bağımlı kalmayacak; hem Letterboxd hem IMDb birinci sınıf vatandaş olarak kabul edilecektir.
- **Kullanıcı Veri Mahremiyeti:** Kullanıcının içe aktardığı veya bağladığı izleme geçmişi verisi yalnızca kullanıcıya öneri üretmek ve analiz sağlamak için kullanılacaktır.

## 4. Mimari & Teknik Standartlar
- **Modülerlik & Genişletilebilirlik:** Öneri motoru veri kaynağından tamamen izole olmalıdır. Veri kaynağı değişse bile öneri mantığı bozulmamalıdır.
- **Kesintisiz Deneyim:** Harici servisler kısıtlama koysa dahi sistem yerel sözlükler, önbellek ve CSV içe aktarma mekanizmalarıyla çalışmaya devam edebilmelidir.
