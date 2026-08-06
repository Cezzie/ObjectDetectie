"""Stap 2 — luchtfototegels downloaden voor tegels waar BAG-panden staan.

Gebruik:
    python scripts/02_download_tiles.py [--config config.yaml] [--max-tegels N]

Vereist: stap 1 (data/bag/panden.geojson).
Uitvoer:
    data/tiles/images/t_KKKK_RRRR.jpg   per tegel
    data/tiles/tiles.json               geo-administratie (RD-bbox per tegel)

Het script is herstartbaar: al gedownloade tegels worden overgeslagen.
"""

from __future__ import annotations

import argparse
import json
import time

from shapely.geometry import box, shape
from shapely.strtree import STRtree
from tqdm import tqdm

from common import data_pad, laad_config
from pdok import make_session, tegel_grid, wms_get_map


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="pad naar config.yaml")
    parser.add_argument("--max-tegels", type=int, default=None,
                        help="stop na N tegels (handig om klein te testen)")
    parser.add_argument("--laag", default=None,
                        help="andere jaargang-laag (bijv. 2022_orthoHR); "
                             "uitvoer komt dan in data/tiles_<laag>/")
    args = parser.parse_args()

    cfg = laad_config(args.config)
    foto = cfg["luchtfoto"]
    laag = args.laag or foto["laag"]
    map_naam = "tiles" if laag == foto["laag"] else f"tiles_{laag}"
    tegel_px = foto["tegelgrootte"]
    tegel_m = tegel_px * foto["resolutie"]
    min_panden = cfg["dataset"]["min_panden_per_tegel"]

    panden_pad = data_pad(cfg, "bag", "panden.geojson")
    if not panden_pad.exists():
        raise SystemExit(f"{panden_pad} ontbreekt — draai eerst scripts/01_fetch_bag.py")
    with open(panden_pad, encoding="utf-8") as f:
        panden = [shape(feat["geometry"]) for feat in json.load(f)["features"]]
    boom = STRtree(panden)
    print(f"{len(panden)} pandcontouren geladen")

    index_pad = data_pad(cfg, map_naam, "tiles.json")
    index: dict[str, dict] = {}
    if index_pad.exists():
        with open(index_pad, encoding="utf-8") as f:
            index = json.load(f)

    afbeeldingen_map = data_pad(cfg, map_naam, "images", ".houder").parent
    sessie = make_session()
    gedownload = 0
    overgeslagen_leeg = 0

    tegels = list(tegel_grid(tuple(cfg["gebied"]["bbox"]), tegel_m, foto["overlap"]))
    try:
        for kolom, rij, tegel_bbox in tqdm(tegels, desc="tegels"):
            if args.max_tegels is not None and gedownload >= args.max_tegels:
                break

            tegel_vlak = box(*tegel_bbox)
            n_panden = sum(1 for i in boom.query(tegel_vlak) if panden[i].intersects(tegel_vlak))
            if n_panden < min_panden:
                overgeslagen_leeg += 1
                continue

            tegel_id = f"t_{kolom:04d}_{rij:04d}"
            bestand = afbeeldingen_map / f"{tegel_id}.{foto['formaat']}"
            if tegel_id in index and bestand.exists():
                continue

            beeld = wms_get_map(
                sessie, foto["wms_url"], laag, tegel_bbox,
                breedte=tegel_px, hoogte=tegel_px, formaat=foto["formaat"],
            )
            bestand.write_bytes(beeld)
            index[tegel_id] = {
                "bbox": list(tegel_bbox),
                "image": f"images/{bestand.name}",
                "px": tegel_px,
                "resolutie": foto["resolutie"],
                "n_panden": n_panden,
                "laag": laag,
            }
            gedownload += 1
            time.sleep(foto["wacht_seconden"])
    finally:
        # Ook bij afbreken de administratie bewaren, zodat hervatten werkt.
        with open(index_pad, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=1)

    if gedownload == 0:
        print(f"Al gedaan: alle {len(index)} tegels stonden al op schijf "
              f"({overgeslagen_leeg} tegels zonder panden overgeslagen).")
    else:
        print(f"Klaar: {gedownload} nieuw gedownload, {len(index)} tegels in {index_pad}, "
              f"{overgeslagen_leeg} tegels zonder panden overgeslagen")


if __name__ == "__main__":
    main()
