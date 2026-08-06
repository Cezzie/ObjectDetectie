<#
Stap 5 — wachten op de Kaggle-training en het model klaarzetten.

Volgt de trainingsstatus (elke minuut een check), downloadt na afloop de
output en zet best.pt in data\models\ met een automatisch opgehoogd
versienummer (bwb_daken_v1.pt, v2, ...). Stap 4 roept dit zelf al aan;
los draaien is handig als je eerder afbrak of later wilt ophalen.

Gebruik:  .\stappen\5-model-ophalen.ps1 [-NietWachten]
#>
param([switch]$NietWachten)

Set-Location "$PSScriptRoot\.."
if (Test-Path ".venv") { & .venv\Scripts\Activate.ps1 }

$slug = "jayscar/bwb-daken-training"

while ($true) {
    $status = (kaggle kernels status $slug 2>&1 | Out-String)
    if ($status -match '"?complete"?') {
        Write-Host "Training is klaar." -ForegroundColor Green
        break
    }
    if ($status -match '"?(error|cancelAcknowledged)"?') {
        Write-Host "Training is niet goed geëindigd:" -ForegroundColor Red
        Write-Host $status
        Write-Host "Bekijk de logs op https://www.kaggle.com/code/$slug"
        exit 1
    }
    if ($NietWachten) {
        Write-Host "Training draait nog. Kom later terug met .\stappen\5-model-ophalen.ps1"
        exit 0
    }
    Write-Host ("{0:HH:mm}  training draait nog, volgende check over 60 s ..." -f (Get-Date))
    Start-Sleep -Seconds 60
}

Write-Host "Output downloaden ..." -ForegroundColor Cyan
Remove-Item data\kaggle_output -Recurse -Force -ErrorAction SilentlyContinue
kaggle kernels output $slug -p data\kaggle_output
if ($LASTEXITCODE -ne 0) { Write-Host "Download mislukt." -ForegroundColor Red; exit 1 }

$best = Get-ChildItem data\kaggle_output -Recurse -Filter best.pt | Select-Object -First 1
if (-not $best) {
    Write-Host "Geen best.pt in de output gevonden — is de training wel tot een model gekomen?" -ForegroundColor Red
    exit 1
}

# Versienummer bepalen: hoogste bestaande bwb_daken_vN.pt + 1
New-Item -ItemType Directory -Force data\models > $null
$versies = Get-ChildItem data\models\bwb_daken_v*.pt -ErrorAction SilentlyContinue |
           ForEach-Object { if ($_.Name -match 'v(\d+)\.pt$') { [int]$Matches[1] } }
$volgende = 1
if ($versies) { $volgende = ($versies | Measure-Object -Maximum).Maximum + 1 }

$doel = "data\models\bwb_daken_v$volgende.pt"
Copy-Item $best.FullName $doel

Write-Host ""
Write-Host "=== Model klaargezet: $doel ===" -ForegroundColor Green
Write-Host "De volgende .\stappen\1-voorbereiden.ps1 pre-annoteert automatisch met dit model."
