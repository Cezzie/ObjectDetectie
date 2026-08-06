"""Stap 1 — BAG-pandcontouren ophalen binnen het projectgebied.

Gebruik:
    python scripts/01_fetch_bag.py [--config config.yaml] [--bbox xmin,ymin,xmax,ymax]

Uitvoer:
    data/bag/panden.geojson  (RD-coördinaten, EPSG:28992)
"""

from __future__ import annotations

import argparse
import json

from common import data_pad, laad_config, parse_bbox
from pdok import fetch_bag_panden, make_session


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="pad naar config.yaml")
    parser.add_argument("--bbox", type=parse_bbox, default=None,
                        help="RD-bbox die de config overschrijft: xmin,ymin,xmax,ymax")
    parser.add_argument("--forceer", action="store_true",
                        help="opnieuw ophalen, ook als de data er al staat")
    args = parser.parse_args()

    cfg = laad_config(args.config)
    bbox = args.bbox or cfg["gebied"]["bbox"]

    uitvoer = data_pad(cfg, "bag", "panden.geojson")
    if uitvoer.exists() and not args.forceer:
        with open(uitvoer, encoding="utf-8") as f:
            bestaand = json.load(f)
        if bestaand.get("bbox_rd") == list(bbox):
            print(f"Al gedaan: {uitvoer} bevat {len(bestaand['features'])} panden voor deze bbox.")
            print("Gebruik --forceer om opnieuw op te halen (bijv. voor BAG-mutaties).")
            return
        print("Bestaande data is van een ándere bbox — er wordt opnieuw opgehaald.")

    print(f"BAG-panden ophalen binnen RD-bbox {bbox} ...")
    sessie = make_session()
    features = fetch_bag_panden(
        sessie,
        cfg["bag"]["wfs_url"],
        tuple(bbox),
        alleen_in_gebruik=cfg["bag"]["alleen_in_gebruik"],
    )

    collectie = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::28992"}},
        "bbox_rd": bbox,
        "bron": "BAG via PDOK (https://www.pdok.nl)",
        "features": features,
    }
    with open(uitvoer, "w", encoding="utf-8") as f:
        json.dump(collectie, f)

    print(f"Klaar: {len(features)} panden -> {uitvoer}")


if __name__ == "__main__":
    main()
