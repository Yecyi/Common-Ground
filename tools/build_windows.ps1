# Rebuild the portable Windows app after editing the source.
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw 'Create the project .venv first. See README.md.'
}
Push-Location -LiteralPath $projectRoot
try {
    & $pythonExe -m pip install pyinstaller==6.20.0
    if ($LASTEXITCODE -ne 0) { throw 'Could not install the build dependency.' }
    $assetDir = Join-Path $projectRoot 'assets'
    $iconFile = Join-Path $assetDir 'icon.ico'
    & $pythonExe -m PyInstaller --noconfirm --onefile --windowed --name 'Common Ground' --icon $iconFile --add-data "$assetDir;assets" --distpath '.' --workpath 'work/build' --specpath 'work' --collect-submodules tools main.py
    if ($LASTEXITCODE -ne 0) { throw 'The build did not finish.' }
} finally {
    Pop-Location
}
