"""Stap 11 — verschilcomposieten bouwen uit twee luchtfoto-jaargangen.

Gebruik:
    python scripts/11_verschilbeeld.py --oud tiles_2022_orthoHR --nieuw tiles_2025_orthoHR

Vereist: stap 02 voor beide jaargangen, bijv.:
    python scripts/02_download_tiles.py --laag 2022_orthoHR
    python scripts/02_download_tiles.py --laag 2025_orthoHR

Het composiet legt beide jaren in één beeld: rood kanaal = oude foto,
groen + blauw = nieuwe foto. Wat verdween kleurt rood, wat erbij kwam cyaan,
wat gelijk bleef blijft grijs. Op deze composieten kan de bestaande
YOLO-pipeline veranderingen als boxen leren detecteren.

Uitvoer:
    data/verander/<oud>__<nieuw>/composites/*.jpg
    data/verander/<oud>__<nieuw>/index.json      geo-administratie per composiet
    data/verander/<oud>__<nieuw>/preview/*.jpg   oud | nieuw | composiet naast elkaar
"""

from __future__ import annotations

import argparse
import json

from PIL import Image
from tqdm import tqdm

from common import data_pad, laad_config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oud", required=True, help="tegelmap van de oude jaargang (bijv. tiles_2022_orthoHR)")
    parser.add_argument("--nieuw", required=True, help="tegelmap van de nieuwe jaargang")
    parser.add_argument("--config", default=None, help="pad naar config.yaml")
    parser.add_argument("--previews", type=int, default=8, help="aantal voorbeeld-drieluiken")
    args = parser.parse_args()

    cfg = laad_config(args.config)
    oud_map = data_pad(cfg, args.oud, ".houder").parent
    nieuw_map = data_pad(cfg, args.nieuw, ".houder").parent
    for map_ in (oud_map, nieuw_map):
        if not (map_ / "tiles.json").exists():
            raise SystemExit(f"{map_ / 'tiles.json'} ontbreekt — draai eerst stap 02 voor die jaargang.")

    with open(oud_map / "tiles.json", encoding="utf-8") as f:
        oud_index = json.load(f)
    with open(nieuw_map / "tiles.json", encoding="utf-8") as f:
        nieuw_index = json.load(f)

    paar_naam = f"{args.oud.removeprefix('tiles_')}__{args.nieuw.removeprefix('tiles_')}"
    uit_map = data_pad(cfg, "verander", paar_naam, ".houder").parent
    comp_map = uit_map / "composites"
    prev_map = uit_map / "preview"
    comp_map.mkdir(parents=True, exist_ok=True)
    prev_map.mkdir(parents=True, exist_ok=True)

    gemeenschappelijk = sorted(set(oud_index) & set(nieuw_index))
    if not gemeenschappelijk:
        raise SystemExit("Geen gemeenschappelijke tegels tussen de twee jaargangen.")

    index = {}
    for i, tegel_id in enumerate(tqdm(gemeenschappelijk, desc="composieten")):
        oud_beeld = Image.open(oud_map / oud_index[tegel_id]["image"]).convert("L")
        nieuw_beeld = Image.open(nieuw_map / nieuw_index[tegel_id]["image"]).convert("L")
        if oud_beeld.size != nieuw_beeld.size:
            nieuw_beeld = nieuw_beeld.resize(oud_beeld.size)

        composiet = Image.merge("RGB", (oud_beeld, nieuw_beeld, nieuw_beeld))
        composiet.save(comp_map / f"{tegel_id}.jpg", quality=90)
        index[tegel_id] = {
            "bbox": nieuw_index[tegel_id]["bbox"],
            "oud": oud_index[tegel_id]["laag"],
            "nieuw": nieuw_index[tegel_id]["laag"],
        }

        if i < args.previews:
            breedte, hoogte = oud_beeld.size
            drieluik = Image.new("RGB", (breedte * 3 + 20, hoogte), (255, 255, 255))
            drieluik.paste(Image.open(oud_map / oud_index[tegel_id]["image"]).convert("RGB"), (0, 0))
            drieluik.paste(Image.open(nieuw_map / nieuw_index[tegel_id]["image"]).convert("RGB"),
                           (breedte + 10, 0))
            drieluik.paste(composiet, (breedte * 2 + 20, 0))
            drieluik.save(prev_map / f"{tegel_id}.jpg", quality=85)

    with open(uit_map / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1)

    print(f"Klaar: {len(index)} composieten -> {comp_map}")
    print(f"Drieluiken (oud | nieuw | composiet) -> {prev_map}")
    print("Rood = verdwenen, cyaan = nieuw, grijs = ongewijzigd.")


if __name__ == "__main__":
    main()
