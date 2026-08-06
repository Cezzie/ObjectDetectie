"""Stap 9 — een externe YOLO-dataset omzetten naar onze klassenindeling.

Gebruik:
    python scripts/09_externe_dataset.py C:/pad/naar/uitgepakte_dataset ^
        --map "solar-panel=zonnepanelen" --map "pool=zwembad" [--naam roboflow_solar]

Werkt met datasets in YOLO-formaat zoals Roboflow ze exporteert (mappen met
images/ en labels/ en een data.yaml met de klassenamen). Alleen klassen die je
via --map koppelt worden meegenomen; de rest wordt geteld en overgeslagen.

Uitvoer: data/extern/<naam>/images + labels. Stap 04 bakt alles onder
data/extern/ automatisch mee in de TRAIN-split (val blijft puur Nederlandse
tegels, zodat de metrics je echte doel blijven meten). Draai dus hierna
stap 04 opnieuw.
"""

from __future__ import annotations

import argparse
import shutil
from collections import Counter
from pathlib import Path

import yaml

from common import data_pad, laad_config

BEELD_EXTENSIES = [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]


def lees_externe_klassen(bron: Path) -> dict[int, str]:
    """Zoek de data.yaml van de externe dataset en geef index -> klassenaam."""
    for kandidaat in sorted(bron.rglob("data.yaml")):
        namen = yaml.safe_load(kandidaat.read_text(encoding="utf-8")).get("names")
        if isinstance(namen, dict):
            return {int(k): str(v) for k, v in namen.items()}
        if isinstance(namen, list):
            return dict(enumerate(str(n) for n in namen))
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bron", help="map met de uitgepakte externe dataset")
    parser.add_argument("--map", action="append", default=[], metavar="EXTERN=EIGEN",
                        help="klassekoppeling, herhaalbaar: externe naam (of index) = onze klasse")
    parser.add_argument("--naam", default=None, help="naam voor deze bron (standaard: mapnaam)")
    parser.add_argument("--config", default=None, help="pad naar config.yaml")
    args = parser.parse_args()

    cfg = laad_config(args.config)
    klassen: list[str] = cfg["dataset"]["klassen"]
    bron = Path(args.bron)
    if not bron.is_dir():
        raise SystemExit(f"{bron} is geen map — pak de dataset eerst uit.")
    naam = args.naam or bron.name.replace(" ", "_").lower()

    extern_namen = lees_externe_klassen(bron)
    if extern_namen:
        print("Externe klassen gevonden:", ", ".join(f"{i}={n}" for i, n in extern_namen.items()))
    else:
        print("Geen data.yaml gevonden — gebruik indexnummers in --map (bijv. \"0=zonnepanelen\").")

    if not args.map:
        raise SystemExit("Geen --map opgegeven; zonder koppeling valt er niets om te zetten.")

    hernummer: dict[int, int] = {}
    for koppeling in args.map:
        extern, _, eigen = koppeling.partition("=")
        extern, eigen = extern.strip(), eigen.strip()
        if eigen not in klassen:
            raise SystemExit(f"'{eigen}' staat niet in config.yaml (dataset.klassen): {klassen}")
        if extern.isdigit():
            extern_idx = int(extern)
        else:
            kandidaten = [i for i, n in extern_namen.items() if n == extern]
            if not kandidaten:
                raise SystemExit(f"Externe klasse '{extern}' niet gevonden; beschikbaar: "
                                 f"{sorted(extern_namen.values())}")
            extern_idx = kandidaten[0]
        hernummer[extern_idx] = klassen.index(eigen)

    doel = data_pad(cfg, "extern", naam, ".houder").parent
    if doel.exists():
        shutil.rmtree(doel)
    (doel / "images").mkdir(parents=True)
    (doel / "labels").mkdir(parents=True)

    per_klasse: Counter[str] = Counter()
    overgeslagen_boxen = 0
    beelden_zonder_boxen = 0
    n_beelden = 0

    for label_pad in sorted(bron.rglob("*.txt")):
        if label_pad.parent.name != "labels":
            continue
        beeld_pad = None
        for ext in BEELD_EXTENSIES:
            kandidaat = label_pad.parent.parent / "images" / (label_pad.stem + ext)
            if kandidaat.exists():
                beeld_pad = kandidaat
                break
        if beeld_pad is None:
            continue

        regels = []
        for regel in label_pad.read_text(encoding="utf-8").splitlines():
            delen = regel.split()
            if len(delen) != 5:
                continue  # segmentatieregels e.d. slaan we over
            extern_idx = int(delen[0])
            if extern_idx not in hernummer:
                overgeslagen_boxen += 1
                continue
            eigen_idx = hernummer[extern_idx]
            regels.append(" ".join([str(eigen_idx)] + delen[1:]))
            per_klasse[klassen[eigen_idx]] += 1

        if not regels:
            beelden_zonder_boxen += 1
            continue

        nieuw = f"{naam}_{label_pad.stem}"
        shutil.copy2(beeld_pad, doel / "images" / (nieuw + beeld_pad.suffix.lower()))
        (doel / "labels" / (nieuw + ".txt")).write_text("\n".join(regels) + "\n", encoding="utf-8")
        n_beelden += 1

    print(f"\nKlaar: {n_beelden} beelden -> {doel}")
    for k, aantal in sorted(per_klasse.items()):
        print(f"  {k}: {aantal} boxen")
    if overgeslagen_boxen:
        print(f"  (niet-gekoppelde klassen: {overgeslagen_boxen} boxen overgeslagen)")
    if beelden_zonder_boxen:
        print(f"  ({beelden_zonder_boxen} beelden zonder bruikbare boxen weggelaten)")
    if n_beelden:
        print("Draai nu scripts/04_build_dataset.py — externe beelden gaan alleen naar train.")


if __name__ == "__main__":
    main()
