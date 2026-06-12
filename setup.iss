[Setup]
AppName=Vertical
AppVersion=1.0

DefaultDirName={autopf}\Vertical
DefaultGroupName=Vertical

OutputDir=output
OutputBaseFilename=VerticalSetup

Compression=lzma
SolidCompression=yes

PrivilegesRequired=admin

[Files]

Source: "dist\Vertical\*"; \
DestDir: "{app}"; \
Flags: recursesubdirs ignoreversion

Source: "installers\postgresql.exe"; \
DestDir: "{tmp}"

Source: "installers\setup_postgres.bat"; \
DestDir: "{tmp}"

Source: "installers\init.sql"; \
DestDir: "{tmp}"

[Icons]

Name: "{group}\Vertical"; \
Filename: "{app}\Vertical.exe"

Name: "{commondesktop}\Vertical"; \
Filename: "{app}\Vertical.exe"

[Run]

; ===== УСТАНОВКА POSTGRES =====

Filename: "{tmp}\postgresql.exe"; \
Parameters: "--mode unattended --unattendedmodeui minimal --superpassword 12345678"; \
StatusMsg: "Установка PostgreSQL..."; \
Flags: waituntilterminated; \
Check: not IsPostgresInstalled

; ===== НАСТРОЙКА БД =====

Filename: "{tmp}\setup_postgres.bat"; \
StatusMsg: "Настройка базы данных..."; \
Flags: runhidden waituntilterminated

; ===== ЗАПУСК ПРИЛОЖЕНИЯ =====

Filename: "{app}\Vertical.exe"; \
Description: "Запустить Vertical"; \
Flags: nowait postinstall skipifsilent

[Code]

function IsPostgresInstalled(): Boolean;
begin
  Result :=
    RegKeyExists(HKLM, 'SOFTWARE\PostgreSQL\Installations');
end;