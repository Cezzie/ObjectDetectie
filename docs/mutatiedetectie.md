# Mutatiedetectie: veranderingen tussen luchtfoto-jaargangen

*Doel: automatisch signaleren dat er iets veranderd is aan of rond een pand — zonnepanelen
geplaatst, dakkapel gebouwd, aanbouw verschenen, zwembad aangelegd — als werklijst voor
een taxateur. In de sector heet dit "mutatiesignalering".*

## TL;DR

1. **We hebben uitstekende data**: PDOK levert per jaargang dezelfde luchtfoto's
   (2016–nu), ons tegelgrid ligt vast in RD-coördinaten, dus voor/na-paren zijn
   pixel-uitgelijnd en gratis. BAG-mutaties en AHN-hoogteverschillen leveren gratis
   veranderlabels.
2. **Begin zónder verandermodel**: draai de objectdetector (die we nu bouwen) op twee
   jaargangen en vergelijk de uitkomsten per BAG-pand. Dat heet post-classification
   comparison en vergt nul extra training.
3. **Een echt bi-temporeel verandermodel** (twee foto's tegelijk als input) is de
   vervolgstap; daarvoor bestaan voorgetrainde modellen (LEVIR-CD e.d.) om op voort
   te bouwen. Pas doen als aanpak 2 zijn plafond bereikt.
4. **Check eerst build-vs-buy**: meerdere Nederlandse partijen verkopen precies dit
   aan gemeenten en belastingsamenwerkingen — mogelijk neemt BWB al zoiets af.

---

## 1. Welke data hebben we?

### Luchtfoto-jaargangen (PDOK, open data, CC-BY)

Dezelfde WMS die onze pipeline al gebruikt (`service.pdok.nl/hwh/luchtfotorgb/wms/v1_0`)
bevat per-jaargang-lagen — gecontroleerd via GetCapabilities:

| Jaargang | Laag | Resolutie / seizoen |
|---|---|---|
| 2016–2020 | `2016_ortho25` … `2020_ortho25` | 25 cm, zomer |
| 2021–nu | `2021_orthoHR` … `2026_orthoHR` | 8 cm (deels 5 cm), winter |
| 2022–nu | ook `*_ortho25` | 25 cm, zomer |
| actueel | `Actueel_orthoHR` / `Actueel_ortho25` | nieuwste opname |

**Waarom dit goud is:** ons tegelgrid staat vast in RD-coördinaten (config + `tiles.json`).
Dezelfde tegel opvragen bij `2022_orthoHR` en `2025_orthoHR` geeft twee beelden van exact
hetzelfde stuk grond, al uitgelijnd. Vijf HR-jaargangen (2021–2025) = vier jaarparen,
landsdekkend.

**Kanttekeningen:**
- **Seizoen/licht**: vergelijk altijd HR-met-HR (winter) of 25-met-25 (zomer), nooit kruislings.
- **Omvalling (relief displacement)**: daken "leunen" per jaargang een andere kant op
  omdat het vliegtuig ergens anders vloog. Verwacht schijnverschuivingen van enkele
  pixels op dakhoogte — een verandermodel moet daar tegen kunnen, en drempels op
  boxoverlap (i.p.v. pixelverschil) vangen dit grotendeels af.
- **Tijdelijke objecten** (steigers, bouwketen): een jaarcadans mist alles wat korter
  staat dan ± een jaar. Zie §5.

### BAG-mutaties (gratis structurele veranderlabels)

De BAG registreert bouwjaar, status ("Bouw gestart", "Pand in gebruik", "Pand gesloopt")
en mutatiedatums. Vergelijk twee BAG-momentopnamen en je weet wáár nieuwbouw, sloop of
splitsing plaatsvond — dat zijn gratis, betrouwbare labels om een verandermodel mee te
trainen of te valideren, in dezelfde geest als onze zwakke pand-labels.

### AHN-hoogteverschillen

AHN3 (±2014–2019), AHN4 (2020–2022) en AHN5 (2023–nu) zijn als 0,5 m hoogterasters
(DSM/DTM) beschikbaar. DSM(t2) − DSM(t1) is fotometrie-ongevoelig: geen last van licht,
seizoen of schaduw. Alles wat >1,5 m hoogteverschil toont bij een pand is een sterke
kandidaat voor aanbouw, dakkapel, bijgebouw of sloop. Nadeel: de jaargangen liggen
verder uit elkaar dan de luchtfoto's.

---

## 2. Drie strategieën, in volgorde van aanbevolen uitvoering

### A. Verschil-van-detecties (start hier — geen nieuw model nodig)

Draai de objectdetector die we nu bouwen op tegels van jaargang t1 én t2, en vergelijk
per BAG-pand de uitkomsten:

```
detecties 2023 per pand   detecties 2025 per pand   signaal
geen zonnepanelen     →   zonnepanelen (conf 0.8)   "PV geplaatst"
geen dakkapel         →   dakkapel (conf 0.7)       "dakkapel gebouwd"
zwembad               →   geen zwembad              "zwembad verwijderd?"
```

- **Voordeel**: nul extra trainingswerk; elk beter detectormodel maakt automatisch ook
  de mutatiesignalering beter; uitlegbaar richting taxateur en Algoritmeregister.
- **Nadeel**: fouten stapelen (een misser in jaar t1 lijkt een verandering). Mitigatie:
  alleen signaleren bij ruime confidence-marge (bijv. t2 ≥ 0.6 én t1 ≤ 0.2), per pand
  aggregeren i.p.v. per box, en de top-N door een taxateur laten bevestigen.
- De bevestigde/afgewezen signalen zijn meteen trainingsdata voor strategie B.

### B. Bi-temporeel verandermodel (de verdieping)

Een model dat béide beelden tegelijk ziet en het verschil leert — robuuster tegen
licht- en seizoensverschil dan A, en vangt ook veranderingen buiten de klassenlijst.

- **Architecturen om op voort te bouwen**: BIT (Bitemporal Image Transformer), TinyCD
  (licht en snel), ChangeFormer, Siamese U-Net. De **open-cd** toolbox (OpenMMLab)
  bundelt deze met voorgetrainde gewichten.
- **Voorgetrainde datasets**: zie §3 — vooral LEVIR-CD en WHU-CD (gebouwmutaties op
  ±0,5 m luchtfoto's) liggen dicht bij ons domein; fine-tunen op Nederlandse paren is
  kansrijk.
- **Labels**: (1) BAG-mutaties voor nieuwbouw/sloop, (2) door taxateurs bevestigde
  signalen uit strategie A, (3) een handmatige Label Studio-ronde op jaarparen
  (twee beelden naast elkaar, verschilgebied intekenen).
- **Wanneer**: pas als A structureel te veel ruis geeft of veranderingen mist. Dit is
  een eigen trainingstraject (andere dataloader, andere metriek) — reken op serieus werk.

**Praktische tussenvariant: verschilcomposiet + YOLO (geïmplementeerd als stap 11).**
Smelt de twee jaargangen samen tot één beeld: rood kanaal = oude foto, groen + blauw =
nieuwe foto. Verdwenen objecten kleuren rood, nieuwe cyaan, ongewijzigd blijft grijs.
Op die composieten traint de béstaande YOLO-pipeline gewoon boxen — met verander-klassen
als `zonnepanelen_geplaatst`, `dakkapel_gebouwd`, `nieuwbouw`. Zo krijg je een model dat
effectief beide foto's ziet, zonder nieuwe toolchain (zelfde Label Studio, zelfde Kaggle):

```powershell
python scripts\02_download_tiles.py --laag 2022_orthoHR
python scripts\02_download_tiles.py --laag 2025_orthoHR
python scripts\11_verschilbeeld.py --oud tiles_2022_orthoHR --nieuw tiles_2025_orthoHR
```

De drieluiken in `data\verander\...\preview\` (oud | nieuw | composiet) tonen meteen ook
de uitdaging: omvalling geeft rood/cyaan-randjes langs álle dakranden. Een getraind model
leert die uniforme randruis negeren; naïef pixels vergelijken kan dat niet — dat is
precies het bestaansrecht van de modelroute.

### C. AHN-hoogteverschil (parallel spoor, geen ML nodig)

DSM-verschil tussen AHN-versies, gesneden met BAG-contouren:
hoogte verschenen buiten contour → kandidaat aanbouw/bijgebouw; hoogtebult op dakvlak →
kandidaat dakkapel; hoogte verdwenen → sloop. Puur rekenwerk, geen model, en het vult
precies de klassen waar beelddetectie zwak in is. Kandidaten gaan als pre-annotatie de
bestaande Label Studio-lus in.

---

## 3. Bestaande modellen en datasets om op voort te bouwen

| Dataset/model | Wat | Bruikbaarheid voor ons |
|---|---|---|
| **LEVIR-CD** | 637 beeldparen 0,5 m, gebouwmutaties, VS | Beste startpunt voor fine-tunen (B) |
| **WHU-CD** | Groot gebouwmutatie-paar, 0,2 m, Nieuw-Zeeland | Idem, hogere resolutie |
| **S2Looking** | Gebouwmutaties, schuine kijkhoek, satelliet | Aanvullend |
| **OSCD** | Sentinel-2, 10 m | Te grof voor pandniveau |
| **xBD** | Schade-detectie na rampen | Ander doel, zelfde techniek |
| **open-cd model zoo** | Voorgetrainde BIT/TinyCD/ChangeFormer op bovenstaande | Direct te fine-tunen |
| **SAM-gebaseerd zero-shot** (bijv. AnyChange) | Verandering zonder training | Onderzoeksstadium; experiment waard, geen fundament |

**Wat er níet bestaat**: publieke verander-datasets op het niveau van zonnepanelen,
dakkapellen of steigers. Voor die klassen is strategie A (verschil-van-detecties) dan
ook niet een tussenoplossing maar de logische route — de detectiekant hebben we immers
zelf in de hand.

---

## 4. Bestaande Nederlandse producten (build vs buy)

Mutatiesignalering wordt in Nederland commercieel geleverd, o.a. door **NEO**
(MutatieSignalering, breed gebruikt door gemeenten voor BAG/WOZ), **READAR**
(dakobjecten en mutaties uit luchtfoto's) en **Sobolt**; **Cyclomedia** levert de
schuine beelden die gevelmutaties zichtbaar maken. Veel belastingsamenwerkingen nemen
al zo'n dienst af — **check dit eerst binnen BWB** voordat we het zelf bouwen.
Zelf bouwen blijft interessant voor: eigen klassen (steiger/bouwactiviteit), eigen
drempels, integratie met taxatiedossiers, en géén licentiekosten per signaal — maar
weet wat er al ingekocht is.

---

## 5. Haalbaarheid per verandertype

| Verandering | Detecteerbaarheid | Beste route |
|---|---|---|
| Zonnepanelen geplaatst/verwijderd | Uitstekend (hoog contrast) | A: detector-diff |
| Dakkapel gebouwd | Goed | A, + C ter bevestiging |
| Aanbouw | Matig op beeld, sterk op hoogte | C (AHN-diff), A als steun |
| Bijgebouw/schuur verschenen | Goed | A + BAG-vergelijking (staat hij al in BAG?) |
| Zwembad aangelegd | Uitstekend | A |
| Nieuwbouw/sloop | Triviaal | BAG-mutaties (geen ML nodig) |
| **Steiger/bouwactiviteit** | Beperkt: tijdelijk object, jaarcadans mist veel | Aparte klasse "bouwactiviteit" (steiger, bouwketen, kraan, zand/materiaal) op de actuele foto — signaal "hier wordt verbouwd", geen verander-paar nodig |
| Gevelwijzigingen (erker, kozijnen) | Niet vanaf nadir | Schuine foto's (Cyclomedia) — apart traject |

Over de steiger: behandel "er wordt verbouwd" als **toestand op één foto** in plaats
van als verandering tussen twee foto's — dan is de jaarcadans geen probleem meer en
is het gewoon een extra detectieklasse in de bestaande pipeline.

---

## 6. Concreet stappenplan in deze repo

**Fase 1 — nu (loopt al):** objectdetector afmaken via de bestaande lus
(annoteren → trainen → pre-annoteren). Elke verbetering hier is directe winst voor de
mutatiesignalering.

**Fase 2 — detector-diff (klein bouwwerk):**
1. `10_download_jaargang.py`: zelfde tegelgrid, maar met laag-parameter
   (bijv. `2022_orthoHR`) en uitvoer naar `data/tiles_2022/`. Grotendeels hergebruik
   van stap 02.
2. `11_mutaties.py`: draai het model op twee jaargang-mappen, koppel detecties aan
   BAG-panden (tegels zijn geo-gerefereerd), pas de confidence-drempels toe en schrijf
   een mutatielijst (CSV/GeoJSON: pand-id, verandertype, confidence t1/t2) plus
   voor/na-previewbeelden per signaal.
3. Verificatie in Label Studio: de mutatielijst als werklijst; bevestigd/afgewezen
   wordt vastgelegd → trainingsdata voor fase 3.

**Fase 3 — optioneel:** bi-temporeel model (open-cd, gestart vanaf LEVIR-CD-gewichten)
op de paren + labels uit fase 2, trainen op Kaggle zoals we nu ook doen.

---

## 7. Juridische aandachtspunten

Mutatiesignalering die tot controle of aanslag kan leiden raakt **art. 22 AVG**
(geautomatiseerde besluitvorming). Dezelfde lijn als het hoofdproject: het systeem
*signaleert*, de taxateur *beslist* — en dat aantoonbaar (elke aanslag heeft een
menselijke beoordeling tussen signaal en besluit). Plan DPIA/IAMA en opname in het
Algoritmeregister vóór productie. PDOK-beelden zijn CC-BY: bronvermelding verplicht,
ook in afgeleide mutatielijsten.

---

*Bevat gegevens van PDOK: Luchtfoto Beeldmateriaal Nederland (CC-BY 4.0), de BAG en het AHN.*
