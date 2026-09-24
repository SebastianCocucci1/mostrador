; Instalador de Windows (Inno Setup 6: https://jrsoftware.org/isinfo.php).
; Primero construir.bat arma dist\Mostrador\; despues abrir este archivo en
; Inno Setup y "Compile" (o: iscc empaquetar\instalador.iss).
; Sale en dist\Mostrador-<version>-instalador.exe

#define Nombre "Mostrador"
#define Version "1.0.0"
#define Editor "Mostrador"

[Setup]
; Este AppId identifica a la app para las actualizaciones: no cambiarlo nunca.
AppId={{6F1C2B7E-3D4A-4E8B-9C2F-5A7D1E0B3C94}
AppName={#Nombre}
AppVersion={#Version}
AppPublisher={#Editor}
DefaultDirName={autopf}\{#Nombre}
DefaultGroupName={#Nombre}
UninstallDisplayIcon={app}\{#Nombre}.exe
OutputDir=..\dist
OutputBaseFilename={#Nombre}-{#Version}-instalador
SetupIconFile=icono.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\{#Nombre}\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#Nombre}"; Filename: "{app}\{#Nombre}.exe"
Name: "{autodesktop}\{#Nombre}"; Filename: "{app}\{#Nombre}.exe"; Tasks: escritorio

[Run]
Filename: "{app}\{#Nombre}.exe"; Description: "Abrir {#Nombre}"; Flags: nowait postinstall skipifsilent
