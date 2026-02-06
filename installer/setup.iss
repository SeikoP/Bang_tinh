; Inno Setup Script for Warehouse Management Application
; This script creates a professional Windows installer with proper configuration

#define MyAppName "Bảng Tính"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Bangla Team"
#define MyAppURL "https://github.com/SeikoP/Bang_tinh"
#define MyAppExeName "Warehouse Management.exe"

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
DefaultDirName={autopf}\BangTinh
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt
InfoBeforeFile=info_before.txt
OutputDir=..\Output
OutputBaseFilename=BangTinhSetup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableProgramGroupPage=yes

[Languages]
Name: "vietnamese"; MessagesFile: "compiler:Languages\Vietnamese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; Main executable from PyInstaller output
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Assets directory
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Configuration template
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist

; Create necessary directories
Source: "..\exports\.gitkeep"; DestDir: "{app}\exports"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\logs\.gitkeep"; DestDir: "{app}\logs"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Gỡ cài đặt {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Option to launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "Khởi chạy {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up logs on uninstall
Type: filesandordirs; Name: "{app}\logs"

[Code]
function InitializeUninstall(): Boolean;
var
  Response: Integer;
begin
  Result := True;
  
  // Ask user if they want to keep their data
  Response := MsgBox('Bạn có muốn giữ lại dữ liệu và cấu hình không?', 
                     mbConfirmation, MB_YESNO);
  
  if Response = IDNO then
  begin
    // Delete all user data
    DelTree(ExpandConstant('{app}\storage.db'), False, True, False);
    DelTree(ExpandConstant('{app}\.env'), False, True, False);
    DelTree(ExpandConstant('{app}\exports'), True, True, True);
  end;
end;
