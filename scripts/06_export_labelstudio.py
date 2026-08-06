"""Stap 6 — tegels exporteren naar Label Studio: taken, pre-annotaties en interface.

Gebruik:
    python scripts/06_export_labelstudio.py [--config config.yaml] [--aantal N]

Vereist: stap 2 (en stap 3 als je de zwakke pand-labels als pre-annotatie wilt).
Uitvoer:
    data/labelstudio/tasks.json            importeren via de Label Studio-UI
    data/labelstudio/labeling_config.xml   plakken onder Settings -> Labeling Interface

De beeld-URL's gaan uit van Label Studio met lokale bestandsserving en
data/tiles als document-root — zie de README voor de opstartcommando's.
"""

from __future__ import annotations

import argparse
import json
import random

from common import data_pad, laad_config

# Vaste kleur per klasse-index; herhaalt zich als er ooit meer klassen komen.
KLEUREN = ["#94A3B8", "#2563EB", "#F59E0B", "#10B981", "#8B5CF6",
           "#EF4444", "#EC4899", "#14B8A6", "#06B6D4"]


def yolo_regel_naar_result(regel: str, klassen: list[str]) -> dict | None:
    idx, cx, cy, b, h = regel.split()
    idx = int(idx)
    cx, cy, b, h = float(cx), float(cy), float(b), float(h)
    if idx >= len(klassen):
        return None
    return {
        "from_name": "label",
        "to_name": "image",
        "type": "rectanglelabels",
        "original_width": 640,
        "original_height": 640,
        "value": {
            "x": (cx - b / 2) * 100,
            "y": (cy - h / 2) * 100,
            "width": b * 100,
            "height": h * 100,
            "rectanglelabels": [klassen[idx]],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="pad naar config.yaml")
    parser.add_argument("--aantal", type=int, default=None,
                        help="willekeurige (maar reproduceerbare) greep van N tegels "
                             "in plaats van alles — handig voor annotatierondes")
    args = parser.parse_args()

    cfg = laad_config(args.config)
    klassen: list[str] = cfg["dataset"]["klassen"]
    tiles_map = data_pad(cfg, "tiles", ".houder").parent
    with open(tiles_map / "tiles.json", encoding="utf-8") as f:
        index = json.load(f)

    keuze = sorted(index)
    if args.aantal is not None and args.aantal < len(keuze):
        keuze = sorted(random.Random(42).sample(keuze, args.aantal))

    taken = []
    n_pre = 0
    for tegel_id in keuze:
        bestandsnaam = index[tegel_id]["image"].split("/")[-1]
        taak = {"data": {"image": f"/data/local-files/?d=images/{bestandsnaam}"}}

        label_pad = tiles_map / "labels" / f"{tegel_id}.txt"
        if label_pad.exists():
            results = [r for r in (yolo_regel_naar_result(regel, klassen)
                                   for regel in label_pad.read_text(encoding="utf-8").splitlines())
                       if r is not None]
            if results:
                taak["predictions"] = [{"model_version": "zwakke-labels", "result": results}]
                n_pre += len(results)
        taken.append(taak)

    ls_map = data_pad(cfg, "labelstudio", ".houder").parent
    ls_map.mkdir(parents=True, exist_ok=True)
    with open(ls_map / "tasks.json", "w", encoding="utf-8") as f:
        json.dump(taken, f, indent=1)

    labels_xml = "\n".join(
        f'    <Label value="{k}" background="{KLEUREN[i % len(KLEUREN)]}"/>'
        for i, k in enumerate(klassen)
    )
    (ls_map / "labeling_config.xml").write_text(
        '<View>\n'
        '  <Image name="image" value="$image" zoom="true" zoomControl="true"/>\n'
        '  <RectangleLabels name="label" toName="image">\n'
        f'{labels_xml}\n'
        '  </RectangleLabels>\n'
        '</View>\n',
        encoding="utf-8",
    )

    print(f"Klaar: {len(taken)} taken ({n_pre} pre-annotaties) -> {ls_map / 'tasks.json'}")
    print(f"Labelinterface -> {ls_map / 'labeling_config.xml'}")


if __name__ == "__main__":
    main()
