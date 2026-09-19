## 4. Çekirdek Özellikler & Fonksiyonel Tasarım (v2)

> Bu bölüm mevcut mimari.md'deki 4.1 ve 4.2'nin yerine geçer. Eski tasarım
> her kullanıcı için aynı sabit şemayı (Tür → Yönetmen → Yapım) dolduruyordu;
> yeni tasarımda şema veriden çıkıyor — graf, kullanıcının verisine bakıp
> kendi topolojisini keşfediyor. Referans implementasyon ve uçtan uca test:
> `taste_engine/` klasörü (graph_builder.py, recommender.py, data.py, run_test.py).

### 4.1 Kullanıcı Karakter Haritası (Taste Network Graph)

Tek bir **ağırlıklı, çok ilişkili graf** üzerine kurulu. Düğüm tipleri
önceden sabitlenmiyor (Tür/Yönetmen/Yapım gibi 3 katman) — `title`,
`genre`, `director`, `decade`, `keyword` (TMDb keywords/tema-ton etiketi)
aynı graf içinde birlikte var oluyor ve gerçek yapı, graf analizinden
ortaya çıkıyor:

* **Kenar ağırlığı** — ham izlenme sayısı değil:
  `weight = (puan/10)^2 × recency_factor`
  Yüksek puanlar üssel olarak daha ağır basar (bir 9/10, bir 6/10'un
  ~3.4 katı ağırlık taşır — "izlenen her şey" değil "gerçekten sevilen
  şey" ağırlıklı graf). `recency_factor`, yakın zamanda izlenenleri hafif
  öne çıkarır ama tabanı 0.7'de tutarak klasikleri ezmez.
* **Bayesian shrinkage** — bir özniteliğin (ör. bir tür) düğüm ağırlığı,
  kanıt sayısı arttıkça güvenilirlik kazanır (`n/(n+k)`). Tek bir 10/10
  puanlı nadir tür, kalıcı bir "kimlik" gibi görünmez.
* **Gerçek merkezilik (PageRank)** — düğüm boyutu artık ham derece/sayım
  değil, ağırlıklı PageRank. Bir düğüm sadece çok bağlantılıysa değil,
  *önemli düğümlere* bağlıysa büyür.
* **Topluluk tespiti (Louvain)** — graf, önceden tanımlanmış "tür kümeleri"
  değil, organik olarak oluşan **zevk toplulukları** buluyor. Bir topluluk
  genellikle birden fazla türü, bir yönetmeni ve birkaç ton etiketini aynı
  anda kapsar (ör. "Mystery + Sci-fi + atmospheric + existential +
  Villeneuve" tek bir gerçek küme olarak çıkıyor — şema onu önceden
  dayatmıyor, veri kendisi gösteriyor).
* **Köprü (bridge) düğümler** — betweenness centrality ile, iki farklı
  zevk topluluğunu birbirine bağlayan düğümler tespit ediliyor (ör. bir
  on yıl, bir tür ya da bir ton etiketi). UI'da özel vurgulanmalı: "işte
  senin X zevkinle Y zevkini birbirine bağlayan şey bu."
* **Karakter Özeti (Persona)** — her pozitif-valence topluluk için
  deterministik ham gerçekler (baskın tür/ton/yönetmen + ortalama puan)
  çıkarılır; bunlar kural tabanlı bir şablonla ya da mimari.md'nin genel
  desenine uygun şekilde bir LLM'e verilip mizahi bir unvana çevrilir.
  **Önemli fark:** düşük puanlı yapımların kümelediği topluluklar
  (`valence = "avoid"`) kimlik olarak sunulmaz — "Kaçındığın Kalıp" olarak
  ayrı gösterilir. Bu, hem daha doğru hem de UI'da ilginç bir ikinci
  panel fırsatı: "Seni Tanımlayan" vs. "Senden Kaçınan".

### 4.2 Akıllı Öneri Motoru (Recommendation Engine)

1. **Çok merkezli zevk uzayı** (tek "Zevk Ağırlık Merkezi" değil): eski
   tasarımda tüm yüksek puanlı yapımlar tek bir vektörde ortalanıyordu —
   kullanıcı hem atmosferik cyberpunk-mystery hem klasik mafya-draması
   seviyorsa, tek merkez ikisinin ARASINDA, kullanıcının aslında sevmediği
   bir bölgede oturuyordu. Yeni tasarımda her Louvain topluluğu kendi
   puan-ağırlıklı centroid'ine sahip; bir aday, **en yakın olduğu merkeze**
   göre puanlanır.
2. **Graf yakınlık bonusu**: aday, kullanıcının kimliğini tanımlayan
   yüksek-PageRank düğümlere (tür/yönetmen) bağlıysa ekstra puan alır —
   sadece embedding benzerliği değil, graf yapısı da öneriyi besler.
3. **Çapraz eşleşme (Dizi ⇄ Film)**: tür vektörü yerine ayrı bir
   *"anlatı DNA'sı"* alt vektörü (tempo/ton etiketleri: slow-burn,
   fast-paced, atmospheric, moral-ambiguity, vb.) kullanılıyor. Bir
   topluluktaki farklı medya tipinden üyelerle bu alt vektör üzerinden
   ayrıca karşılaştırma yapılıp bonus ekleniyor — medya tipi farkı
   benzerliği artık bozmuyor.
4. **Yumuşak negatif filtreleme**: sert eleme yerine, düşük puanlı
   yapımlara anlamsal benzerlik oranında **ceza puanı**:
   `penalty = benzerlik × (5-puan)/4`. Bir aday sadece uzaktan bir ortak
   temaya sahipse hafif cezalanır; tamamen örtüşüyorsa ağır cezalanır.
5. **Keşif (novelty) bonusu**: izlenenlerin hiçbirine aşırı yakın olmayan
   adaylar (aynı damarda ama tekrar olmayan) küçük bir bonus alır —
   "hep aynı şeyi öneren" motor riskini azaltır.
6. **MMR yeniden sıralama**: son Top-N liste, sadece skora göre değil,
   Maximal Marginal Relevance ile **çeşitlilik** de gözetilerek
   seçiliyor — 5 önerinin hepsi aynı kümeden gelmiyor.
7. **"Neden İzlemelisin?" katmanı**: gerekçe artık serbest LLM
   halüsinasyonu değil, skorlama sürecinin ürettiği **gerçek sinyallerden**
   (hangi küme eşleşti, hangi merkezi düğüm paylaşıldı, hangi izlenen
   yapıma en yakın, çapraz-medya bonusu var mı) deterministik olarak
   çıkarılıyor; bu yapılandırılmış gerçekler isteğe bağlı olarak bir LLM'e
   verilip doğal cümleye çevrilebilir — ama her cümle gerçek bir veriye
   dayanıyor.

**Doğrulama yöntemi (leave-k-out):** Kullanıcının yüksek puanlı 2 yapımı
graf/embedding'den gizlenip "puanı bilinmiyor" gibi aday havuzuna atıldı.
İlk testte biri düşük sıraya düştü — sebep araştırıldı ve serbest metin
(overview) ağırlığının, yapılandırılmış etiketlerden (keywords/tür) daha
fazla söz sahibi olması olduğu bulundu. Ağırlıklandırma düzeltildikten
(`keywords ×3, tür ×2, yönetmen ×2, overview ×1`) sonra iki gizli yapım da
aday havuzunun üst yarısına, biri #1 sıraya çıktı. Bu, prod'a geçerken
**gerçek embedding modeli kullanmanın** (bkz. Prod. Notu) TF-IDF'e göre
neden fark yaratacağını da gösteriyor.

**Prod. Notu:** Referans implementasyon `TfidfVectorizer` kullanıyor —
mimariyi test etmek için yeterli, ama TF-IDF sadece kelime örtüşmesine
bakıyor, anlam benzerliğine değil. Gerçek sisteme geçerken tek değişmesi
gereken yer `TasteVectorSpace.vectorize()` — çok dilli bir
sentence-transformer (ör. `paraphrase-multilingual-mpnet-base-v2`) ya da
bir embedding API'si (OpenAI/Voyage) ile değiştirilebilir; n8n'deki
mevcut "Python deterministic + LLM interpretation" mimarine uygun şekilde
bu adım da bir HTTP node ile n8n akışına bağlanabilir.
