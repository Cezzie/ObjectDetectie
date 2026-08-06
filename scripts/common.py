"""Gedeelde hulpfuncties: configuratie laden en datapaden bepalen."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def laad_config(pad: str | Path | None = None) -> dict:
    config_pad = Path(pad) if pad else REPO_ROOT / "config.yaml"
    with open(config_pad, encoding="utf-8") as f:
        return yaml.safe_load(f)


def data_pad(cfg: dict, *delen: str) -> Path:
    """Pad binnen de datamap uit de config; maakt de map aan als die ontbreekt."""
    pad = REPO_ROOT / cfg["paden"]["data"]
    for deel in delen:
        pad = pad / deel
    pad.parent.mkdir(parents=True, exist_ok=True)
    return pad


def parse_bbox(tekst: str) -> list[float]:
    """Parseer 'xmin,ymin,xmax,ymax' naar een lijst van vier floats."""
    delen = [float(d) for d in tekst.split(",")]
    if len(delen) != 4:
        raise ValueError("bbox moet vier komma-gescheiden getallen zijn: xmin,ymin,xmax,ymax")
    return delen
