# SuggestIT - Karşılıklı Çalışma & Teknik Notlar (Notlar)

Bu dosya, proje sürecinde yaptığımız beyin fırtınalarını, teknik araştırmaları, karar süreçlerini ve canlı test sonuçlarını tuttuğumuz alandır.

---

## 🔬 URL Testi & Canlı Araştırma Sonuçları (2026-09-19)

### 1. IMDb URL Testi & AWS WAF Engeli
- **Gerçek Test:** `IMDbService.sync_from_url` gerçek IMDb herkese açık liste ve profil URL'leri (`imdb.com/list/...` ve `imdb.com/user/ur.../ratings`) ile test edildi.
- **Sonuç:** IMDb sunucuları doğrudan HTTP GET isteklerine (Python requests, httpx veya curl) `HTTP 202 / 403 Forbidden` yanıtı döndürüyor.
- **Teşhis:** Sayfada `window.awsWafCookieDomainList = ['imdb.com']` ve `challenge.js` scripti çalışıyor. Amazon Web Services WAF (Web Application Firewall), JavaScript çalıştırmayan istemcileri doğrudan bot olarak sınıflandırıp engelliyor.
- **Mimari Çözüm:** 
  - Kullanıcı IMDb kullanıyorsa, masaüstünden indirdiği `ratings.csv` veya `watchlist.csv` dosyasını arayüze sürükleyecek (CSV parser'ımız bunu saliseler içinde kusursuz çözüyor).

---

### 2. Letterboxd URL Canlı Testi (BÜYÜK BAŞARI!)
- **Gerçek Test:** Popüler Letterboxd kullanıcı profili (`letterboxd.com/dave` veya kullanıcı adı `dave`) üzerinden test yapıldı.
- **Sonuç:** `HTTP 200 OK` ile **100 adet film, çıkış yılları, kullanıcının verdiği 5'lik puanlar (10'luk sisteme çevrildi) ve hatta TMDB ID'leri** tek istekte 0.2 saniyede başarıyla çekildi!
- **Yeni Uç Nokta Eklendi:** `POST /api/v1/sync/letterboxd-url` servisi doğrudan canlıya alındı ve API testleri başarıyla geçti (`[SUCCESS]`).