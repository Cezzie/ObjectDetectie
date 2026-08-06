"""Stap 4 — YOLO-dataset samenstellen, zippen en klaarzetten voor Kaggle.

Gebruik:
    python scripts/04_build_dataset.py [--config config.yaml]

Vereist: stap 2 en 3.
Uitvoer:
    data/dataset/<naam>/                YOLO-mapstructuur + data.yaml
    data/kaggle_upload/<naam>/          zip + dataset-metadata.json voor de Kaggle CLI

De train/val-splitsing gebeurt per blok van `dataset.blok_maat` meter, zodat
aangrenzende tegels (en dus dezelfde buurt) nooit in beide splitsen zitten.
De keuze is deterministisch en garandeert dat val nooit leeg is.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil

from tqdm import tqdm

from common import REPO_ROOT, data_pad, laad_config


def kies_val_tegels(naam: str, geldig: list[tuple], val_fractie: float) -> set[str]:
    """Bepaal deterministisch welke tegel-ids naar val gaan.

    Blokken worden op hash gerangschikt en de eerste ~val_fractie wordt val,
    zodat val nooit leeg is (het oude kansdrempel-schema kon bij weinig
    blokken toevallig alles aan train toewijzen). Is er maar één blok, dan
    valt de splitsing terug op tegelniveau.
    """
    def rang(sleutel: str) -> str:
        return hashlib.md5(f"{naam}:{sleutel}".encode()).hexdigest()

    blokken = sorted({blok for *_, blok in geldig}, key=lambda b: rang(f"{b[0]}:{b[1]}"))
    if len(blokken) > 1:
        n_val = min(len(blokken) - 1, max(1, round(val_fractie * len(blokken))))
        val_blokken = set(blokken[:n_val])
        return {tegel_id for tegel_id, *_, blok in geldig if blok in val_blokken}

    tegels = sorted((tegel_id for tegel_id, *_ in geldig), key=rang)
    if len(tegels) < 2:
        return set()
    n_val = min(len(tegels) - 1, max(1, round(val_fractie * len(tegels))))
    return set(tegels[:n_val])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="pad naar config.yaml")
    parser.add_argument("--geen-zip", action="store_true",
                        help="alleen de datasetmap bouwen, geen zip voor de Kaggle CLI "
                             "(gebruik dit als het script óp Kaggle draait)")
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

    geldig = []
    for tegel_id, tegel in index.items():
        beeld = tiles_map / tegel["image"]
        label = tiles_map / "labels" / f"{tegel_id}.txt"
        if not beeld.exists() or not label.exists():
            continue
        blok = (int(tegel["bbox"][0] // ds["blok_maat"]), int(tegel["bbox"][1] // ds["blok_maat"]))
        geldig.append((tegel_id, beeld, label, blok))
    if not geldig:
        raise SystemExit("Geen tegels met beeld én label gevonden — draai eerst stap 02 en 03.")

    val_tegels = kies_val_tegels(naam, geldig, ds["val_fractie"])
    telling = {"train": 0, "val": 0}
    for tegel_id, beeld, label, _ in tqdm(geldig, desc="kopiëren"):
        split = "val" if tegel_id in val_tegels else "train"
        shutil.copy2(beeld, dataset_map / "images" / split / beeld.name)
        shutil.copy2(label, dataset_map / "labels" / split / label.name)
        telling[split] += 1

    # Externe datasets (stap 09) gaan alleen naar train: de val-split blijft
    # puur Nederlandse tegels, zodat de metrics het echte doel meten.
    n_extern = 0
    extern_basis = data_pad(cfg, "extern", ".houder").parent
    for beeld in sorted(extern_basis.glob("*/images/*")):
        label = beeld.parent.parent / "labels" / (beeld.stem + ".txt")
        if not label.exists():
            continue
        shutil.copy2(beeld, dataset_map / "images" / "train" / beeld.name)
        shutil.copy2(label, dataset_map / "labels" / "train" / label.name)
        n_extern += 1

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

    print(f"\nKlaar: {telling['train']} train- en {telling['val']} val-tegels"
          + (f", plus {n_extern} externe trainingsbeelden" if n_extern else ""))
    print(f"Dataset:    {dataset_map}")
    if args.geen_zip:
        return

    upload_map = data_pad(cfg, "kaggle_upload", naam, ".houder").parent
    upload_map.mkdir(parents=True, exist_ok=True)
    print("Zip maken ...")
    zip_pad = shutil.make_archive(str(upload_map / naam), "zip", dataset_map)
    gebruiker = cfg.get("kaggle", {}).get("gebruikersnaam", "JOUW_KAGGLE_GEBRUIKERSNAAM")
    metadata = {
        "title": naam,
        # Kaggle-slugs gebruiken koppeltekens, geen underscores.
        "id": f"{gebruiker}/{naam.replace('_', '-')}",
        "licenses": [{"name": "CC-BY-SA-4.0"}],
    }
    with open(upload_map / "dataset-metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Kaggle-zip: {zip_pad}")
    print(
        f"\nUploaden naar Kaggle (als {metadata['id']}):\n"
        f"  Nieuwe dataset:   kaggle datasets create -p {upload_map.relative_to(REPO_ROOT)}\n"
        f"  Nieuwe versie:    kaggle datasets version -p {upload_map.relative_to(REPO_ROOT)} -m \"update\""
    )


if __name__ == "__main__":
    main()
