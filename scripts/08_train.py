"""Stap 8 — lokaal trainen: hetzelfde recept als het Kaggle-trainingsnotebook.

Gebruik:
    python scripts/08_train.py [--config config.yaml] [--model yolo11s.pt]
                               [--epochs 100] [--batch 16] [--imgsz 640]

Vereist: stap 04 (de datasetmap) en eenmalig `pip install -r requirements-train.txt`.
Zonder NVIDIA-GPU traint dit op de CPU: prima voor een proefrun met weinig
epochs, maar voor serieuze trainingen is het Kaggle-notebook (gratis GPU) sneller.

Uitvoer: data/runs/<datasetnaam>/weights/best.pt
"""

from __future__ import annotations

import argparse

import yaml

from common import data_pad, laad_config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None, help="pad naar config.yaml")
    parser.add_argument("--model", default="yolo11s.pt",
                        help="startgewichten (yolo11n/s/m/l; n is het snelst, s de standaard)")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default=None,
                        help="reken-apparaat: 0 (NVIDIA), 'mps' (Apple Silicon) of 'cpu'; "
                             "standaard kiest ultralytics zelf")
    args = parser.parse_args()

    try:
        from ultralytics import YOLO
    except ImportError:
        raise SystemExit("ultralytics ontbreekt — draai eerst: pip install -r requirements-train.txt")

    cfg = laad_config(args.config)
    naam = cfg["dataset"]["naam"]
    dataset_map = data_pad(cfg, "dataset", naam, ".houder").parent
    data_yaml = dataset_map / "data.yaml"
    if not data_yaml.exists():
        raise SystemExit(f"{data_yaml} ontbreekt — draai eerst scripts/04_build_dataset.py")

    # Absoluut pad in de data.yaml zetten, anders zoekt ultralytics de dataset
    # in zijn eigen standaard-datasetsmap.
    d = yaml.safe_load(data_yaml.read_text(encoding="utf-8"))
    d["path"] = str(dataset_map)
    data_yaml.write_text(yaml.safe_dump(d, allow_unicode=True), encoding="utf-8")

    runs_map = data_pad(cfg, "runs", ".houder").parent
    model = YOLO(args.model)
    extra = {"device": args.device} if args.device else {}
    model.train(
        data=str(data_yaml),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=20,
        project=str(runs_map),
        name=naam,
        exist_ok=True,
        **extra,
    )

    beste = runs_map / naam / "weights" / "best.pt"
    print(f"\nKlaar. Beste gewichten: {beste}")
    print("Trainingscurves en confusion matrix: " + str(runs_map / naam))


if __name__ == "__main__":
    main()
