# Arma el paquete de Mostrador para Windows, sin .exe propio:
#
#   dist\Mostrador\
#     Abrir Mostrador.cmd   abre el programa (la primera vez crea los accesos directos)
#     LEEME.txt
#     python\               Python oficial embebido (pythonw.exe firmado por la PSF)
#     lib\                  librerias (Flask, pdfplumber, Pillow...)
#     app\                  codigo del programa
#
#   dist\Mostrador.zip                  todo, para la primera instalacion
#   dist\Mostrador-app.zip (+ .sha256)  solo app\: lo que baja el actualizador cada vez
#   dist\Mostrador-lib.zip (+ .sha256)  solo lib\: lo baja si cambiaron las librerias
#
# app\lib.txt y lib\lib.txt tienen la huella de requirements.txt: el
# actualizador compara las dos para saber si tiene que bajar lib tambien.
#
# Uso (con el mismo Python 3.12 que el embebido, para que las librerias compiladas sirvan):
#   ./scripts/armar_paquete.ps1 -PythonVersion 3.12.10
param([string]$PythonVersion = '3.12.10')
$ErrorActionPreference = 'Stop'

$dist = Join-Path (Get-Location) 'dist'
if (Test-Path $dist) { Remove-Item -Recurse -Force $dist }
$raiz = Join-Path $dist 'Mostrador'
$python = Join-Path $raiz 'python'
$lib = Join-Path $raiz 'lib'
$app = Join-Path $raiz 'app'
New-Item -ItemType Directory -Force $python, $lib, $app | Out-Null

# --- Python oficial embebido ---------------------------------------------------
$zipPython = Join-Path ([IO.Path]::GetTempPath()) "python-$PythonVersion-embed-amd64.zip"
Invoke-WebRequest "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip" -OutFile $zipPython
Expand-Archive $zipPython $python

foreach ($exe in 'python.exe', 'pythonw.exe') {
    $firma = Get-AuthenticodeSignature (Join-Path $python $exe)
    if ($firma.Status -ne 'Valid' -or $firma.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
        throw "$exe no tiene una firma valida de la Python Software Foundation ($($firma.Status))"
    }
    Write-Output "$exe firmado por: $($firma.SignerCertificate.Subject)"
}

# El Python embebido solo busca modulos donde dice su archivo ._pth: se agregan app y lib
$pth = Get-ChildItem $python -Filter 'python*._pth' | Select-Object -First 1
Add-Content $pth.FullName "`r`n..\app`r`n..\lib" -Encoding ascii

# --- Librerias -----------------------------------------------------------------------
$v = (python -c "import sys; print('%d.%d' % sys.version_info[:2])").Trim()
$vEmbebido = ($PythonVersion -split '\.')[0..1] -join '.'
if ($v -ne $vEmbebido) { throw "Las librerias se arman con Python $v pero el embebido es $vEmbebido" }
python -m pip install --disable-pip-version-check --no-compile --only-binary=:all: --target $lib -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las librerias' }
# pip deja lanzadores .exe (flask.exe...) que no se usan y ponen nerviosos a los antivirus
if (Test-Path (Join-Path $lib 'bin')) { Remove-Item -Recurse -Force (Join-Path $lib 'bin') }
Get-ChildItem $lib -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force

# Huella de las librerias: las lineas de requirements.txt (sin comentarios)
$lineas = Get-Content requirements.txt | ForEach-Object { $_.Trim() } | Where-Object { $_ -and -not $_.StartsWith('#') }
$bytes = [Text.Encoding]::UTF8.GetBytes(($lineas -join "`n"))
$huella = -join ([Security.Cryptography.SHA256]::Create().ComputeHash($bytes) | ForEach-Object { $_.ToString('x2') })
[IO.File]::WriteAllText((Join-Path $lib 'lib.txt'), $huella, [Text.Encoding]::ASCII)

# --- Codigo ------------------------------------------------------------------------
Copy-Item Mostrador.pyw $app
foreach ($c in 'mostrador', 'web', 'recursos') { Copy-Item -Recurse $c (Join-Path $app $c) }
Get-ChildItem $app -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
[IO.File]::WriteAllText((Join-Path $app 'lib.txt'), $huella, [Text.Encoding]::ASCII)

# --- Lanzador y LEEME ----------------------------------------------------------------
$lanzador = "@echo off`r`nstart `"`" `"%~dp0python\pythonw.exe`" `"%~dp0app\Mostrador.pyw`"`r`n"
[IO.File]::WriteAllText((Join-Path $raiz 'Abrir Mostrador.cmd'), $lanzador, [Text.Encoding]::ASCII)
Copy-Item recursos\LEEME.txt $raiz

# --- Zips ----------------------------------------------------------------------------
function Zip-ConSha($carpeta, $nombre) {
    $zip = Join-Path $dist $nombre
    python scripts/comprimir.py $carpeta $zip
    if ($LASTEXITCODE -ne 0) { throw "No se pudo armar $nombre" }
    $hash = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
    [IO.File]::WriteAllText("$zip.sha256", "$hash  $nombre", [Text.Encoding]::ASCII)
    Write-Output "SHA-256 de ${nombre}: $hash"
}
Zip-ConSha $app 'Mostrador-app.zip'
Zip-ConSha $lib 'Mostrador-lib.zip'
python scripts/comprimir.py $raiz (Join-Path $dist 'Mostrador.zip') --incluir-carpeta
if ($LASTEXITCODE -ne 0) { throw 'No se pudo armar el zip completo' }

Get-ChildItem $dist -File | Format-Table Name, Length | Out-String | Write-Output
Write-Output "Huella de las librerias: $huella"
