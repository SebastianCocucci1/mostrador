# PyInstaller: arma dist/Mostrador/Mostrador.exe (una carpeta, arranca rapido).
#     pyinstaller empaquetar/mostrador.spec --noconfirm
# Lo corre solo construir.bat.

from pathlib import Path

RAIZ = Path(SPECPATH).parent

a = Analysis(
    [str(RAIZ / "main.py")],
    pathex=[str(RAIZ)],
    datas=[(str(RAIZ / "web"), "web")],
    hiddenimports=["webview.platforms.winforms", "webview.platforms.edgechromium", "clr"],
    excludes=["tkinter", "pytest", "matplotlib", "numpy", "pandas", "IPython"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="Mostrador",
    icon=str(RAIZ / "empaquetar" / "icono.ico"),
    console=False,
    version=str(RAIZ / "empaquetar" / "version.txt"),
)
coll = COLLECT(exe, a.binaries, a.datas, name="Mostrador")
