"""Stap 7 — Label Studio-annotaties terugzetten naar YOLO-labels.

Gebruik:
    python scripts/07_import_labelstudio.py pad/naar/export.json [--config config.yaml]

In Label Studio: selecteer de taken -> Export -> formaat JSON.
Geannoteerde tegels overschrijven hun (zwakke) labels in data/tiles/labels/;
tegels zonder annotatie blijven ongemoeid. Draai daarna stap 04 opnieuw.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter

from common import data_pad, laad_config

TEGEL_PATROON = re.compile(r"t_\d{4}_\d{4}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", help="JSON-export uit Label Studio")
    parser.add_argument("--config", default=None, help="pad naar config.yaml")
    args = parser.parse_args()

    cfg = laad_config(args.config)
    klassen: list[str] = cfg["dataset"]["klassen"]
    labels_map = data_pad(cfg, "tiles", "labels", ".houder").parent

    with open(args.export, encoding="utf-8") as f:
        taken = json.load(f)

    per_klasse: Counter[str] = Counter()
    onbekend: Counter[str] = Counter()
    bijgewerkt: list[str] = []

    for taak in taken:
        beeld_ref = taak.get("data", {}).get("image", "")
        match = TEGEL_PATROON.search(beeld_ref)
        if not match:
            print(f"  Overgeslagen: geen tegel-id herkend in '{beeld_ref}'")
            continue
        tegel_id = match.group()

        annotaties = [a for a in taak.get("annotations", []) if not a.get("was_cancelled")]
        if not annotaties:
            continue  # niet geannoteerd: zwakke labels blijven staan

        regels = []
        for result in annotaties[-1].get("result", []):  # nieuwste annotatie telt
            if result.get("type") != "rectanglelabels":
                continue
            naam = result["value"]["rectanglelabels"][0]
            if naam not in klassen:
                onbekend[naam] += 1
                continue
            w = result["value"]["width"] / 100
            h = result["value"]["height"] / 100
            cx = result["value"]["x"] / 100 + w / 2
            cy = result["value"]["y"] / 100 + h / 2
            regels.append(f"{klassen.index(naam)} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
            per_klasse[naam] += 1

        (labels_map / f"{tegel_id}.txt").write_text(
            "\n".join(regels) + ("\n" if regels else ""), encoding="utf-8")
        bijgewerkt.append(tegel_id)

    # Administratie zodat stap 03 en 06 deze tegels voortaan met rust laten.
    geannoteerd_pad = labels_map.parent / "geannoteerd.json"
    geannoteerd: set[str] = set(bijgewerkt)
    if geannoteerd_pad.exists():
        with open(geannoteerd_pad, encoding="utf-8") as f:
            geannoteerd |= set(json.load(f))
    with open(geannoteerd_pad, "w", encoding="utf-8") as f:
        json.dump(sorted(geannoteerd), f, indent=1)

    n_tegels = len(bijgewerkt)
    print(f"Klaar: {n_tegels} tegels bijgewerkt in {labels_map} "
          f"(totaal {len(geannoteerd)} geannoteerde tegels geregistreerd)")
    for naam, aantal in sorted(per_klasse.items()):
        print(f"  {naam}: {aantal} boxen")
    for naam, aantal in onbekend.items():
        print(f"  LET OP: {aantal}x klasse '{naam}' onbekend in config.yaml — overgeslagen")
    if n_tegels:
        print("Draai nu scripts/04_build_dataset.py om de dataset te verversen.")


if __name__ == "__main__":
    main()
