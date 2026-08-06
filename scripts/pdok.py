"""PDOK-services: BAG-panden via WFS en luchtfototegels via WMS.

Alles blijft in RD New (EPSG:28992); er is dus nergens herprojectie nodig.
"""

from __future__ import annotations

from collections.abc import Iterator

import requests
from requests.adapters import HTTPAdapter, Retry

# PDOK vraagt om een herkenbare User-Agent bij geautomatiseerd gebruik.
USER_AGENT = "ObjectDetectie-dataset-generator/0.1"

Bbox = tuple[float, float, float, float]


def make_session() -> requests.Session:
    sessie = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    sessie.mount("https://", HTTPAdapter(max_retries=retry))
    sessie.headers["User-Agent"] = USER_AGENT
    return sessie


def fetch_bag_panden(
    sessie: requests.Session,
    wfs_url: str,
    bbox: Bbox,
    alleen_in_gebruik: bool = True,
    pagina_grootte: int = 1000,
) -> list[dict]:
    """Haal alle BAG-pandcontouren binnen de bbox op als GeoJSON-features (RD)."""
    features: list[dict] = []
    start = 0
    while True:
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "bag:pand",
            "srsName": "EPSG:28992",
            "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:28992",
            "outputFormat": "json",
            "count": pagina_grootte,
            "startIndex": start,
        }
        antwoord = sessie.get(wfs_url, params=params, timeout=60)
        antwoord.raise_for_status()
        pagina = antwoord.json().get("features", [])
        features.extend(pagina)
        print(f"  WFS-pagina vanaf {start}: {len(pagina)} panden")
        if len(pagina) < pagina_grootte:
            break
        start += pagina_grootte

    if alleen_in_gebruik:
        features = [f for f in features if f["properties"].get("status") == "Pand in gebruik"]
    return features


def wms_get_map(
    sessie: requests.Session,
    wms_url: str,
    laag: str,
    bbox: Bbox,
    breedte: int,
    hoogte: int,
    formaat: str = "jpeg",
) -> bytes:
    """Vraag één kaartbeeld op bij de WMS en geef de afbeeldingsbytes terug."""
    params = {
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": laag,
        "styles": "",
        "crs": "EPSG:28992",
        "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
        "width": breedte,
        "height": hoogte,
        "format": f"image/{formaat}",
    }
    antwoord = sessie.get(wms_url, params=params, timeout=60)
    antwoord.raise_for_status()
    if not antwoord.headers.get("Content-Type", "").startswith("image/"):
        raise RuntimeError(f"WMS gaf geen afbeelding terug: {antwoord.text[:300]}")
    return antwoord.content


def tegel_grid(bbox: Bbox, tegel_m: float, overlap: float = 0.0) -> Iterator[tuple[int, int, Bbox]]:
    """Genereer (kolom, rij, tegel-bbox) voor een regelmatig grid over de bbox."""
    stap = tegel_m * (1.0 - overlap)
    xmin, ymin, xmax, ymax = bbox
    rij = 0
    y = ymin
    while y < ymax:
        kolom = 0
        x = xmin
        while x < xmax:
            yield kolom, rij, (x, y, x + tegel_m, y + tegel_m)
            x += stap
            kolom += 1
        y += stap
        rij += 1
