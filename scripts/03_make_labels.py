"""Stap 3 — zwakke labels genereren: BAG-contouren -> YOLO-boxen per tegel.

Gebruik:
    python scripts/03_make_labels.py [--config config.yaml]

Vereist: stap 1 en 2.
Uitvoer:
    data/tiles/labels/t_KKKK_RRRR.txt   YOLO-formaat: "klasse cx cy w h" (genormaliseerd)

Alleen de klasse 'pand' wordt automatisch gelabeld; de overige klassen uit de
config worden later handmatig toegevoegd/gecorrigeerd (zie README).
"""

from __future__ import annotations

import argparse
import json

from shapely.geometry import box, shape
from shapely.strtree import STRtree
from tqdm import tqdm

from common import data_pad, laad_config

# Randjes van buurpanden die nog nét de tegel in prikken zijn geen bruikbare
# trainingsvoorbeelden: filter op minimale oppervlakte en boxgrootte.
MIN_OPPERVLAK_M2 = 2.0
MIN_BOX_PX = 6


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="pad naar config.yaml")
    parser.add_argument("--forceer", action="store_true",
                        help="ook handmatig geannoteerde tegels overschrijven met zwakke labels "
                             "(LET OP: dat gooit annotatiewerk weg)")
    args = parser.parse_args()

    cfg = laad_config(args.config)
    klassen: list[str] = cfg["dataset"]["klassen"]
    klasse_pand = klassen.index("pand")

    # Tegels die via Label Studio zijn geannoteerd (stap 07) niet overschrijven.
    geannoteerd_pad = data_pad(cfg, "tiles", "geannoteerd.json")
    geannoteerd: set[str] = set()
    if geannoteerd_pad.exists() and not args.forceer:
        with open(geannoteerd_pad, encoding="utf-8") as f:
            geannoteerd = set(json.load(f))

    with open(data_pad(cfg, "bag", "panden.geojson"), encoding="utf-8") as f:
        panden = [shape(feat["geometry"]) for feat in json.load(f)["features"]]
    boom = STRtree(panden)

    with open(data_pad(cfg, "tiles", "tiles.json"), encoding="utf-8") as f:
        index = json.load(f)

    labels_map = data_pad(cfg, "tiles", "labels", ".houder").parent
    n_boxen = 0
    beschermd = 0

    for tegel_id, tegel in tqdm(index.items(), desc="labels"):
        if tegel_id in geannoteerd:
            beschermd += 1
            continue
        xmin, ymin, xmax, ymax = tegel["bbox"]
        res = tegel["resolutie"]
        px = tegel["px"]
        tegel_vlak = box(xmin, ymin, xmax, ymax)

        regels = []
        for i in boom.query(tegel_vlak):
            geknipt = panden[i].intersection(tegel_vlak)
            if geknipt.is_empty or geknipt.area < MIN_OPPERVLAK_M2:
                continue
            gxmin, gymin, gxmax, gymax = geknipt.bounds

            # RD -> pixels; de y-as klapt om (beeldrij 0 ligt aan de noordkant).
            bx_min = (gxmin - xmin) / res
            bx_max = (gxmax - xmin) / res
            by_min = (ymax - gymax) / res
            by_max = (ymax - gymin) / res
            if bx_max - bx_min < MIN_BOX_PX or by_max - by_min < MIN_BOX_PX:
                continue

            cx = (bx_min + bx_max) / 2 / px
            cy = (by_min + by_max) / 2 / px
            b = (bx_max - bx_min) / px
            h = (by_max - by_min) / px
            regels.append(f"{klasse_pand} {cx:.6f} {cy:.6f} {b:.6f} {h:.6f}")

        (labels_map / f"{tegel_id}.txt").write_text("\n".join(regels) + ("\n" if regels else ""),
                                                    encoding="utf-8")
        n_boxen += len(regels)

    print(f"Klaar: {n_boxen} boxen over {len(index) - beschermd} tegels -> {labels_map}")
    if beschermd:
        print(f"{beschermd} handmatig geannoteerde tegels met rust gelaten "
              f"(--forceer overschrijft ze, maar dat gooit annotatiewerk weg).")


if __name__ == "__main__":
    main()
