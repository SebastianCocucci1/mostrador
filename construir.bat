@echo off
rem Arma dist\Mostrador\Mostrador.exe listo para repartir.
rem Despues, para el instalador: abrir empaquetar\instalador.iss con Inno Setup.
cd /d "%~dp0"
python -m pip install -r requirements.txt -r requirements-dev.txt || goto :error
python -m pytest -q tests || goto :error
python empaquetar\hacer_icono.py || goto :error
python -m PyInstaller empaquetar\mostrador.spec --noconfirm --clean --distpath dist --workpath build || goto :error
echo.
echo Listo: dist\Mostrador\Mostrador.exe
pause
exit /b 0
:error
echo.
echo Algo fallo (mira el mensaje de arriba).
pause
exit /b 1
