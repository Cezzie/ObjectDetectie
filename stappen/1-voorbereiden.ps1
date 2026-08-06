<#
Stap 1 — alles klaarzetten voor een annotatieronde.

Doet: git pull, venv + afhankelijkheden, data genereren (BAG + tegels + labels),
previews, en de annotatieronde exporteren. Is er al een getraind model in
data\models\, dan tekent dat automatisch voor.

Gebruik:  .\stappen\1-voorbereiden.ps1 [-Aantal 200]
#>
param([int]$Aantal = 100)

Set-Location "$PSScriptRoot\.."

git pull
if ($LASTEXITCODE -ne 0) {
    Write-Host "Let op: git pull lukte niet (offline?). We gaan door met de huidige versie." -ForegroundColor Yellow
}

& .\start.ps1 -Aantal $Aantal
