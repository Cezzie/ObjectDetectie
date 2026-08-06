"""Stap 5 (controle) — labels over de luchtfoto's tekenen om de kwaliteit te beoordelen.

Gebruik:
    python scripts/05_preview.py [--config config.yaml] [--aantal 8]

Uitvoer:
    data/preview/*.jpg   tegels met rode boxen per gelabeld object
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter

from PIL import Image, ImageDraw

from common import KLEUREN, data_pad, laad_config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="pad naar config.yaml")
    parser.add_argument("--aantal", type=int, default=8, help="aantal willekeurige tegels")
    parser.add_argument("--alleen-geannoteerde", action="store_true",
                        help="alleen tegels tonen die al handmatig geannoteerd zijn (stap 07)")
    args = parser.parse_args()

    cfg = laad_config(args.config)
    tiles_map = data_pad(cfg, "tiles", ".houder").parent
    preview_map = data_pad(cfg, "preview", ".houder").parent
    preview_map.mkdir(parents=True, exist_ok=True)

    with open(tiles_map / "tiles.json", encoding="utf-8") as f:
        index = json.load(f)

    pool = sorted(index)
    if args.alleen_geannoteerde:
        geannoteerd_pad = tiles_map / "geannoteerd.json"
        if not geannoteerd_pad.exists():
            raise SystemExit("Nog geen handmatige annotaties geregistreerd — draai eerst stap 07.")
        with open(geannoteerd_pad, encoding="utf-8") as f:
            pool = [t for t in sorted(json.load(f)) if t in index]

    keuze = random.sample(pool, k=min(args.aantal, len(pool)))
    for tegel_id in keuze:
        tegel = index[tegel_id]
        beeld = Image.open(tiles_map / tegel["image"]).convert("RGB")
        teken = ImageDraw.Draw(beeld)
        px = tegel["px"]

        label_pad = tiles_map / "labels" / f"{tegel_id}.txt"
        if label_pad.exists():
            for regel in label_pad.read_text(encoding="utf-8").splitlines():
                delen = regel.split()
                idx = int(delen[0])
                cx, cy, b, h = (float(d) for d in delen[1:])
                x0, y0 = (cx - b / 2) * px, (cy - h / 2) * px
                x1, y1 = (cx + b / 2) * px, (cy + h / 2) * px
                teken.rectangle([x0, y0, x1, y1],
                                outline=KLEUREN[idx % len(KLEUREN)], width=3)

        uitvoer = preview_map / f"{tegel_id}.jpg"
        beeld.save(uitvoer, quality=90)
        print(f"  {uitvoer}")

    print(f"Klaar: {len(keuze)} previews in {preview_map}")

    # Samenvatting van de huidige labelstand (zwak + handmatig samen).
    klassen: list[str] = cfg["dataset"]["klassen"]
    telling: Counter[int] = Counter()
    for label_pad in (tiles_map / "labels").glob("*.txt"):
        for regel in label_pad.read_text(encoding="utf-8").splitlines():
            telling[int(regel.split()[0])] += 1
    print("\nStand van de labels:")
    for idx in range(len(klassen)):
        print(f"  {klassen[idx]:<20} {telling.get(idx, 0)} boxen")
    geannoteerd_pad = tiles_map / "geannoteerd.json"
    if geannoteerd_pad.exists():
        with open(geannoteerd_pad, encoding="utf-8") as f:
            print(f"  ({len(json.load(f))} tegels handmatig geannoteerd)")


if __name__ == "__main__":
    main()
