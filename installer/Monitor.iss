#define MyAppName "Monitor"
#define MyAppVersion "3.0.0"
#define MyAppExeName "Monitor.App.exe"
#define MyAppPublisher "Monitor"
#define MyAppId "{{6D493EE4-3168-4F2A-8C0B-A761D171B91D}}"
#define PublishDir "..\artifacts\publish\Monitor"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Monitor
DefaultGroupName=Monitor
DisableProgramGroupPage=yes
OutputDir=..\artifacts\installer
OutputBaseFilename=Monitor-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=..\src\Monitor.App\Assets\monitor-icon.ico
SetupLogging=yes

[Languages]
Name: "chinesesimp"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; Flags: checkedonce
Name: "startup"; Description: "开机自动启动"; Flags: unchecked
Name: "resetdata"; Description: "清空旧数据后安装（会删除本机现有记录）"; Flags: unchecked

[Dirs]
Name: "{commonappdata}\Monitor"; Permissions: users-modify
Name: "{commonappdata}\Monitor\backups"; Permissions: users-modify
Name: "{commonappdata}\Monitor\logs"; Permissions: users-modify

[Files]
Source: "{#PublishDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Monitor"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Monitor"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{commonstartup}\Monitor"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 Monitor"; Flags: nowait postinstall skipifsilent

[Code]
var
  RemoveDataOnUninstall: Boolean;

function GetDataDir(): String;
begin
  Result := ExpandConstant('{commonappdata}\Monitor');
end;

function IsWebView2RuntimeInstalled(): Boolean;
var
  Version: String;
begin
  Result :=
    RegQueryStringValue(HKLM, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) or
    RegQueryStringValue(HKLM32, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version) or
    RegQueryStringValue(HKCU, 'SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}', 'pv', Version);
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsWebView2RuntimeInstalled() then
  begin
    MsgBox(
      '未检测到 Microsoft Edge WebView2 Runtime。' + #13#10 +
      '请先安装 WebView2 Runtime，再重新运行安装程序。',
      mbError,
      MB_OK
    );
    Result := False;
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
var
  ConfirmResult: Integer;
begin
  Result := True;

  if (CurPageID = wpSelectTasks) and WizardIsTaskSelected('resetdata') and DirExists(GetDataDir()) then
  begin
    ConfirmResult := MsgBox(
      '将删除本机已有数据，包括历史记录、配置和备份。' + #13#10 +
      '确认继续安装吗？',
      mbConfirmation,
      MB_YESNO
    );

    if ConfirmResult <> IDYES then
      Result := False;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssInstall) and WizardIsTaskSelected('resetdata') and DirExists(GetDataDir()) then
    DelTree(GetDataDir(), True, True, True);
end;

function InitializeUninstall(): Boolean;
var
  ConfirmResult: Integer;
begin
  Result := True;
  RemoveDataOnUninstall := False;

  if DirExists(GetDataDir()) then
  begin
    ConfirmResult := MsgBox(
      '是否同时删除本机数据？' + #13#10 +
      '这会删除历史记录、配置和备份，且无法恢复。',
      mbConfirmation,
      MB_YESNO
    );

    RemoveDataOnUninstall := ConfirmResult = IDYES;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if (CurUninstallStep = usPostUninstall) and RemoveDataOnUninstall and DirExists(GetDataDir()) then
    DelTree(GetDataDir(), True, True, True);
end;
