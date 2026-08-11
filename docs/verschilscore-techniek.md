# De verschilscore: welke techniek zit erachter?

*Uitleg van de methode in `notebooks/mutaties_etten_leur.ipynb`, sectie 2 — inclusief het
antwoord op de vraag: "kun je niet beter eerst de foto's van elkaar aftrekken en dan
een berekening doen?"*

## In één zin

Per pand meten we hoeveel de twee luchtfoto's van elkaar afwijken, **nádat we per foto
eerst de storende verschillen hebben weggenomen** (belichting, textuurruis,
camerastandpunt) — het restverschil binnen de pandcontour is de score.

## De pijplijn, stap voor stap

```
foto 2022 ─► grijswaarden ─► blur ─► normaliseren ─┐
                                                    ├─► |aftrekken| in 9 verschuivingen
foto 2025 ─► grijswaarden ─► blur ─► normaliseren ─┘        │ per pixel het minimum
                                                            ▼
                                     gemiddelde binnen pandcontour ─► score per pand
                                                            ▼
                                     drempel (99e percentiel) ─► detectielijst
```

1. **Grijswaarden.** Kleur voegt voor "is er iets veranderd?" weinig toe, maar
   kleurzweemverschillen tussen jaargangen (andere camera, andere nabewerking) zouden
   wél ruis geven. Weg ermee.
2. **Lichte blur (Gauss, 1,5 px).** Zonder blur "verschilt" elke dakpan van zichzelf
   door scherpte- en ruisverschil tussen de opnames. De blur dempt textuur maar laat
   objecten van betekenisvolle grootte (paneel, dakkapel) intact.
3. **Normaliseren per foto** (z-score: gemiddelde eraf, delen door de spreiding, per
   tegel). Dit haalt globale belichtings- en contrastverschillen weg: was 2022 zonniger
   dan 2025, dan is dat na deze stap onzichtbaar. Dit is een berekening *per foto*,
   vóór enige vergelijking — zie de vraag hieronder waarom dat moet.
4. **Aftrekken, maar verschuivings-tolerant.** We maken 9 varianten van de nieuwe foto
   (verschoven met −8/0/+8 pixels in x en y), berekenen per variant het absolute
   verschil met de oude foto, en nemen per pixel het **minimum** over de 9. Waarom: de
   *omvalling* — daken "leunen" per jaargang een andere kant op omdat het vliegtuig
   ergens anders vloog. Een dak dat een halve meter verschoven lijkt maar verder
   identiek is, vindt in één van de verschuivingen een goede match → klein verschil.
   Een dak waar zonnepanelen op verschenen matcht in géén enkele verschuiving → het
   verschil blijft groot.
5. **Aggregeren per pand, binnen de contour.** Het gemiddelde van de
   minimum-verschilkaart binnen de **pandcontour zelf** (niet de omsluitende box) →
   één getal per pand. Zo telt het erf of de akker rondom een boerderij niet mee —
   juist buiten de stad veranderen die van nature sterk (ploegen, gewassen).
6. **Drempel per omgevingstype.** Panden worden ingedeeld in *stedelijk* of
   *buitengebied* (op panddichtheid per tegel, `STEDELIJK_VANAF`), en de drempel
   (percentiel `DREMPEL_PCT`) wordt bínnen elk stratum bepaald. Reden: de
   score-verdelingen verschillen structureel tussen stad en buitengebied; één
   globale drempel zou de werkvoorraad vullen met buitengebied-ruis en stedelijke
   subtiele veranderingen verdringen. Het notebook toont beide verdelingen als
   histogram, elk met hun eigen drempellijn. Alles boven de eigen drempel is een
   "visuele detectie" en wordt gesplitst in *verklaard door de BAG* en
   *onverklaard* (de werkvoorraad).

## "Kun je niet beter eerst aftrekken en dan berekenen?"

Dat is de klassieke naïeve aanpak (*image differencing*) — en hij is aantoonbaar
zwakker, om twee redenen die allebei neerkomen op **informatieverlies**:

1. **Belichting is per foto, niet per verschil.** Trek je de rauwe foto's af, dan
   "verandert" de hele stad zodra 2025 iets donkerder is opgenomen dan 2022. En na het
   aftrekken is het onherstelbaar: uit het verschilbeeld kun je niet meer afleiden of
   een afwijking door licht of door echte verandering komt. De normalisatie *moet* dus
   per foto gebeuren, vóór de aftrekking.
2. **De verschuivingstruc heeft beide foto's nodig.** Om omvalling te dempen schuiven
   we de nieuwe foto in negen richtingen ten opzichte van de oude en houden per pixel
   de beste match over. Van een reeds afgetrokken beeld valt niets meer te verschuiven —
   die informatie is weg.

De vuistregel uit de verander-detectieliteratuur is daarom: **eerst per beeld
corrigeren en kenmerken berekenen, dán pas vergelijken.** Aardig om te zien: het
geplande bi-temporele verandermodel (zie [mutatiedetectie.md](mutatiedetectie.md)) is
precies de geleerde versie van dit principe — een siamees netwerk stuurt beide foto's
eerst elk door dezelfde encoder (berekening per foto) en vergelijkt daarna de
kenmerken. Wat wij hier met blur + normalisatie + verschuivingen met de hand doen,
leert zo'n netwerk zelf, en beter.

## Parameters en hun effect

| Parameter | Waarde | Effect bij verhogen/verlagen |
|---|---|---|
| Blur | 1,5 px | Hoger: minder textuurruis, maar kleine objecten (dakraam) vervagen |
| Verschuivingsbereik | ±8 px (≈ 0,64 m) | Hoger: meer omvalling gedempt, maar echte kleine verplaatsingen worden ook "weggematcht"; trager |
| Minimale pandgrootte | 25 m² / 12 px | Lager: ook schuurtjes gescoord, maar meer ruis |
| `STEDELIJK_VANAF` | 6 panden per tegel | Grens stedelijk/buitengebied voor de eigen drempel per stratum |
| `DREMPEL_PCT` | 99 | Lager (97/95): meer vangst (hogere recall op BAG-mutaties), grotere werkvoorraad |

Kalibreer de drempel met sectie 3b van het notebook: de bekende BAG-mutaties zijn de
gratis grondwaarheid — nieuwbouw hoort grotendeels bóven de drempel te zitten,
"bouwvergunning verleend" (nog niets gebouwd) juist eronder.

## Eerlijke beperkingen

- **Omvalling groter dan 8 px** (hoge gebouwen aan de rand van een vluchtstrook) geeft
  nog steeds valse detecties.
- **Schaduwrichting en seizoen**: ook binnen "winter" verschillen zonnestand en
  vochtigheid van daken per opnamedag.
- **Bomen die over een dak hangen** veranderen van vorm en tellen mee in de box.
- **De box is grover dan de contour**: bij dicht op elkaar staande panden lekt
  verandering van de buurman de box in.
- **De score zegt "hier is iets anders", niet wát.** De classificatie (zonnepanelen?
  dakkapel? renovatie?) komt van het YOLO-model en uiteindelijk het verandermodel;
  de score is de zeef die bepaalt wáár die modellen moeten kijken.

*Bevat gegevens van PDOK: Luchtfoto Beeldmateriaal Nederland (CC-BY 4.0) en de BAG.*
