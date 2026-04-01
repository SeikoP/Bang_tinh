; Inno Setup Script for WMS
; This script creates a professional Windows installer with proper configuration

#define MyAppName "WMS"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "WAREHOUSE"
#define MyAppURL "https://github.com/SeikoP/Bang_tinh"
#define MyAppExeName "WarehouseManagement.exe"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
AppId={{A5B3C7D9-E1F2-4A5B-8C9D-0E1F2A3B4C5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\WMS
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\..\LICENSE.txt
InfoBeforeFile=info_before.txt
OutputDir=..\..\Output
OutputBaseFilename=BangTinhSetup
Compression=lzma2/ultra64
SolidCompression=yes
SetupIconFile=..\..\src\wms\assets\icons\icon.ico
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Main executable from PyInstaller output
Source: "..\..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Assets directory
Source: "..\..\src\wms\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Configuration template
Source: "..\..\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist skipifsourcedoesntexist

; Create necessary directories
Source: "..\..\data\exports\.gitkeep"; DestDir: "{app}\exports"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\..\data\logs\.gitkeep"; DestDir: "{app}\logs"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\icon.ico"
Name: "{group}\Gỡ cài đặt {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\icon.ico"; Tasks: desktopicon

[Run]
; Add Windows Firewall rules so the notification server can receive connections
; TCP 5005 — HTTP notification server (Android → Desktop)
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""WMS - Notification Server (TCP 5005)"" dir=in action=allow protocol=TCP localport=5005 profile=any"; Flags: runhidden; StatusMsg: "Mở cổng tường lửa 5005 (TCP)..."
; UDP 5006 — Auto-discovery broadcast
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall add rule name=""WMS - Discovery Server (UDP 5006)"" dir=in action=allow protocol=UDP localport=5006 profile=any"; Flags: runhidden; StatusMsg: "Mở cổng tường lửa 5006 (UDP)..."

; Option to launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "Khởi chạy {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove firewall rules on uninstall
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""WMS - Notification Server (TCP 5005)"""; Flags: runhidden
Filename: "{sys}\netsh.exe"; Parameters: "advfirewall firewall delete rule name=""WMS - Discovery Server (UDP 5006)"""; Flags: runhidden

[UninstallDelete]
; Clean up logs on uninstall
Type: filesandordirs; Name: "{app}\logs"

[Code]
function InitializeUninstall(): Boolean;
var
  Response: Integer;
  DataDir: String;
begin
  Result := True;

  if UninstallSilent then
    Exit;
  
  // Ask user if they want to keep their data
  Response := MsgBox('Bạn có muốn giữ lại dữ liệu và cấu hình không?', 
                     mbConfirmation, MB_YESNO);
  
  if Response = IDNO then
  begin
    // Delete runtime data stored outside Program Files
    DataDir := ExpandConstant('{localappdata}\WMS');
    DelTree(DataDir, True, True, True);

    // Delete local configuration shipped with the installer
    DeleteFile(ExpandConstant('{app}\.env'));
    DelTree(ExpandConstant('{app}\exports'), True, True, True);
  end;
end;
