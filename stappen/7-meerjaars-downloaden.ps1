<#
Stap 7 — extra jaargangen downloaden voor de meerjaars-consistentiescan.

Vult de bestaande el_2022 en el_2025 aan met 2023 en 2024 (zelfde grid, heel
Etten-Leur), zodat notebooks\mutaties_meerjaars.ipynb vier opeenvolgende
jaarparen kan vergelijken en mutaties kan dateren.

± 1 GB extra schijf, ± 45-60 min; volledig herstartbaar. GEEN GPU nodig.

Gebruik:  .\stappen\7-meerjaars-downloaden.ps1
Daarna:   open notebooks\mutaties_meerjaars.ipynb (.venv-kernel) -> Run All
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

$bbox = "101500,395000,107000,400000"   # heel Etten-Leur — zelfde grid als el_2022/el_2025

foreach ($jaar in 2023, 2024) {
    Write-Host "Luchtfoto $jaar downloaden (herstartbaar) ..." -ForegroundColor Cyan
    python scripts\02_download_tiles.py --bbox $bbox --laag "${jaar}_orthoHR" --map-naam "el_$jaar"
    Check
}

Write-Host ""
Write-Host "=== Vier jaargangen compleet (2022 t/m 2025) ===" -ForegroundColor Green
Write-Host "Open notebooks\mutaties_meerjaars.ipynb (.venv-kernel) en klik Run All."
Write-Host "Reken op 15-30 min (4 jaarparen scoren, met voortgangsbalk)."
