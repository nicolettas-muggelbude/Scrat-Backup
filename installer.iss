; Inno Setup Script für Scrat-Backup
; Erstellt einen professionellen Windows-Installer
;
; Voraussetzungen:
; 1. Inno Setup 6.x installiert (https://jrsoftware.org/isinfo.php)
; 2. PyInstaller Build erfolgreich abgeschlossen (dist/ScratBackup/)
;
; Verwendung:
; 1. Öffne dieses Script in Inno Setup Compiler
; 2. Klicke auf "Compile" oder drücke F9
; 3. Installer wird in Output/ erstellt

#define MyAppName "Scrat-Backup"
#define MyAppVersion "0.2.1-beta"
#define MyAppPublisher "Scrat-Backup Project"
#define MyAppURL "https://github.com/nicolettas-muggelbude/Scrat-Backup"
#define MyAppExeName "ScratBackup.exe"
#define MyAppIconName "scrat.ico"

[Setup]
; Basis-Informationen
AppId={{8F7D4A2B-5C9E-4F1B-A3D6-7E8C9B0A1F2D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE
InfoBeforeFile=docs\INSTALL.txt
OutputDir=output
OutputBaseFilename=ScratBackup-{#MyAppVersion}-Setup
SetupIconFile=assets\icons\{#MyAppIconName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Visual Style
WizardImageFile=compiler:WizModernImage-IS.bmp
WizardSmallImageFile=compiler:WizModernSmallImage-IS.bmp

; Uninstall-Informationen
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Haupt-Executable
Source: "dist\ScratBackup\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Alle Dateien aus dem PyInstaller Build-Ordner
Source: "dist\ScratBackup\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Dokumentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

; User Guide (falls vorhanden)
Source: "docs\USER_GUIDE.md"; DestDir: "{app}\docs"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Startmenü
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{#MyAppURL}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch (optional, nur alte Windows-Versionen)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Nach Installation Optionen
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Custom Code für erweiterte Installationslogik

// Prüfe ob alte Version installiert ist
function GetUninstallString(): String;
var
  sUnInstPath: String;
  sUnInstallString: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\{#emit SetupSetting("AppId")}_is1');
  sUnInstallString := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', sUnInstallString) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', sUnInstallString);
  Result := sUnInstallString;
end;

// Prüfe ob Deinstallation notwendig ist
function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

// Deinstalliere alte Version
function UnInstallOldVersion(): Integer;
var
  sUnInstallString: String;
  iResultCode: Integer;
begin
  Result := 0;
  sUnInstallString := GetUninstallString();
  if sUnInstallString <> '' then begin
    sUnInstallString := RemoveQuotes(sUnInstallString);
    if Exec(sUnInstallString, '/SILENT /NORESTART /SUPPRESSMSGBOXES','', SW_HIDE, ewWaitUntilTerminated, iResultCode) then
      Result := 3
    else
      Result := 2;
  end else
    Result := 1;
end;

// Vor der Installation
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep=ssInstall) then
  begin
    if (IsUpgrade()) then
    begin
      UnInstallOldVersion();
    end;
  end;
end;

// Initialisierung
function InitializeSetup(): Boolean;
begin
  Result := True;
end;

[UninstallDelete]
; Lösche Benutzer-Konfiguration (optional, auskommentiert für Sicherheit)
; Type: filesandordirs; Name: "{userappdata}\scrat-backup"

[Registry]
; Füge Registry-Einträge hinzu (z.B. für File-Associations)
; Beispiel: Backup-Dateien mit Scrat-Backup öffnen
; Root: HKCR; Subkey: ".scbak"; ValueType: string; ValueName: ""; ValueData: "ScratBackupFile"; Flags: uninsdeletevalue
; Root: HKCR; Subkey: "ScratBackupFile"; ValueType: string; ValueName: ""; ValueData: "Scrat-Backup File"; Flags: uninsdeletekey
; Root: HKCR; Subkey: "ScratBackupFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
; Root: HKCR; Subkey: "ScratBackupFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Messages]
; Deutsche Meldungen
german.WelcomeLabel2=Dieses Programm wird [name/ver] auf deinem Computer installieren.%n%n🐿️ Wie ein Eichhörnchen seine Eicheln bewahrt, so bewahren wir deine Daten.%n%nEs wird empfohlen, alle anderen Anwendungen zu schließen, bevor du mit dem Setup fortfährst.
german.FinishedHeadingLabel=Installation von [name] abgeschlossen
german.FinishedLabelNoIcons=Die Installation von [name] wurde abgeschlossen.
german.FinishedLabel=Die Installation von [name] wurde abgeschlossen. Du kannst die Anwendung jetzt starten.

; Englische Meldungen
english.WelcomeLabel2=This will install [name/ver] on your computer.%n%n🐿️ Just as a squirrel preserves its acorns, we preserve your data.%n%nIt is recommended that you close all other applications before continuing.
english.FinishedHeadingLabel=[name] installation completed
english.FinishedLabelNoIcons=[name] installation has been completed.
english.FinishedLabel=[name] installation has been completed. You can now launch the application.
