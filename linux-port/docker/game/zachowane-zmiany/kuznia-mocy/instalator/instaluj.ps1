# Kuznia Mocy - instalator na PC (Windows + Docker Desktop).
# Uzycie: kliknij instaluj.bat albo:  powershell -ExecutionPolicy Bypass -File instaluj.ps1 [-Serwer "C:\sciezka\do\serwera"]
# Mozna uruchamiac wiele razy, np. po kazdej aktualizacji serwera - zaczyna od oryginalow autora.
param([string]$Serwer = "")
$ErrorActionPreference = "Stop"
$pkg = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-Serwer($p) { $p -and (Test-Path (Join-Path $p "linux-port\docker\docker-compose.yml")) }

if (-not (Test-Serwer $Serwer)) {
    foreach ($c in @((Split-Path $pkg -Parent), (Get-Location).Path, "C:\MT2009", "C:\metin2", "$env:USERPROFILE\Desktop\MT2009")) {
        if (Test-Serwer $c) { $Serwer = $c; break }
    }
}
if (-not (Test-Serwer $Serwer)) {
    Add-Type -AssemblyName System.Windows.Forms
    $d = New-Object System.Windows.Forms.FolderBrowserDialog
    $d.Description = "Wskaz folder serwera MT2009 (ten z folderem linux-port)"
    if ($d.ShowDialog() -eq "OK") { $Serwer = $d.SelectedPath }
}
if (-not (Test-Serwer $Serwer)) { Write-Host "Nie znaleziono serwera (brak linux-port\docker\docker-compose.yml)." -ForegroundColor Red; exit 2 }
docker info *> $null
if ($LASTEXITCODE -ne 0) { Write-Host "Docker Desktop nie dziala - uruchom go i sprobuj ponownie." -ForegroundColor Red; exit 2 }

$wersja = ""; if (Test-Path "$pkg\WERSJA") { $wersja = (Get-Content "$pkg\WERSJA" -Raw).Trim() }
Write-Host "==> Kuznia Mocy $wersja -> $Serwer" -ForegroundColor Cyan
New-Item -ItemType Directory -Force "$pkg\kopie" | Out-Null
docker run --rm -v "${Serwer}\linux-port:/srv" -v "${pkg}:/pkg:ro" -v "${pkg}\kopie:/kopie" python:3.12-slim sh /pkg/wewnatrz.sh
if ($LASTEXITCODE -ne 0) { Write-Host "Instalacja przerwana (opis wyzej). Serwer nie byl zmieniany poza plikami z kopii w folderze kopie." -ForegroundColor Red; exit $LASTEXITCODE }

Write-Host "==> Budowa gry i panelu (pierwszy raz kilkanascie minut)" -ForegroundColor Cyan
Push-Location "$Serwer\linux-port\docker"
try {
    docker compose build game seban-panel; if ($LASTEXITCODE -ne 0) { throw "budowa nie powiodla sie" }
    docker compose up -d; if ($LASTEXITCODE -ne 0) { throw "start nie powiodl sie" }
} finally { Pop-Location }
Write-Host ""
Write-Host "GOTOWE. Panel -> Kuznia Mocy. Dalej:" -ForegroundColor Green
Write-Host " 1) Kuznia Mocy: wszystkie systemy startuja od zera - ustaw je po swojemu."
Write-Host " 2) Przeglad -> Klient (ROOT): wgraj swoj root.index + root.data, pobierz gotowy ROOT i podmien w kliencie."
