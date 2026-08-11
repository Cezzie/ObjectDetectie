<#
Stap 6 — stadsbrede mutatiescan: heel Etten-Leur, luchtfoto 2022 -> 2025.

Downloadt de BAG en beide luchtfoto-jaargangen voor heel Etten-Leur
(± 1 GB schijf, ± 45-60 min; herstartbaar — opnieuw draaien gaat verder
waar hij was) en zet het rapport-notebook klaar.

GEEN GPU nodig: dit is downloaden + CPU-rekenwerk.

Gebruik:  .\stappen\6-mutatiescan.ps1
Daarna:   open notebooks\mutaties_etten_leur.ipynb in VS Code,
          kies de .venv-kernel en klik "Run All" (rekent 5-15 min).
#>

Set-Location "$PSScriptRoot\.."

function Check {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Gestopt: de vorige stap gaf een fout." -ForegroundColor Red
        exit 1
    }
}

if (-not (Test-Path ".venv")) { py -m venv .venv; Check }
& .venv\Scripts\Activate.ps1
pip install -q -r requirements.txt
Check

$bbox = "101500,395000,107000,400000"   # heel Etten-Leur (5,5 x 5 km)

Write-Host "BAG ophalen voor heel Etten-Leur (~28.000 panden) ..." -ForegroundColor Cyan
python scripts\01_fetch_bag.py --bbox $bbox
Check

Write-Host "Luchtfoto 2022 downloaden (herstartbaar) ..." -ForegroundColor Cyan
python scripts\02_download_tiles.py --bbox $bbox --laag 2022_orthoHR --map-naam el_2022
Check

Write-Host "Luchtfoto 2025 downloaden (herstartbaar) ..." -ForegroundColor Cyan
python scripts\02_download_tiles.py --bbox $bbox --laag 2025_orthoHR --map-naam el_2025
Check

Write-Host ""
Write-Host "=== Data compleet ===" -ForegroundColor Green
Write-Host "Open notebooks\mutaties_etten_leur.ipynb in VS Code (.venv-kernel) en klik Run All."
Write-Host "Het rapport toont: nieuwbouw per jaar, de detectie-trechter (gedetecteerd ->"
Write-Host "verklaard door BAG -> onverklaard) en voor/na-galerijen met gele markering."
Write-Host ""
Write-Host "Let op: je pilot-annotatieflow (stap 1 t/m 5) blijft gewoon werken — de eerstvolgende"
Write-Host ".\stappen\1-voorbereiden.ps1 haalt automatisch weer de pilot-BAG op."
