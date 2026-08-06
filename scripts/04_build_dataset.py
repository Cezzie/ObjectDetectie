"""Stap 4 — YOLO-dataset samenstellen, zippen en klaarzetten voor Kaggle.

Gebruik:
    python scripts/04_build_dataset.py [--config config.yaml]

Vereist: stap 2 en 3.
Uitvoer:
    data/dataset/<naam>/                YOLO-mapstructuur + data.yaml
    data/kaggle_upload/<naam>/          zip + dataset-metadata.json voor de Kaggle CLI

De train/val-splitsing gebeurt per blok van `dataset.blok_maat` meter, zodat
aangrenzende tegels (en dus dezelfde buurt) nooit in beide splitsen zitten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil

from tqdm import tqdm

from common import REPO_ROOT, data_pad, laad_config


def split_voor_blok(dataset_naam: str, blok: tuple[int, int], val_fractie: float) -> str:
    """Deterministische train/val-keuze per ruimtelijk blok."""
    sleutel = f"{dataset_naam}:{blok[0]}:{blok[1]}".encode()
    dobbel = int(hashlib.md5(sleutel).hexdigest(), 16) % 1000
    return "val" if dobbel < val_fractie * 1000 else "train"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="pad naar config.yaml")
    args = parser.parse_args()

    cfg = laad_config(args.config)
    ds = cfg["dataset"]
    naam = ds["naam"]

    with open(data_pad(cfg, "tiles", "tiles.json"), encoding="utf-8") as f:
        index = json.load(f)
    tiles_map = data_pad(cfg, "tiles", ".houder").parent

    dataset_map = data_pad(cfg, "dataset", naam, ".houder").parent
    if dataset_map.exists():
        shutil.rmtree(dataset_map)
    for split in ("train", "val"):
        (dataset_map / "images" / split).mkdir(parents=True)
        (dataset_map / "labels" / split).mkdir(parents=True)

    telling = {"train": 0, "val": 0}
    for tegel_id, tegel in tqdm(index.items(), desc="kopiëren"):
        beeld = tiles_map / tegel["image"]
        label = tiles_map / "labels" / f"{tegel_id}.txt"
        if not beeld.exists() or not label.exists():
            continue
        blok = (int(tegel["bbox"][0] // ds["blok_maat"]), int(tegel["bbox"][1] // ds["blok_maat"]))
        split = split_voor_blok(naam, blok, ds["val_fractie"])
        shutil.copy2(beeld, dataset_map / "images" / split / beeld.name)
        shutil.copy2(label, dataset_map / "labels" / split / label.name)
        telling[split] += 1

    data_yaml = (
        f"# Dataset: {naam}\n"
        f"# Bevat gegevens van PDOK: Luchtfoto Beeldmateriaal Nederland (CC-BY 4.0) en de BAG.\n"
        f"path: .\n"
        f"train: images/train\n"
        f"val: images/val\n"
        f"names:\n"
        + "".join(f"  {i}: {k}\n" for i, k in enumerate(ds["klassen"]))
    )
    (dataset_map / "data.yaml").write_text(data_yaml, encoding="utf-8")

    upload_map = data_pad(cfg, "kaggle_upload", naam, ".houder").parent
    upload_map.mkdir(parents=True, exist_ok=True)
    print("Zip maken ...")
    zip_pad = shutil.make_archive(str(upload_map / naam), "zip", dataset_map)
    metadata = {
        "title": naam,
        "id": f"JOUW_KAGGLE_GEBRUIKERSNAAM/{naam}",
        "licenses": [{"name": "CC-BY-SA-4.0"}],
    }
    with open(upload_map / "dataset-metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nKlaar: {telling['train']} train- en {telling['val']} val-tegels")
    print(f"Dataset:    {dataset_map}")
    print(f"Kaggle-zip: {zip_pad}")
    print(
        "\nUploaden naar Kaggle (eenmalig 'pip install kaggle' + API-token, zie README):\n"
        f"  1. Zet je Kaggle-gebruikersnaam in {upload_map / 'dataset-metadata.json'}\n"
        f"  2. Nieuwe dataset:   kaggle datasets create -p {upload_map.relative_to(REPO_ROOT)}\n"
        f"     Nieuwe versie:    kaggle datasets version -p {upload_map.relative_to(REPO_ROOT)} -m \"update\""
    )


if __name__ == "__main__":
    main()
