# Ściągawka do nauki — etap 1 (prezentacja tematu)

Ten dokument tłumaczy **od zera** wszystko, co jest na slajdach i w protokole etapu 1. Czytaj po kolei —
każda część korzysta z poprzedniej. Wszystkie liczby pochodzą z naszego pilota (`results/pilot/`) albo
z publikacji Kohaviego (oznaczone [K]). Części dla etapów 2 i 3 dopiszemy później.

Na obronie prowadzący może poprosić o: wyjaśnienie wzoru i symboli, małe obliczenie, uzasadnienie
decyzji, wskazanie miejsca w kodzie, przewidzenie skutku zmiany parametru. Wszystko to jest niżej.

---

## 0. O co w ogóle chodzi (3 zdania)

Mamy mało danych (200 obiektów) i uczymy na nich klasyfikator. Chcemy wiedzieć, **jak często ten
klasyfikator będzie się mylił na nowych danych** — ale nowych danych nie mamy, więc musimy to
**oszacować** z tych samych 200 obiektów. Najpopularniejszy sposób to walidacja krzyżowa (CV) i
pytanie projektu brzmi: **o ile CV się myli (obciążenie) i jak bardzo jej wynik skacze (zmienność)**,
w zależności od liczby części $k$ — a dodatkowo, co daje stratyfikacja, gdy jedna klasa jest rzadka.

---

## 1. Odsetek pomyłek — nasza miara

Klasyfikator $C$ dostaje obiekt $x$ i mówi, do której klasy należy (0 albo 1). Sprawdzamy to na
obiektach, dla których znamy prawdziwą klasę $y$.

**Odsetek pomyłek** (błąd) = liczba pomyłek / liczba sprawdzonych obiektów.

Przykład: sprawdziliśmy 40 obiektów, klasyfikator pomylił się 7 razy → błąd $= 7/40 = 0{,}175 = 17{,}5\,\%$.
Trafność to $1 -$ błąd $= 82{,}5\,\%$. Kohavi podaje trafność, my błąd — to ta sama informacja.

### Błąd prawdziwy (slajd 4, pierwszy wzór)

$$e(C) = P\big(C(X) \neq Y\big)$$

- $C$ — nasz klasyfikator (już nauczony).
- $(X, Y)$ — **nowy, losowy** obiekt z tego samego źródła co dane treningowe; $X$ to cechy, $Y$ prawdziwa klasa.
- $C(X) \neq Y$ — zdarzenie „klasyfikator się pomylił”.
- $P(\dots)$ — prawdopodobieństwo tego zdarzenia.

Czyli: **jak często $C$ myli się na nowych danych**. Tej liczby nie da się policzyć dokładnie (nowych
danych jest nieskończenie wiele) — można ją tylko **oszacować**. Im więcej nowych obiektów sprawdzimy,
tym dokładniej. Dlatego w projekcie mamy duży zbiór testowy $T$: 10 000 obiektów → odsetek pomyłek na
$T$, oznaczany $e_{test}$, jest bardzo bliski $e(C)$ (odchyla się od niego o ok. 0,4 punktu
procentowego — p. §7).

**Dlaczego nie można zawsze tak robić?** Bo w prawdziwym życiu nie mamy 10 000 dodatkowych obiektów —
mamy tylko te 200. My je mamy, bo dane **generujemy sami**. To jest nasza „sztuczka”: dzięki
generatorowi znamy odpowiedź ($e_{test}$) i możemy sprawdzić, jak dobrze zgaduje ją CV.

---

## 2. Walidacja krzyżowa (CV) — co się dzieje krok po kroku

Mamy zbiór $D$: 200 obiektów. $k$-krotna CV dla $k = 5$:

1. Mieszamy obiekty losowo i dzielimy na $k = 5$ części (**foldów**) po $200/5 = 40$ obiektów:
   $D_1, D_2, D_3, D_4, D_5$.
2. Powtarzamy 5 razy (dla $j = 1, 2, 3, 4, 5$): **odkładamy** fold $D_j$, uczymy klasyfikator na pozostałych
   4 foldach ($4 \cdot 40 = 160$ obiektów), sprawdzamy go na odłożonym $D_j$ i zapisujemy błąd $e_j$.
3. Uśredniamy pięć błędów.

Każdy obiekt jest **dokładnie raz** w foldzie testowym i $k - 1$ razy w treningu. CV kosztuje $k$ uczeń
modelu.

### Wzór (slajd 5, protokół)

$$\hat e_{CV} = \frac{1}{k}\sum_{j=1}^{k} e_j, \qquad e_j = \frac{m_j}{|D_j|}$$

| Symbol | Co znaczy |
|---|---|
| $k$ | liczba foldów (u nas 2, 5 albo 10) |
| $j$ | numer foldu, od 1 do $k$ |
| $D_j$ | $j$-ty fold (zbiór 40 obiektów przy $k = 5$) |
| $\lvert D_j\rvert$ | liczba obiektów w foldzie $j$ (40) |
| $C_{-j}$ | klasyfikator nauczony **bez** foldu $j$ (na pozostałych 160 obiektach); minus = „bez” |
| $m_j$ | liczba pomyłek klasyfikatora $C_{-j}$ na foldzie $D_j$ |
| $e_j$ | odsetek pomyłek na foldzie $j$: $m_j / \lvert D_j\rvert$ |
| $\sum_{j=1}^{k} e_j$ | suma błędów wszystkich foldów: $e_1 + e_2 + \dots + e_k$ |
| $\frac{1}{k}\sum \dots$ | suma podzielona przez $k$, czyli **zwykła średnia** |
| $\hat e_{CV}$ | wynik CV; **daszek** oznacza „oszacowanie” (nie prawdziwa wartość, tylko jej przybliżenie), indeks CV mówi, skąd pochodzi |

Czyli: **$\hat e_{CV}$ to średnia z błędów na odłożonych foldach.**

### Przykład z pilota (slajd 6) — policz sam

Zbiór $D_1$, GaussianNB, $k = 5$, każdy fold ma 40 obiektów. Pomyłki na foldach: 7, 3, 7, 8, 4.

- $e_1 = 7/40 = 0{,}175$, $e_2 = 3/40 = 0{,}075$, $e_3 = 7/40 = 0{,}175$, $e_4 = 8/40 = 0{,}200$, $e_5 = 4/40 = 0{,}100$.
- $\hat e_{CV} = (0{,}175 + 0{,}075 + 0{,}175 + 0{,}200 + 0{,}100)/5 = 0{,}725/5 = \mathbf{0{,}145}$.
- Inaczej (wzór Kohaviego): wszystkie pomyłki / wszystkie obiekty $= 29/200 = 0{,}145$. **To samo**, bo foldy są
  równe. (Przy nierównych foldach wyniki by się minimalnie różniły — u nas 200 dzieli się przez 2, 5 i 10, więc nie.)
- Ten sam GaussianNB nauczony na **całym** $D_1$ (200 obiektów) i sprawdzony na $T$ (10 000 obiektów) ma
  $e_{test} = 0{,}1754$ (1754 pomyłki na 10 000).
- Różnica: $\hat e_{CV} - e_{test} = 0{,}145 - 0{,}1754 = -0{,}030$. W tym jednym zbiorze CV **zaniżyła** błąd o 3 p.p.

**Uwaga:** jedna różnica nic nie dowodzi — to przypadek. Dopiero wiele takich różnic (u nas 30) pokaże, czy CV
**średnio** zaniża, zawyża, czy trafia, i jak bardzo skacze. O tym §3.

---

## 3. Obciążenie i zmienność — dwa różne błędy estymatora

**Estymator** = przepis na oszacowanie jakiejś liczby z danych. Tu: $\hat e_{CV}$ szacuje prawdziwy błąd $e(C)$.
Każdy estymator może mylić się na dwa sposoby:

- **Obciążenie (bias)** — błąd **systematyczny**: estymator średnio (po wielu powtórzeniach) trafia obok prawdy.
  Jak celowniczy, który zawsze strzela trochę w lewo. Nie znika, choćbyśmy powtarzali w nieskończoność.
- **Zmienność (wariancja)** — **rozrzut**: wyniki kolejnych powtórzeń różnią się między sobą. Jak drżąca ręka —
  strzały rozsiane wokół środka.

Mogą występować w dowolnej kombinacji: celnie i stabilnie; celnie, ale rozrzut; obok, ale stabilnie; obok i rozrzut.
**Niska zmienność nie oznacza małego obciążenia** (celowniczy może strzelać bardzo powtarzalnie — ciągle w to samo złe
miejsce). To jedno z trzech pytań kontrolnych z karty tematu.

### Wzory (slajd 4, drugi rząd)

$$\text{bias} = \mathrm{E}[\hat e_{CV}] - e_{test}, \qquad \text{sd} = \sqrt{\mathrm{Var}[\hat e_{CV}]}$$

- $\mathrm{E}[\dots]$ — **wartość oczekiwana**: średnia, jaką dostalibyśmy, powtarzając eksperyment bardzo wiele razy.
  W praktyce zastępujemy ją zwykłą średnią z 30 powtórzeń.
- $\text{bias}$ — ile średnio $\hat e_{CV}$ różni się od prawdy. **Dodatnie = CV zawyża błąd = pesymizm**
  (Kohavi mówi „pesymizm”, bo u niego trafność jest zaniżona — to samo zjawisko).
- $\mathrm{Var}[\dots]$ — wariancja: średni kwadrat odchylenia od średniej; $\text{sd}$ (odchylenie standardowe) to
  jej pierwiastek, w tych samych jednostkach co błąd. Mówi, **o ile typowo** $\hat e_{CV}$ odbiega od swojej średniej.

### Jak to liczymy w projekcie (protokół, §2)

Powtarzamy całość dla $R = 30$ niezależnych zbiorów $D_1, \dots, D_{30}$. Dla każdego zbioru $r$ mamy jedną różnicę
$\Delta_r = \hat e_{CV,r} - e_{test,r}$. Wtedy:

$$\text{bias} \approx \frac{1}{R}\sum_{r=1}^{R}\big(\hat e_{CV,r} - e_{test,r}\big) = \text{średnia z } \Delta_r,
\qquad \text{zmienność} = \mathrm{sd}_r(\Delta_r) = \text{odchylenie standardowe } \Delta_r.$$

Indeks $r$ numeruje zbiory (powtórzenia), $\approx$ bo 30 powtórzeń to przybliżenie wartości oczekiwanej.

**Jak policzyć odchylenie standardowe ręcznie** (na 3 liczbach, żeby zrozumieć): $\Delta = 0{,}01;\ 0{,}03;\ 0{,}05$.
Średnia $= 0{,}03$. Odchylenia od średniej: $-0{,}02;\ 0;\ +0{,}02$. Kwadraty: $0{,}0004;\ 0;\ 0{,}0004$. Suma $0{,}0008$,
dzielimy przez $R - 1 = 2$ (tak liczy się sd z próby): $0{,}0004$. Pierwiastek: $\text{sd} = 0{,}02$.
Czyli: obciążenie $= +0{,}03$ (pesymizm 3 p.p.), zmienność $= 0{,}02$.

### Przykład „obciążenie vs zmienność” na liczbach

Prawdziwy błąd $0{,}17$. Estymator A w trzech powtórzeniach: $0{,}20;\ 0{,}22;\ 0{,}18$. Estymator B: $0{,}10;\ 0{,}24;\ 0{,}17$.
- A: średnia $0{,}20$ → obciążenie $+0{,}03$; rozrzut mały (sd $0{,}02$). **Obciążony, ale stabilny.**
- B: średnia $0{,}17$ → obciążenie $0$; rozrzut duży (sd $0{,}07$). **Nieobciążony, ale skacze.**

### Skąd pesymizm CV? (slajd 4, dół)

W CV model uczy się **nie na 200 obiektach, tylko na $200\cdot(k-1)/k$**: dla $k = 2$ na 100, $k = 5$ na 160,
$k = 10$ na 180. Model nauczony na mniejszej liczbie danych myli się częściej (to się nazywa **krzywa uczenia**:
błąd maleje, gdy danych przybywa). Więc CV mierzy błąd **gorszego modelu** niż ten, który finalnie nauczymy na całych
200 obiektach → zawyża błąd → pesymizm. Najgorzej dla $k = 2$ (traci połowę danych), prawie wcale dla $k = 10$ (traci 10 %).
**Stąd hipoteza H1:** obciążenie największe dla $k = 2$, bliskie zera dla $k = 10$.

### Skąd zmienność CV?

Dwa źródła: (1) jakie 200 obiektów wylosowaliśmy do $D_r$; (2) jak losowo podzieliliśmy je na foldy. Przy $k = 2$
model uczy się na 100 obiektach — jest „chwiejny”, małe zmiany danych dają inny model → **większy rozrzut**.
Dla modelu bardzo stabilnego (takiego, który po usunięciu foldu daje praktycznie te same odpowiedzi) Kohavi pokazuje,
że zmienność **nie zależy od $k$** [K, Propozycja 1]. **Stąd hipoteza H1′/H1″:** zmienność największa dla $k = 2$,
a efekty silniejsze dla niestabilnego drzewa CART niż dla stabilnego GaussianNB.

---

## 4. Dlaczego foldy nie są „niezależnymi pomiarami” (pytanie kontrolne 1)

Kusi, żeby policzyć rozrzut pięciu $e_j$ i uznać go za niepewność $\hat e_{CV}$. To błąd. Przy $k = 5$ model $C_{-1}$
uczy się na foldach 2–5, a $C_{-2}$ na foldach 1, 3, 4, 5 — mają **3 z 4 foldów wspólne (75 %)**; przy $k = 10$ —
8 z 9 (89 %). To prawie te same modele, więc ich błędy są ze sobą powiązane (skorelowane), a nie niezależne.
Rozrzut $e_j$ jest przez to mylący — Kohavi pokazuje skrajny przypadek [K, Przykład 1]: iris + klasyfikator „zawsze
klasa większościowa” + leave-one-out → **wszystkie** foldy dają 0 % trafności, rozrzut między foldami 0, a estymata jest
kompletnie błędna (prawda: 33 %).

Niezależne są dopiero **osobne zbiory danych**. Dlatego w naszym protokole **jednostką powtórzenia jest zbiór $D_r$**,
a obciążenie i zmienność liczymy po $r = 1..30$, nie po foldach.

---

## 5. Generator danych (slajd 7) — skąd biorą się nasze dane

Każdy obiekt ma 10 cech (liczb) i klasę $y \in \{0, 1\}$. Generujemy go tak:

$$X \mid y \sim \mathcal N(\mu_y, I_{10}),\qquad \mu_1 = -\mu_0 = \tfrac{\delta}{2}\,u,\qquad
u = \tfrac{1}{\sqrt5}(1,1,1,1,1,0,0,0,0,0),\qquad \delta = 2,\qquad y \sim \text{Bernoulli}(\pi_1)$$

| Symbol | Co znaczy, po ludzku |
|---|---|
| $y \sim \text{Bernoulli}(\pi_1)$ | najpierw losujemy klasę: 1 z prawdopodobieństwem $\pi_1$, inaczej 0. $\pi_1 = 0{,}5$ (klasy po równo) w odtworzeniu, $\pi_1 = 0{,}1$ (klasa 1 rzadka) w eksperymencie własnym |
| $X \mid y \sim \mathcal N(\mu_y, I_{10})$ | potem losujemy 10 cech z rozkładu normalnego („dzwon”) o środku $\mu_y$ zależnym od klasy; $I_{10}$ = każda cecha ma wariancję 1 i cechy są od siebie niezależne |
| $\mu_0, \mu_1$ | środki dzwonów klasy 0 i 1; leżą symetrycznie: $\mu_1 = -\mu_0$ |
| $u$ | kierunek, w którym klasy się różnią: pierwsze 5 cech ma niezerowe wartości (**cechy informacyjne**), ostatnie 5 to zera (**cechy szumowe** — wyglądają tak samo w obu klasach). $1/\sqrt5$ sprawia, że $u$ ma długość 1 |
| $\delta = 2$ | odległość między środkami dzwonów (odległość Mahalanobisa; przy wariancji 1 = zwykła odległość). Większe $\delta$ = klasy łatwiej rozdzielić |

Obrazowo: dwa dzwony w przestrzeni 10-wymiarowej, odsunięte od siebie o 2 wzdłuż kierunku $u$. Na slajdzie 7 lewy
rysunek pokazuje 200 wylosowanych punktów na dwóch cechach (klasy się mieszają), prawy — oba dzwony po rzucie na
kierunek $u$ (jedna oś).

### Błąd Bayesa — ile myli się najlepszy możliwy klasyfikator

Dzwony na siebie nachodzą, więc **żaden** klasyfikator nie będzie bezbłędny. Najlepszy możliwy (reguła Bayesa) stawia
granicę w połowie między środkami (dla klas po równo) i myli się na obiektach, które „wpadły” po drugiej stronie —
to zacieniowane pola na prawym rysunku. Ich wielkość to:

$$e^* = \Phi(-\delta/2) = \Phi(-1) = 0{,}1587 \approx 15{,}9\,\%,$$

gdzie $\Phi$ to dystrybuanta rozkładu normalnego (tablice: $\Phi(-1) = 0{,}1587$ — „prawdopodobieństwo, że zmienna
normalna jest mniejsza niż −1 odchylenie”). Odległość od środka dzwonu do granicy to $\delta/2 = 1$, stąd $\Phi(-1)$.

Dla klasy rzadkiej ($\pi_1 = 0{,}1$) opłaca się przesunąć granicę w stronę rzadkiej klasy (bo klasa 0 jest 9× częstsza):
próg $t = \ln(9)/\delta = 1{,}10$, błąd Bayesa **7,0 %**. Ale uwaga: klasyfikator „zawsze mów 0” ma błąd 10 % — niewiele
gorzej! Dlatego w eksperymencie własnym sam odsetek pomyłek mało mówi i mierzymy też **czułość** klasy rzadkiej
(ile obiektów klasy 1 model wykrył); Bayes wykrywa 46 % z nich.

**Po co nam znany błąd Bayesa?** Wiemy, jak daleko od ideału są nasze modele. W pilocie GaussianNB na 200 obiektach ma
$e_{test} \approx 17{,}5\,\%$ — blisko 15,9 %; CART 24–34 % — daleko.

### Dlaczego taki generator pasuje do GaussianNB i CART

- **GaussianNB** zakłada dokładnie to, co generujemy: cechy niezależne, każda z rozkładu normalnego w klasie. Uczy się
  tylko średniej i wariancji każdej cechy w każdej klasie — te liczby prawie się nie zmieniają, gdy odłożymy 40 obiektów.
  → model **stabilny**, krzywa uczenia szybko się płaszczy → spodziewamy się małego obciążenia CV.
- **CART** (drzewo decyzyjne) zadaje pytania o jedną cechę naraz („czy $x_3 > 0{,}2$?”), a granica między klasami
  jest **ukośna** (zależy od 5 cech jednocześnie). Drzewo musi ją „schodkować” wieloma pytaniami, na 200 obiektach
  dopasowuje się do szumu (bez przycinania liście mają po 1 obiekcie), małe zmiany danych dają inne drzewo
  → model **niestabilny** → spodziewamy się dużego obciążenia i zmienności CV. To nasz odpowiednik pary C4.5 / Naive-Bayes u Kohaviego.

---

## 6. Protokół — każdy parametr w jednym zdaniu (slajdy 7–8, protokół §3–4)

| Parametr | Wartość | Dlaczego |
|---|---|---|
| $n$ — rozmiar zbioru treningowego | 200 | z karty tematu; dzieli się przez 2, 5 i 10 → równe foldy (100 / 40 / 20) |
| $R$ — liczba zbiorów (powtórzeń) | 30 | z karty; każda różnica $\Delta_r$ to jedno niezależne „pomiary”; średnia z 30 jest 5,5× dokładniejsza niż jedna |
| $N$ — rozmiar testu $T$ | 10 000 | z karty; $e_{test}$ jest wtedy dokładny do ok. 0,4 p.p. (§7) — praktycznie „prawda” |
| $k$ | 2, 5, 10 | z karty; porównujemy mało / średnio / dużo foldów |
| modele | GaussianNB, CART (DecisionTreeClassifier, domyślne ustawienia sklearn) | z karty; stabilny vs niestabilny |
| podział na foldy | `KFold(shuffle=True, random_state=2000 + r)` | losowy, **ten sam dla obu modeli** (jak u Kohaviego) — porównanie modeli jest uczciwe |
| ziarna losowe | $D_r$: $1000 + r$; podziały: $2000 + r$; $T$: 90001 | ustalone **przed** badaniem, zapisane w `cvbias/protocol.py`; nikt nie może zarzucić, że dobraliśmy losowania pod wynik; każde uruchomienie daje te same liczby |
| metryka | odsetek pomyłek | z karty |
| co porównujemy | $\Delta_{r} = \hat e_{CV,r} - e_{test,r}$ dla każdego $k$ i modelu | średnia po $r$ = obciążenie, sd po $r$ = zmienność |

**Ziarno** (seed) to liczba startowa generatora liczb losowych: to samo ziarno = ta sama „losowa” sekwencja. Dzięki temu
zbiór $D_7$ jest zawsze tym samym zbiorem, a ktoś inny może odtworzyć nasze wyniki co do cyfry.

**Czego nie wolno robić z testem $T$** (pytanie kontrolne 3): wybierać według niego parametrów modeli, parametrów
generatora ani wariantu CV. $T$ służy **tylko do oceny**. Gdybyśmy np. zmieniali $\delta$, aż wyniki „ładnie wyjdą”, to
$T$ przestałby być niezależnym sędzią, a stałby się częścią dopasowywania — i mierzony błąd byłby zaniżony.
Nasze $\delta = 2$ wynika z teorii (błąd Bayesa 15,9 % — ani trywialnie, ani beznadziejnie), ustalone zanim cokolwiek policzyliśmy.

### Schemat (slajd 8) słowami

Generator → 30 zbiorów $D_r$ po 200 obiektów. Dla każdego $D_r$ i każdego modelu:
(a) CV dla $k = 2, 5, 10$ → trzy wartości $\hat e_{CV}$;
(b) model na całym $D_r$ → sprawdzony na $T$ → $e_{test}$.
Różnice (a) − (b) → dla każdego $k$ 30 liczb → średnia (obciążenie) i sd (zmienność). Modele: $2 + 5 + 10 = 17$ uczeń
w CV + 1 na całości = 18 na zbiór i model → $30 \cdot 2 \cdot 18 = 1080$ uczeń.

---

## 7. Dwie liczby o dokładności (żeby umieć uzasadnić $N$ i $R$)

Odsetek pomyłek z $N$ obiektów ma rozrzut (odchylenie standardowe) $\sqrt{e(1-e)/N}$ — bo każdy obiekt to „rzut monetą”
pomyłka/nie-pomyłka (rozkład dwumianowy).

- $e_{test}$ przy $N = 10\,000$, $e = 0{,}17$: $\sqrt{0{,}17\cdot0{,}83/10\,000} = 0{,}0038$ → **0,4 p.p.** Czyli $e_{test}$ to praktycznie prawda.
- Błąd jednego foldu po 40 obiektów: $\sqrt{0{,}17\cdot0{,}83/40} = 0{,}059$ → **5,9 p.p.** Dlatego pojedyncze $e_j$ tak skaczą
  (w pilocie od 0,075 do 0,200) i dlatego je uśredniamy.
- Dokładność obciążenia z $R = 30$ zbiorów: $\text{se} = \text{sd}/\sqrt{30}$. Jeśli sd różnic $= 0{,}03$, to
  se $= 0{,}03/5{,}48 = 0{,}0055$ → **0,55 p.p.** Obciążenie mniejsze niż ok. 1 p.p. (prawdopodobne dla GaussianNB) może być
  nie do odróżnienia od zera — i to **też jest wynik** („dla stabilnego modelu CV jest praktycznie nieobciążona”).

---

## 8. Eksperyment własny — stratyfikacja (slajd 9)

**Stratyfikacja** = dzielimy na foldy tak, żeby **w każdym foldzie proporcja klas była taka jak w całym zbiorze**.
Zwykły `KFold` losuje obiekty do foldów nie patrząc na klasę; `StratifiedKFold` losuje osobno w każdej klasie.

Przy $\pi_1 = 0{,}1$ w 200 obiektach jest średnio 20 obiektów klasy rzadkiej (w pilocie: 24, 25, 14). Zwykły podział na
5 foldów po 40 rozrzuca je nierówno — w pilocie ($D_1$, 24 rzadkie): **2, 5, 9, 6, 2**; stratyfikowany: **4, 5, 5, 5, 5**.
Gdy rzadkich jest 14 (zbiór $D_3$), zwykły podział ma ok. 4 % szans na fold **bez żadnego** obiektu klasy rzadkiej —
i tak się stało w pilocie. W takim foldzie nie da się policzyć czułości (0 wykrytych z 0 obecnych) → zapisujemy
„brak wyniku, powód: brak klasy w foldzie”, nie wstawiamy zera i nie pomijamy po cichu.

Co porównujemy **na tych samych zbiorach $D_r$** (ten sam zbiór, dwa sposoby podziału): obciążenie, zmienność, czułość klasy
rzadkiej, liczbę foldów bez klasy rzadkiej.

**Hipoteza H2:** stratyfikacja **nie zmienia obciążenia** (model w foldzie dalej uczy się na 160 obiektach — ta sama krzywa
uczenia), ale **zmniejsza zmienność** (znika losowość „ile rzadkich trafiło do tego foldu”) i eliminuje puste foldy.
Kohavi [K] widział to samo: stratyfikacja „uniformly better” — trochę mniejsze obciążenie i trochę mniejsza wariancja.

---

## 9. Publikacja Kohaviego — co trzeba o niej wiedzieć (slajd 2)

- **Pytanie:** jak dobrze różne metody (holdout, CV z różnym $k$, bootstrap) szacują trafność klasyfikatora i którą wybrać
  do porównywania modeli.
- **Jak:** C4.5 (drzewo) i Naive-Bayes na 7 zbiorach z UCI (+ zbiór z losowymi etykietami), 50 powtórzeń; „prawdziwą”
  trafność liczył holdoutem na reszcie zbioru; te same foldy dla obu algorytmów; ponad pół miliona uruchomień.
- **Wyniki:** CV pesymistyczna, najbardziej dla $k = 2$ i $5$; przy $k = 10$–$20$ prawie bez obciążenia. Wariancja największa
  dla $k = 2$ (i dla leave-one-out przy C4.5). Stratyfikacja: mniejsze obciążenie i wariancja. Bootstrap .632: mała wariancja,
  ale na niektórych zbiorach ogromne obciążenie (do 9,8 p.p.) — przykład na „niska wariancja ≠ małe obciążenie”.
- **Zalecenie:** 10-krotna stratyfikowana CV.
- **Co bierzemy, co zmieniamy:** bierzemy pytanie i schemat (wiele powtórzeń, te same foldy dla obu modeli, niezależny punkt
  odniesienia). Zmieniamy: dane UCI → nasz generator (znany błąd Bayesa, prawdziwie niezależne zbiory), C4.5/NB → CART/GaussianNB
  ze scikit-learn, 50 → 30 powtórzeń, holdout → test 10 000, bez bootstrapu i leave-one-out (karta ich nie wymaga; LOO to 200
  uczeń na zbiór — poza budżetem 2500). To **adaptacja** — mówimy o tym wprost.
- **Słaby punkt publikacji** (jedno zdanie na obronę): jego „prawdziwa” trafność to też tylko oszacowanie z reszty zbioru,
  a 50 próbek losowanych z tego samego zbioru nie jest w pełni niezależnych — nasz generator tego problemu nie ma.

---

## 10. Pilot — co pokazują liczby na slajdzie 10

- **174 dopasowania, 0,16 s** — 3 zbiory × 2 modele × (2 + 5 + 10 + 1 uczeń) = 108 w odtworzeniu, plus 3 × 2 × (5 + 5 + 1) = 66
  w eksperymencie własnym. Pełna seria: 1080 + 660 = 1740, plus 180 na etap 3 = **1920 ≤ 2500** (budżet z karty).
- Pilot służy **tylko** do sprawdzenia, że kod działa i że wyniki mają sensowne wartości (NB ok. 17,5 %, blisko błędu Bayesa;
  CART 24–34 %). Z 3 zbiorów **nie wyciągamy wniosków** — rozrzut jest za duży (§7).
- Każde uruchomienie zapisuje: błąd i skład klas każdego foldu (`*_folds.csv`), podsumowanie na zbiór × model × $k$
  (`*_summary.csv`: `e_cv`, `e_test`, `diff`), `meta.json` (wersje bibliotek, ziarna, liczba uczeń, czas). To są „surowe
  wyniki”, których wymaga karta.

### Gdzie to jest w kodzie (gdyby prowadzący poprosił o pokazanie)

| Co | Gdzie |
|---|---|
| generator | `cvbias/generator.py`, funkcja `generate(cfg, n, seed)`; błąd Bayesa: `GeneratorConfig.bayes_error()` |
| wszystkie parametry i ziarna | `cvbias/protocol.py` |
| test $T$ losowany raz, przed pętlą po zbiorach | `cvbias/experiment.py`, `run_series`: linia `X_test, y_test = generate(...)` |
| pętla po zbiorach $D_r$ | `for r in range(1, n_reps + 1): X, y = generate(cfg, P.N_TRAIN, seeds["train"] + r)` |
| $e_{test}$ (model na całym $D_r$) | `fit_and_predict(model_name, X, y, X_test)` → `error_rate` |
| ten sam podział dla obu modeli | `make_splitter(cv_type, k, seeds["split"] + r)` — ziarno zależy tylko od $r$ |
| CV i błędy foldów | `cross_validate` — model uczy się na `X[train_idx]`, sprawdzany na `X[test_idx]` |
| średnia foldów i wzór Kohaviego | `e_cv = errors.mean()`, `e_cv_pooled = sum(n_errors) / len(y)` |
| flaga „fold bez klasy” | `missing_class_test`; czułość `recall_class1` zwraca NaN, gdy brak klasy 1 |
| liczenie uczeń (budżet) | `FIT_COUNTER` |
| obciążenie i zmienność | `cvbias/analysis.py`, `bias_variance_table`: `mean(diff)`, `std(diff)` |

---

## 11. Co powiedzieć przy każdym slajdzie (ok. 10 minut)

1. **Tytuł** — temat, publikacja, my.
2. **Publikacja i problem** — „Kohavi sprawdzał, jak dobrze CV i bootstrap szacują trafność; znalazł pesymizm CV przy małym $k$,
   dużą wariancję przy $k = 2$ i korzyść ze stratyfikacji. My odtwarzamy to pytanie na własnych danych i modelach
   (tabela: co takie samo, co zmienione).”
3. **Pytanie i hipotezy** — przeczytać pytanie; H1: pesymizm największy dla $k = 2$, bo trening na połowie danych;
   H1′: tam też największa zmienność; H1″: silniej dla CART; H2: stratyfikacja zmniejsza zmienność, nie zmienia obciążenia.
4. **Obciążenie i zmienność** — błąd prawdziwy = jak często model myli się na nowych danych; nie znamy go, mamy $e_{test}$
   z 10 000 obiektów; obciążenie = średnia różnica CV − prawda (dodatnie = pesymizm); zmienność = rozrzut; skąd pesymizm
   (trening na 100/160/180 zamiast 200); jak liczymy (30 zbiorów → 30 różnic).
5. **Wzór CV** — przeczytać wzór symbol po symbolu (tabela z §2); „foldy nie są niezależne, bo ich zbiory uczące się
   pokrywają — dlatego powtórzeniem jest cały zbiór”.
6. **Przykład ręczny** — policzyć na głos: 7/40 … średnia 0,145 = 29/200; $e_{test}$ 0,1754; różnica −0,030; „jedna różnica
   to przypadek, liczy się 30”.
7. **Generator** — dwa dzwony odsunięte o $\delta = 2$, 5 cech informacyjnych + 5 szumu; błąd Bayesa 15,9 % (zacieniowane pola),
   7,0 % przy klasie rzadkiej; 30 zbiorów po 200; test 10 000 tylko do oceny.
8. **Plan odtworzenia** — przejść strzałki schematu; „te same podziały dla obu modeli; ziarna utrwalone w protocol.py”.
9. **Eksperyment własny** — co to stratyfikacja; tabela 2/5/9/6/2 vs 4/5/5/5/5; pusty fold w $D_3$; co mierzymy.
10. **Wykonalność** — 174 uczenia w 0,16 s; 1920 ≤ 2500; co zapisujemy; cztery zasady kontroli poprawności.
11. **Ograniczenia, źródła, 2A** — dane „idealne” dla NB; jeden wspólny test; 30 powtórzeń = efekty < 1 p.p. niewidoczne; AI:
    poziom 2, wsparcie.
12. *(zapas)* trzy pytania kontrolne.

---

## 12. Pytania, które mogą paść na etapie 1 — krótkie odpowiedzi

**Co oznacza daszek nad $e$?** Że to oszacowanie (estymata), a nie prawdziwa wartość.

**Co to jest $e_j$ i jak powstaje?** Odsetek pomyłek modelu nauczonego bez foldu $j$, policzony na foldzie $j$: pomyłki / 40.

**Dlaczego średnia błędów foldów równa się „wszystkie pomyłki / 200”?** Bo każdy fold ma tyle samo obiektów (40):
$\frac{1}{5}\sum \frac{m_j}{40} = \frac{\sum m_j}{200}$.

**Dlaczego CV jest pesymistyczna?** Model w foldzie uczy się na mniejszej liczbie danych (100/160/180) niż model końcowy (200),
więc myli się częściej.

**Co to obciążenie, a co zmienność?** Obciążenie — o ile średnio estymata chybia prawdy (błąd systematyczny). Zmienność — jak
bardzo estymata skacze między powtórzeniami. Niezależne od siebie.

**Czy niższa wariancja oznacza mniejsze obciążenie?** Nie — przykład A/B z §3 i bootstrap .632 u Kohaviego (mała wariancja,
obciążenie do 9,8 p.p.).

**Dlaczego 10 foldów to nie 10 niezależnych pomiarów?** Zbiory uczące sąsiednich foldów pokrywają się w 8/9; to prawie te same
modele; niezależne są dopiero osobne zbiory danych (nasze 30).

**Czego nie wolno dobierać według dużego testu?** Niczego: ani parametrów modeli, ani generatora, ani wariantu CV. Test tylko ocenia.

**Dlaczego 30 zbiorów, a nie więcej?** Karta tematu i budżet; se $=$ sd/√30 — wystarcza dla efektów rzędu 2–3 p.p. (CART), za mało
dla < 1 p.p. (NB) i mówimy o tym wprost.

**Dlaczego jeden test, a nie 30?** Karta mówi o jednym dużym teście; jego szum to 0,4 p.p. — pomijalny; ograniczenie odnotowane.

**Co to znaczy, że model jest stabilny?** Po usunięciu części danych daje prawie te same odpowiedzi. GaussianNB — tak (uczy się
średnich i wariancji), CART — nie (zmienia się kształt drzewa).

**Dlaczego CART bez przycinania?** Ustawienia domyślne scikit-learn; chcemy mieć model niestabilny jako kontrast dla stabilnego NB.
Przycinanie można dodać jako analizę dodatkową, ale to zmiana protokołu do uzgodnienia.

**Co się stanie, gdy zwiększycie $\delta$ do 3?** Klasy dalej od siebie → błąd Bayesa $\Phi(-1{,}5) = 6{,}7\,\%$ → modele uczą się
szybciej (płaska krzywa uczenia) → mniejsze obciążenie i mniejsza zmienność CV.

**A gdy dodacie więcej cech szumowych?** Modele mają więcej do nauczenia z tych samych 200 obiektów → większy błąd, stromsza krzywa
uczenia → większe obciążenie CV; CART cierpi bardziej (fałszywe podziały na szumie).

**A gdy zmienicie ziarno?** Inne konkretne zbiory i podziały → inne pojedyncze liczby, ale w granicach zmienności; wnioski z 30
zbiorów bez zmian. Ziarna są ustalone z góry właśnie po to, by nikt nie podejrzewał dobierania.

**Dlaczego mierzycie czułość klasy rzadkiej?** Przy 10 % klasy rzadkiej model „zawsze 0” ma tylko 10 % błędu — odsetek pomyłek nie
pokazuje, czy klasa rzadka jest w ogóle wykrywana.

**Co robicie z foldem bez klasy rzadkiej?** Odsetek pomyłek liczymy normalnie; czułość = brak wyniku z zapisanym powodem; liczba takich
foldów jest jedną z miar eksperymentu.

**Czy to jeszcze odtworzenie, skoro zmieniliście dane i modele?** Odtwarzamy pytanie i schemat badania; dane i modele to zadeklarowana
adaptacja — karta tematu tak każe.

**Co, jeśli hipotezy się nie potwierdzą?** Raportujemy wynik taki, jaki jest, i tłumaczymy (np. NB stabilny → brak obciążenia zgodny
z Propozycją 1 Kohaviego). Kontrakt: wynik negatywny nie obniża oceny.

---

## 13. Sprawdź się (odpowiedzi w rozwijanych blokach)

**A.** Foldy po 40, pomyłki 5, 9, 6, 7, 8. Policz $\hat e_{CV}$ dwiema metodami.
<details><summary>Odpowiedź</summary>
$e_j$: 0,125; 0,225; 0,150; 0,175; 0,200 → średnia $0{,}875/5 = 0{,}175$. Łącznie $35/200 = 0{,}175$.
</details>

**B.** $k = 10$, $n = 200$: ile obiektów w foldzie, ile w treningu, jaki ułamek zbiorów uczących dwóch foldów jest wspólny?
<details><summary>Odpowiedź</summary>
Fold 20, trening 180, wspólne 8 z 9 = 89 %.
</details>

**C.** Trzy różnice $\Delta$: $0{,}02;\ 0{,}05;\ 0{,}08$. Obciążenie i zmienność?
<details><summary>Odpowiedź</summary>
Średnia $0{,}05$ (pesymizm 5 p.p.). Odchylenia $-0{,}03; 0; 0{,}03$ → kwadraty $0{,}0009; 0; 0{,}0009$ → suma $0{,}0018$ / 2 $= 0{,}0009$
→ sd $= 0{,}03$.
</details>

**D.** Dlaczego błąd Bayesa dla $\delta = 2$ to $\Phi(-1)$, a nie $\Phi(-2)$?
<details><summary>Odpowiedź</summary>
Granica leży w połowie między środkami dzwonów, czyli w odległości $\delta/2 = 1$ od każdego środka. Obiekt klasy 0 jest błędnie
sklasyfikowany, gdy wyląduje dalej niż 1 odchylenie od swojego środka w stronę klasy 1: $P = \Phi(-1) = 15{,}9\,\%$.
</details>

**E.** Model na 200 obiektach ma $e_{test} = 0{,}29$. CV z $k = 2$ dała $0{,}33$, z $k = 10$ — $0{,}30$. Który wynik jest bardziej
pesymistyczny i dlaczego tak się spodziewamy?
<details><summary>Odpowiedź</summary>
$k = 2$ (różnica +0,04 vs +0,01): model w foldzie uczył się tylko na 100 obiektach zamiast 180, więc mylił się częściej.
</details>

---

## Słowniczek

walidacja krzyżowa (cross-validation, CV) · fold (część zbioru) · estymata/estymator (oszacowanie / przepis na nie) ·
obciążenie (bias) · zmienność / wariancja / odchylenie standardowe (sd) · pesymistyczny (zawyża błąd) · krzywa uczenia
(błąd vs liczba danych) · stabilność modelu · stratyfikacja (foldy z proporcjami klas jak całość) · błąd Bayesa (najmniejszy
możliwy błąd) · rozkład normalny („dzwon”) · $\Phi$ (dystrybuanta rozkładu normalnego) · ziarno (seed) · przeciek danych ·
czułość (odsetek wykrytych obiektów danej klasy) · i.i.d. (obiekty niezależne, z tego samego rozkładu).
