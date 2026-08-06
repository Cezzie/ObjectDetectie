<#
Stap 4 — dataset bouwen, uploaden en trainen op Kaggle.

Doet: dataset verversen (met je nieuwste annotaties), uploaden naar Kaggle,
training starten op GPU, wachten tot hij klaar is en het model klaarzetten
in data\models\ (via stap 5).

Gebruik:  .\stappen\4-trainen.ps1 [-NietWachten]
#>
param([switch]$NietWachten)

Set-Location "$PSScriptRoot\.."

& .\start.ps1 -Trainen
if ($LASTEXITCODE -ne 0) { exit 1 }

if ($NietWachten) {
    Write-Host "Niet gewacht op de training. Straks ophalen:  .\stappen\5-model-ophalen.ps1"
    exit 0
}
& "$PSScriptRoot\5-model-ophalen.ps1"
