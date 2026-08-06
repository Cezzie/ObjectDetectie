<#
Startscript voor de ObjectDetectie-pipeline (Windows/PowerShell).

Gebruik:
  .\start.ps1              data genereren + annotatieronde klaarzetten
  .\start.ps1 -Aantal 200  idem, met een grotere annotatieronde (standaard 100)
  .\start.ps1 -Labelen     Label Studio starten (installeert zo nodig)
  .\start.ps1 -Trainen     dataset bouwen, naar Kaggle uploaden en training starten

Alle stappen zijn herstartbaar: wat al gedaan is wordt overgeslagen of gemeld,
en handmatige annotaties worden nooit overschreven. Dit script kun je dus
altijd gewoon opnieuw draaien.
#>
param(
    [switch]$Trainen,
    [switch]$Labelen,
    [int]$Aantal = 100
)

Set-Location $PSScriptRoot

function Check {
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Gestopt: de vorige stap gaf een fout." -ForegroundColor Red
        exit 1
    }
}

# --- Omgeving ---
if (-not (Test-Path ".venv")) {
    Write-Host "Venv aanmaken ..." -ForegroundColor Cyan
    py -m venv .venv
    Check
}
& .venv\Scripts\Activate.ps1
pip install -q -r requirements.txt
Check

if ($Labelen) {
    if (-not (Get-Command label-studio -ErrorAction SilentlyContinue)) {
        Write-Host "Label Studio installeren (eenmalig, kan enkele minuten duren) ..." -ForegroundColor Cyan
        pip install -q label-studio
        Check
    }
    $env:LABEL_STUDIO_LOCAL_FILES_SERVING_ENABLED = "true"
    $env:LABEL_STUDIO_LOCAL_FILES_DOCUMENT_ROOT = "$PSScriptRoot\data\tiles"
    Write-Host ""
    Write-Host "=== Label Studio start op http://localhost:8080 (stoppen: Ctrl+C) ===" -ForegroundColor Green
    Write-Host "Eerste keer? Projectinrichting (eenmalig):"
    Write-Host "  1. Account aanmaken -> Create Project"
    Write-Host "  2. Settings -> Labeling Interface -> Code -> plak data\labelstudio\labeling_config.xml"
    Write-Host "  3. Settings -> Cloud Storage -> Add Source Storage -> Local files"
    Write-Host "     pad: $PSScriptRoot\data\tiles\images  (niet syncen)"
    Write-Host "Elke ronde: Import -> data\labelstudio\tasks.json -> annoteren -> Export -> JSON"
    Write-Host ""
    label-studio start
    exit 0
}

if ($Trainen) {
    # --- Dataset bouwen en naar Kaggle ---
    python scripts\04_build_dataset.py
    Check
    Write-Host "Dataset uploaden naar Kaggle ..." -ForegroundColor Cyan
    kaggle datasets version -p data\kaggle_upload\bwb_daken_v1 -m ("update " + (Get-Date -Format "yyyy-MM-dd HH:mm"))
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Versie-update lukte niet — dataset bestaat waarschijnlijk nog niet, aanmaken ..." -ForegroundColor Yellow
        kaggle datasets create -p data\kaggle_upload\bwb_daken_v1
        Check
    }
    Write-Host "Training starten op Kaggle (GPU) ..." -ForegroundColor Cyan
    kaggle kernels push -p notebooks
    Check
    Write-Host ""
    Write-Host "=== Training draait op Kaggle ===" -ForegroundColor Green
    Write-Host "Voortgang:     kaggle kernels status jayscar/bwb-daken-training"
    Write-Host "Model ophalen: kaggle kernels output jayscar/bwb-daken-training -p data\kaggle_output"
    Write-Host "Klaarzetten:   Copy-Item data\kaggle_output\runs\bwb_daken\weights\best.pt data\models\bwb_daken_vX.pt"
    exit 0
}

# --- Data genereren (herstartbaar) ---
python scripts\01_fetch_bag.py
Check
python scripts\02_download_tiles.py
Check
python scripts\03_make_labels.py
Check
python scripts\05_preview.py --aantal 4
Check

# --- Annotatieronde klaarzetten; nieuwste model pre-annoteert als het er is ---
$model = Get-ChildItem data\models\*.pt -ErrorAction SilentlyContinue |
         Sort-Object LastWriteTime | Select-Object -Last 1
if ($model) {
    Write-Host "Pre-annotatie met model: $($model.Name)" -ForegroundColor Cyan
    python scripts\06_export_labelstudio.py --aantal $Aantal --model $model.FullName
} else {
    python scripts\06_export_labelstudio.py --aantal $Aantal
}
Check

Write-Host ""
Write-Host "=== Klaar voor annotatie — volgende stappen ===" -ForegroundColor Green
Write-Host "1. Controleer data\preview\ (liggen de boxen op de daken?)"
Write-Host "2. Start Label Studio:  .\start.ps1 -Labelen"
Write-Host "3. Importeer data\labelstudio\tasks.json in je project en annoteer"
Write-Host "4. Export -> JSON, dan: python scripts\07_import_labelstudio.py <export.json>"
Write-Host "5. Daarna: .\start.ps1 -Trainen"
