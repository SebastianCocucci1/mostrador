# Prueba de punta a punta en Windows del paquete armado en dist\:
#   1. El programa arranca con el Python oficial (pythonw.exe) y responde.
#   2. La primera vez crea el acceso directo del escritorio.
#   3. Ante una version nueva (GitHub falso) que ademas pide OTRAS librerias:
#      baja el codigo y las librerias, reemplaza app\, se reinicia, el arranque
#      nuevo cambia lib\ (que el proceso viejo tenia "en uso") y vuelve a responder.
$ErrorActionPreference = 'Stop'

$base = if ($env:RUNNER_TEMP) { $env:RUNNER_TEMP } else { [IO.Path]::GetTempPath() }
$dir = Join-Path $base 'prueba_instalacion'
$datos = Join-Path $base 'prueba_datos'
foreach ($d in $dir, $datos) { if (Test-Path $d) { Remove-Item -Recurse -Force $d } }
Copy-Item -Recurse dist\Mostrador $dir

# Que parezca una instalacion vieja con otras librerias: asi la actualizacion las tiene que bajar
Set-Content (Join-Path $dir 'lib\lib.txt') 'librerias-viejas' -Encoding ascii -NoNewline

$logFalso = Join-Path $base 'github_falso.log'
if (Test-Path $logFalso) { Remove-Item $logFalso }
$falso = Start-Process python -ArgumentList 'tests\servidor_releases_falso.py', 'dist\Mostrador-app.zip', 'dist\Mostrador-lib.zip', '8765', $logFalso -WindowStyle Hidden -PassThru
Start-Sleep 2

$env:MOSTRADOR_DATOS = $datos
$env:MOSTRADOR_PUERTO = '8099'
$env:MOSTRADOR_URL_RELEASES = 'http://127.0.0.1:8765/releases/latest'
Start-Process (Join-Path $dir 'python\pythonw.exe') -ArgumentList "`"$(Join-Path $dir 'app\Mostrador.pyw')`"", '--no-abrir' -WorkingDirectory $dir

$ok = $false
for ($i = 0; $i -lt 90; $i++) {
    Start-Sleep 2
    try {
        $p = Invoke-RestMethod 'http://127.0.0.1:8099/ping' -TimeoutSec 3
        $pedidos = if (Test-Path $logFalso) { Get-Content $logFalso } else { @() }
        $app = @($pedidos | Where-Object { $_ -eq '/app' }).Count
        $lib = @($pedidos | Where-Object { $_ -eq '/lib' }).Count
        $consultas = @($pedidos | Where-Object { $_ -eq '/releases/latest' }).Count
        Write-Output "intento $i : version=$($p.version) estado=$($p.actualizacion) consultas=$consultas app=$app lib=$lib"
        if ($app -eq 1 -and $lib -eq 1 -and $consultas -ge 2 -and $p.actualizacion -eq 'al_dia') { $ok = $true; break }
    } catch {
        Write-Output "intento $i : el programa no responde (puede estar reiniciando)"
    }
}

$lnk = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Mostrador.lnk'
$hayAcceso = Test-Path $lnk
$huellaApp = (Get-Content (Join-Path $dir 'app\lib.txt') -Raw).Trim()
$huellaLib = (Get-Content (Join-Path $dir 'lib\lib.txt') -Raw).Trim()

Start-Sleep 3
Get-ChildItem $dir | Format-Table Name, Mode | Out-String | Write-Output
$registro = Join-Path $datos 'mostrador.log'
if (Test-Path $registro) { Get-Content $registro -Encoding utf8 | Write-Output }

# solo la copia de prueba (en una PC de verdad puede haber otros programas con pythonw)
Get-Process pythonw -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$dir*" } | Stop-Process -Force
Stop-Process -Id $falso.Id -Force -ErrorAction SilentlyContinue
if (-not $ok) { throw 'La actualizacion automatica no funciono' }
if ($huellaLib -ne $huellaApp) { throw "No se pusieron las librerias nuevas (lib: $huellaLib, app: $huellaApp)" }
if (Test-Path (Join-Path $dir 'lib.new')) { throw 'Quedo lib.new sin poner en su lugar' }
if (-not $hayAcceso) { throw 'No se creo el acceso directo en el escritorio' }
if (-not (Test-Path (Join-Path $dir 'app\Mostrador.pyw'))) { throw 'Falta app\Mostrador.pyw despues de actualizar' }
if (Test-Path (Join-Path $dir 'app.old')) { Write-Warning 'Quedo app.old (se borra en el proximo arranque)' }
Write-Output 'Instalacion, acceso directo y actualizacion automatica (codigo + librerias) OK'
