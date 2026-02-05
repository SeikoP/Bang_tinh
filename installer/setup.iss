; Inno Setup Script for Warehouse Management Application
; This script creates a professional Windows installer with proper configuration

#define MyAppName "Warehouse Management"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Bangla Team"
#define MyAppURL "https://github.com/bangla-team/warehouse-management"
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
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=..\LICENSE.txt
InfoBeforeFile=..\installer\info_before.txt
OutputDir=..\dist
OutputBaseFilename=WarehouseManagement-Setup-{#MyAppVersion}
SetupIconFile=..\assets\icon.png
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "vietnamese"; MessagesFile: "compiler:Languages\Vietnamese.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Main executable
Source: "..\dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; Assets directory
Source: "..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs

; Configuration template
Source: "..\.env.example"; DestDir: "{app}"; DestName: ".env"; Flags: onlyifdoesntexist confirmoverwrite

; Create necessary directories
Source: "..\exports\.gitkeep"; DestDir: "{app}\exports"; Flags: ignoreversion
Source: "..\logs\.gitkeep"; DestDir: "{app}\logs"; Flags: ignoreversion

; Documentation (if exists)
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist
Source: "..\LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion skipifsourcedoesntexist

[Icons]
; Start Menu shortcuts
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch shortcut (optional, for older Windows)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
; Option to launch application after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user data on uninstall (optional - commented out for safety)
; Type: filesandordirs; Name: "{app}\logs"
; Type: filesandordirs; Name: "{app}\exports"
; Type: files; Name: "{app}\storage.db"
; Type: files; Name: "{app}\.env"

[Code]
// Custom Pascal Script code for advanced installer behavior

function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // Check if .NET Framework or other prerequisites are needed
  // Add custom checks here if required
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Perform post-installation tasks
    // For example: create initial database, set permissions, etc.
  end;
end;

function InitializeUninstall(): Boolean;
var
  Response: Integer;
begin
  Result := True;
  
  // Ask user if they want to keep their data
  Response := MsgBox('Do you want to keep your database and configuration files?', 
                     mbConfirmation, MB_YESNO);
  
  if Response = IDYES then
  begin
    // Keep user data - don't delete database and config
    Result := True;
  end
  else
  begin
    // Delete all user data
    DelTree(ExpandConstant('{app}\storage.db'), False, True, False);
    DelTree(ExpandConstant('{app}\.env'), False, True, False);
    DelTree(ExpandConstant('{app}\logs'), True, True, True);
    DelTree(ExpandConstant('{app}\exports'), True, True, True);
    Result := True;
  end;
end;
