<#
Stap 3 — je Label Studio-annotaties terugzetten in de pipeline.

Zoekt automatisch de nieuwste Label Studio-export (project-*.json) in je
Downloads-map en verwerkt die met scripts\07_import_labelstudio.py.
Geannoteerde tegels zijn daarna beschermd en verschijnen niet opnieuw
in volgende annotatierondes.

Gebruik:  .\stappen\3-annotaties-importeren.ps1 [-Bestand C:\pad\export.json]
#>
param([string]$Bestand)

Set-Location "$PSScriptRoot\.."

function Check {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Gestopt: de vorige stap gaf een fout." -ForegroundColor Red
        exit 1
    }
}

& .venv\Scripts\Activate.ps1

if (-not $Bestand) {
    $kandidaat = Get-ChildItem "$env:USERPROFILE\Downloads\project-*.json" -ErrorAction SilentlyContinue |
                 Sort-Object LastWriteTime | Select-Object -Last 1
    if (-not $kandidaat) {
        Write-Host "Geen Label Studio-export (project-*.json) gevonden in je Downloads." -ForegroundColor Yellow
        Write-Host "Exporteer in Label Studio als JSON, of geef het pad mee:"
        Write-Host "  .\stappen\3-annotaties-importeren.ps1 -Bestand C:\pad\naar\export.json"
        exit 1
    }
    Write-Host "Gevonden export: $($kandidaat.Name)  (van $($kandidaat.LastWriteTime))"
    $antwoord = Read-Host "Deze importeren? (j/n)"
    if ($antwoord -ne "j") { exit 0 }
    $Bestand = $kandidaat.FullName
}

python scripts\07_import_labelstudio.py $Bestand
Check

Write-Host ""
Write-Host "Volgende stap:  .\stappen\4-trainen.ps1" -ForegroundColor Green
