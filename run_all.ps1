# run_all.ps1
# Windows PowerShell equivalent of run_all.sh
# ---------------------------------------------
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Python = ".\venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " 1/4  Generating sample dataset" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
& $Python data/generate_dataset.py

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " 2/4  Training proposed model (TF-IDF + LogReg)" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
& $Python src/sentiment_service/train_model.py

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " 3/4  Generating result charts" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
& $Python results/generate_results.py

Write-Host ""
Write-Host "==============================================" -ForegroundColor Cyan
Write-Host " 4/4  Traditional vs. Proposed comparison" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan
& $Python results/baseline_comparison.py

Write-Host ""
Write-Host "==============================================" -ForegroundColor Green
Write-Host " All pipeline steps completed successfully!" -ForegroundColor Green
Write-Host " Starting live microservices..." -ForegroundColor Green
Write-Host "==============================================" -ForegroundColor Green
& $Python run_services.py
