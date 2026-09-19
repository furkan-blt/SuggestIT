# -*- coding: utf-8 -*-
"""
Sentetik test verisi.
Gerçek sistemde bu veriler TMDb API + kullanıcının IMDb export'undan gelecek.
Burada, ekran görüntüsündeki düğümlerden (Blade Runner 2049, Denis Villeneuve,
The Godfather Part II, Francis Ford Coppola, Nuremberg, vb.) esinlenilmiş,
algoritmayı uçtan uca test edebileceğimiz kadar zengin bir set kuruldu.

Her kayıt:
  id, title, media_type ("movie"/"series"), genres[], director,
  decade (yapımın ait olduğu on yıl), keywords[] (tema/ton etiketleri —
  TMDb keywords benzeri), overview (kısa metin, embedding/TF-IDF girdisi),
  user_rating (None ise izlenmemiş/aday havuzu), days_since_watched
"""

WATCHED = [
    # --- Villeneuve / atmosferik sci-fi / mystery kümesi ---
    dict(id="t1", title="Blade Runner 2049", media_type="movie",
         genres=["Sci-fi", "Mystery", "Drama"], director="Denis Villeneuve",
         decade="2010s", keywords=["dystopia", "identity", "slow-burn", "atmospheric", "neo-noir", "existential"],
         overview="A replicant detective uncovers a buried secret that threatens to unravel society, "
                  "moving through a melancholic, rain-soaked future city.",
         user_rating=9, days_since_watched=40),
    dict(id="t2", title="Arrival", media_type="movie",
         genres=["Sci-fi", "Mystery", "Drama"], director="Denis Villeneuve",
         decade="2010s", keywords=["identity", "atmospheric", "existential", "linguistics", "slow-burn"],
         overview="A linguist is recruited to communicate with alien visitors, and the encounter reshapes "
                  "her understanding of time and loss.",
         user_rating=9, days_since_watched=200),
    dict(id="t3", title="Prisoners", media_type="movie",
         genres=["Mystery", "Crime", "Drama"], director="Denis Villeneuve",
         decade="2010s", keywords=["moral-ambiguity", "slow-burn", "atmospheric", "grief", "investigation"],
         overview="A father takes matters into his own hands after his daughter disappears, spiraling into "
                  "a grim moral investigation.",
         user_rating=8, days_since_watched=300),
    dict(id="t4", title="Sicario", media_type="movie",
         genres=["Crime", "Mystery", "Drama"], director="Denis Villeneuve",
         decade="2010s", keywords=["moral-ambiguity", "atmospheric", "tension", "slow-burn"],
         overview="An idealistic FBI agent is pulled into a morally murky task force operation on the border.",
         user_rating=8, days_since_watched=500),

    # --- Coppola / klasik dönem crime-drama kümesi ---
    dict(id="t5", title="The Godfather Part II", media_type="movie",
         genres=["Crime", "Drama"], director="Francis Ford Coppola",
         decade="1970s", keywords=["family", "power", "tragedy", "slow-burn", "moral-ambiguity"],
         overview="The rise of a young patriarch and the moral decay of his son are told in parallel across generations.",
         user_rating=10, days_since_watched=60),
    dict(id="t6", title="The Godfather", media_type="movie",
         genres=["Crime", "Drama"], director="Francis Ford Coppola",
         decade="1970s", keywords=["family", "power", "tragedy", "slow-burn"],
         overview="A mafia patriarch hands control of his empire to his reluctant son.",
         user_rating=10, days_since_watched=400),
    dict(id="t7", title="Apocalypse Now", media_type="movie",
         genres=["Drama", "War"], director="Francis Ford Coppola",
         decade="1970s", keywords=["moral-ambiguity", "descent", "atmospheric", "existential"],
         overview="A soldier travels upriver into the chaos of war to confront a renegade colonel, and himself.",
         user_rating=9, days_since_watched=650),
    dict(id="t8", title="Goodfellas", media_type="movie",
         genres=["Crime", "Drama"], director="Martin Scorsese",
         decade="1990s", keywords=["family", "power", "tragedy", "fast-paced", "moral-ambiguity"],
         overview="A mobster's rise and fall is narrated with kinetic energy and dark humor.",
         user_rating=9, days_since_watched=120),

    # --- Savaş / tarihi dram kümesi (Nuremberg, Oppenheimer tarzı) ---
    dict(id="t9", title="Oppenheimer", media_type="movie",
         genres=["Drama", "History"], director="Christopher Nolan",
         decade="2020s", keywords=["moral-ambiguity", "existential", "tension", "atmospheric", "power"],
         overview="The father of the atomic bomb grapples with the moral weight of his creation.",
         user_rating=9, days_since_watched=15),
    dict(id="t10", title="Nuremberg", media_type="movie",
         genres=["Drama", "History"], director="James Vanderbilt",
         decade="2020s", keywords=["moral-ambiguity", "tension", "power", "investigation"],
         overview="A psychiatrist evaluates a Nazi leader ahead of the Nuremberg trials, probing the nature of evil.",
         user_rating=8, days_since_watched=5),

    # --- Hafif / negatif filtre için düşük puanlar ---
    dict(id="t11", title="Just Go with It", media_type="movie",
         genres=["Comedy", "Romance"], director="Dennis Dugan",
         decade="2010s", keywords=["lighthearted", "fast-paced", "feel-good"],
         overview="A plastic surgeon's white lie spirals into an elaborate romantic farce.",
         user_rating=3, days_since_watched=900),
    dict(id="t12", title="The Spy Next Door", media_type="movie",
         genres=["Comedy", "Family"], director="Brian Levant",
         decade="2010s", keywords=["lighthearted", "feel-good", "fast-paced"],
         overview="A secret agent poses as an ordinary neighbor to win over his girlfriend's kids.",
         user_rating=4, days_since_watched=800),

    # --- Diziler (çapraz eşleştirme testi için) ---
    dict(id="s1", title="True Detective (S1)", media_type="series",
         genres=["Mystery", "Crime", "Drama"], director="Cary Fukunaga",
         decade="2010s", keywords=["moral-ambiguity", "atmospheric", "slow-burn", "existential", "investigation"],
         overview="Two detectives revisit a decades-old occult murder case that unravels their own sense of self.",
         user_rating=10, days_since_watched=250),
    dict(id="s2", title="The Sopranos", media_type="series",
         genres=["Crime", "Drama"], director="David Chase",
         decade="1990s", keywords=["family", "power", "tragedy", "moral-ambiguity", "slow-burn"],
         overview="A mob boss balances family life and organized crime while seeing a therapist.",
         user_rating=9, days_since_watched=180),
]

# Leave-k-out testi için "watched" listesinden ayrılan, ama gerçekte
# kullanıcının çok sevdiği başlıklar. Aday havuzuna (candidate pool)
# hiç puanı görünmeyen bir başlık gibi eklenecekler; iyi bir motor
# bunları yüksek sıraya koymalı.
HELD_OUT = [
    dict(id="h1", title="Enemy", media_type="movie",
         genres=["Mystery", "Drama"], director="Denis Villeneuve",
         decade="2010s", keywords=["identity", "atmospheric", "existential", "slow-burn"],
         overview="A man discovers his exact double and is pulled into a disorienting psychological spiral.",
         user_rating=None, days_since_watched=None),
    dict(id="h2", title="The Irishman", media_type="movie",
         genres=["Crime", "Drama"], director="Martin Scorsese",
         decade="2010s", keywords=["family", "power", "tragedy", "slow-burn", "moral-ambiguity"],
         overview="An aging hitman looks back on his decades of loyalty and violence inside organized crime.",
         user_rating=None, days_since_watched=None),
]

# Gerçek aday havuzu: motorun hiç bağlam olmadan sıralaması gereken,
# karışık kalitede yapımlar (bazıları zevkle örtüşüyor, bazıları negatif
# etiketlerle örtüşüyor, bazıları nötr).
CANDIDATES = [
    dict(id="c1", title="Dune", media_type="movie",
         genres=["Sci-fi", "Drama"], director="Denis Villeneuve",
         decade="2020s", keywords=["dystopia", "power", "atmospheric", "existential", "slow-burn"],
         overview="A young heir is thrust into a struggle for control of a desert planet's precious resource."),
    dict(id="c2", title="Severance", media_type="series",
         genres=["Sci-fi", "Mystery"], director="Ben Stiller",
         decade="2020s", keywords=["identity", "dystopia", "atmospheric", "existential", "slow-burn"],
         overview="Employees surgically split their memories between work and home, unraveling a deeper conspiracy."),
    dict(id="c3", title="Peaky Blinders", media_type="series",
         genres=["Crime", "Drama"], director="Otto Bathurst",
         decade="2010s", keywords=["family", "power", "tragedy", "moral-ambiguity"],
         overview="A post-war gang leader builds a criminal empire through cunning and ruthless ambition."),
    dict(id="c4", title="Zodiac", media_type="movie",
         genres=["Mystery", "Crime", "Drama"], director="David Fincher",
         decade="2000s", keywords=["investigation", "slow-burn", "atmospheric", "moral-ambiguity"],
         overview="A cartoonist becomes obsessed with identifying a serial killer terrorizing San Francisco."),
    dict(id="c5", title="The Grand Budapest Hotel", media_type="movie",
         genres=["Comedy", "Drama"], director="Wes Anderson",
         decade="2010s", keywords=["lighthearted", "whimsical", "fast-paced"],
         overview="A legendary concierge and his protege get entangled in a theft and murder farce at a famous hotel."),
    dict(id="c6", title="40-Year-Old Virgin", media_type="movie",
         genres=["Comedy", "Romance"], director="Judd Apatow",
         decade="2000s", keywords=["lighthearted", "feel-good", "fast-paced"],
         overview="A middle-aged electronics store employee navigates dating for the first time."),
    dict(id="c7", title="Chernobyl", media_type="series",
         genres=["Drama", "History"], director="Johan Renck",
         decade="2010s", keywords=["moral-ambiguity", "tension", "power", "investigation", "atmospheric"],
         overview="Soviet officials and scientists confront denial and cover-ups after a catastrophic nuclear disaster."),
    dict(id="c8", title="Ozark", media_type="series",
         genres=["Crime", "Drama"], director="Bill Dubuque",
         decade="2010s", keywords=["family", "power", "moral-ambiguity", "tension", "slow-burn"],
         overview="A financial advisor relocates his family to launder money for a drug cartel, spiraling into deeper crime."),
]
