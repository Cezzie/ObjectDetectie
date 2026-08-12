# Ideeën en strategieën — naast het statistische model

*Aanvullingen en alternatieven op wat er nu staat (YOLO-objectdetectie + de
statistische verschilscore uit [verschilscore-techniek.md](verschilscore-techniek.md)).
Per idee: wat het is, waarom het kansrijk is, en de inschatting van de moeite
(S = dagen, M = weken, L = maanden). Onderaan een prioriteitsadvies.*

---

## 1. Slimmere modellen

### 1.1 Embedding-verandering in plaats van pixelverschil (M) ⭐
Laat een voorgetraind beeldnetwerk van elke pand-uitsnede per jaargang een
*embedding* maken (een compacte getalsvector die "wat er te zien is" samenvat) en
meet de afstand tussen de vectoren van 2022 en 2025. Robuuster dan pixels: belichting,
JPEG-artefacten en kleine verschuivingen veranderen de embedding nauwelijks, een
nieuw dakvlak of PV-installatie wél. Geen labels nodig — dit is de logische
opvolger van de statistische verschilscore en een goede tussenstap naar 1.2.

### 1.2 Bi-temporeel verandermodel (L)
Het siamese netwerk dat beide foto's tegelijk ziet — uitgewerkt in
[mutatiedetectie.md](mutatiedetectie.md) (strategie B, met LEVIR-CD als
voortrainbasis). Pas starten als de taxateur-feedback uit de werkvoorraad genoeg
gelabelde paren heeft opgeleverd.

### 1.3 Segmentatie in plaats van boxen (M)
YOLO11-seg of SAM-gebaseerd: exacte contouren in plaats van rechthoeken. Voor de
WOZ interessanter dan het lijkt — "PV-oppervlak: 24 m²" of "aanbouw: 18 m²" is
direct bruikbaar in een taxatie, waar een box alleen "hier zit iets" zegt.

### 1.4 Open-vocabulary detectie als pre-annotator (S/M)
Modellen als Grounding DINO herkennen objecten op basis van een tekstprompt
("solar panel", "dormer") zonder eigen training. Te onnauwkeurig voor productie,
maar prima als éérste voortekenaar in Label Studio — sneller op gang dan wachten
op je eigen eerste model.

### 1.5 Actief leren (S) ⭐
Laat het model zelf aangeven wáár het onzeker is (confidence tussen 0,3 en 0,6)
en annoteer juist díe tegels. Haalt aantoonbaar meer modelverbetering per
geannoteerd uur dan willekeurige batches — een kleine aanpassing op stap 06
(sorteer de export op onzekerheid).

### 1.6 Meerjaars-consistentie / temporal voting (S)
Met vijf HR-jaargangen (2021–2025) hoeft een detectie of mutatie niet uit één
paar te komen: eis dat een object in ≥ 2 jaargangen gezien wordt, of dateer een
mutatie preciezer door de reeks af te lopen ("PV verscheen tussen 2023 en 2024").
Drukt valse detecties én geeft de taxateur een jaartal.

## 2. Andere databronnen

### 2.1 AHN-hoogteverschil (M) ⭐
Al gepland als strategie C: DSM-verschil tussen AHN-versies, gesneden met
BAG-contouren → kandidaten voor aanbouw, dakkapel, bijgebouw en sloop, ongevoelig
voor licht en seizoen. Het beste antwoord op de klassen waar beelddetectie zwak
in is.

### 2.2 CIR-infraroodluchtfoto (S)
PDOK levert dezelfde jaargangen ook in kleureninfrarood. Vegetatie licht daar
fel op; daken en PV niet — een goedkoop extra kanaal om "boom over dak" en
"mos/groen dak" uit de verschilscore te filteren, en een extra feature voor het
model (4-kanaals input).

### 2.3 Sentinel-2 als vroegsignalering (M)
Gratis satellietbeeld van 10 m resolutie, elke ~5 dagen. Te grof voor dakkapellen,
maar grote veranderingen (bouwrijp maken, nieuwbouwblok, sloop) zie je er
maandelijks in plaats van jaarlijks. Rol: continue trigger-laag die bepaalt wáár
de volgende HR-jaargang extra aandacht verdient.

### 2.4 Vergunningendata kruisen (M) ⭐
De omgekeerde controle van wat we nu doen. Kruis verleende bouwvergunningen met
de detecties: (a) vergunning verleend maar nooit iets zichtbaar gebouwd, en
(b) zichtbare bouw zónder vergunning — categorie b is voor toezicht/handhaving
en de WOZ het interessantst. Vereist toegang tot het gemeentelijke
vergunningenregister (BWB-intern te regelen).

### 2.5 BGT en 3DBAG (S/M)
De Basisregistratie Grootschalige Topografie kent erfverharding, water en
"overig bouwwerk" — kruising levert gratis context (zwembad vs vijver!). 3DBAG
geeft dakvorm per pand: een dakkapel-detectie op een plat dak is verdacht, op
een zadeldak plausibel.

### 2.6 Schuine beelden / streetview (L, commercieel)
Cyclomedia-beelden voor gevelelementen (erkers, kozijnen, zijaanzicht dakkapel).
Eerst intern checken of BWB al een afnamecontract heeft — veel
belastingsamenwerkingen wel. Dit is een eigen traject met eigen modellen.

## 3. Proces en organisatie

### 3.1 De taxateursbeoordeling als datamotor (S) ⭐
Elke bevestiging of afwijzing in de werkvoorraad is een gratis gelabeld
voorbeeld. Regel het vastleggen daarvan vanaf dag één (simpel: kolom
"oordeel" in de mutatielijst-export), en de trainingsdata voor 1.1/1.2 groeit
vanzelf met het gewone werk mee.

### 3.2 Prioriteren op waarde-impact (S)
Sorteer de werkvoorraad niet op verschilscore maar op *score × geschatte
WOZ-impact* (objectgrootte, wijk, objecttype). Dezelfde beoordelingscapaciteit
levert dan meer belastingopbrengst-correctie per uur.

### 3.3 Jaarlijkse kwaliteitsaudit (S)
Trek jaarlijks een aselecte steekproef panden en beoordeel die volledig
handmatig, los van het systeem. Dat geeft een onafhankelijke recall/precisie-meting
— precies wat het Algoritmeregister en de IAMA vragen, en de enige manier om
blinde vlekken (gemist én ongeregistreerd) te kwantificeren.

### 3.4 Koppeling met het taxatiesysteem (M)
De mutatielijst als GeoJSON/CSV met BAG-pand-id is er bijna al; de winst zit in
automatische aanlevering in het taxatiepakket (werkvoorraadmodule) zodat het
signaal in het bestaande werkproces valt in plaats van in een los notebook.

### 3.5 Samenwerken en niet dubbel bouwen (S om te starten)
CBS (DeepSolaris) is per mail benaderbaar; andere belastingsamenwerkingen
worstelen met hetzelfde vraagstuk — een gedeelde labelpool (iedereen annoteert
zijn eigen gebied, modellen worden samen getraind) vermenigvuldigt de
trainingsdata. En check de build-vs-buy-vraag (NEO, READAR) vóór fase 3.

## 4. Kleinere technische verbeteringen aan de bestaande pijplijn

| Idee | Moeite | Winst |
|---|---|---|
| Tegel-overlap 0,25 aanzetten (config) | S | panden op tegelranden vaker volledig in beeld |
| 5 cm-zones gebruiken waar beschikbaar | S | dakramen/schoorstenen beter zichtbaar |
| SAHI (sliced inference) bij voorspellen | S | kleine objecten op volledige-resolutie tegels |
| Confidence-kalibratie van het model | S | drempels krijgen een echte betekenis (0,8 ≈ 80% kans) |
| Hard negatives meetrainen (bevestigde valse detecties) | S | minder herhaalde fouten |
| RT-DETR naast YOLO11 benchmarken | M | mogelijk betere kleine-objectdetectie |

---

## Prioriteitsadvies

Eerst afmaken wat loopt: **annotatieronde 1 → getraind objectmodel → werkvoorraad
beoordelen** — alles hieronder wordt daar beter van.

Daarna, in volgorde van rendement per uur werk:

1. **3.1 Taxateursoordeel vastleggen** (S) — kost bijna niets, maakt al het latere mogelijk.
2. **1.5 Actief leren in stap 06** (S) — direct minder annotatiewerk per modelverbetering.
3. **1.6 Meerjaars-consistentie** (S) — minder ruis en een jaartal per mutatie, met data die er al is.
4. **2.1 AHN-hoogteverschil** (M) — vult de zwakste klassen (aanbouw, bijgebouw) met een onafhankelijk signaal.
5. **1.1 Embedding-verandering** (M) — de sprong voorbij pixelvergelijking, zonder labels te vereisen.

**2.4 (vergunningen kruisen)** verdient een apart gesprek binnen BWB: technisch
middelgroot, maar organisatorisch het meest waardevolle nieuwe signaal.

*Bevat gegevens van PDOK: Luchtfoto Beeldmateriaal Nederland (CC-BY 4.0), de BAG en het AHN.*
